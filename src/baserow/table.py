"""
The module provides the ORM-like functionality of Baserowdantic.
"""


import abc
from functools import wraps
from typing import Any, ClassVar, Generic, Optional, Tuple, Type, TypeVar, Union, get_args, get_origin
import uuid

from pydantic import BaseModel, ConfigDict, Field, RootModel, model_serializer, model_validator
from pydantic.fields import FieldInfo

from baserow.client import Client, GlobalClient, MinimalRow
from baserow.error import InvalidFieldForCreateTableError, InvalidTableConfigurationError, MultiplePrimaryFieldsError, NoClientAvailableError, NoPrimaryFieldError, PydanticGenericMetadataError, RowIDNotSetError
from baserow.field import BaserowField
from baserow.field_config import DEFAULT_CONFIG_FOR_BUILT_IN_TYPES, Config, FieldConfigType, LinkFieldConfig, PrimaryField
from baserow.filter import Filter


def valid_configuration(func):
    """
    This decorator checks whether the model configuration has been done
    correctly. In addition to validating the class vars Table.table_id and
    Table.table_name, it also verifies whether the model config is set with
    populate_by_name=True.
    """

    @wraps(func)
    def wrapper(cls, *args, **kwargs):
        if not isinstance(cls.table_id, int):
            raise InvalidTableConfigurationError(
                cls.__name__, "table_id not set")
        if not isinstance(cls.table_name, str):
            raise InvalidTableConfigurationError(
                cls.__name__, "table_name not set")
        if "populate_by_name" not in cls.model_config:
            raise InvalidTableConfigurationError(
                cls.__name__,
                "populate_by_name is not set in the model config; it should most likely be set to true"
            )
        return func(cls, *args, **kwargs)
    return wrapper


T = TypeVar("T", bound="Table")


class RowLink(BaseModel, Generic[T]):
    """
    A single linking of one row to another row in another table. A link field
    can have multiple links. Part of `table.TableLinkField`.
    """
    row_id: Optional[int] = Field(alias=str("id"))
    key: Optional[str] = Field(alias=str("value"))

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def id_or_value_must_be_set(self: "RowLink") -> "RowLink":
        if self.row_id is None and self.key is None:
            raise ValueError(
                "At least one of the row_id and value fields must be set"
            )
        return self

    @model_serializer
    def serialize(self) -> Union[int, str]:
        """
        Serializes the field into the data structure required by the Baserow
        API. If an entry has both an id and a value set, the id is used.
        Otherwise the key field is used.

        From the Baserow API documentation: Accepts an array containing the
        identifiers or main field text values of the related rows.
        """
        if self.row_id is not None:
            return self.row_id
        if self.key is not None:
            return self.key
        raise ValueError("both fields id and key are unset for this entry")

    async def query_linked_row(self) -> T:
        """
        Queries and returns the linked row.
        """
        if self.row_id is None:
            raise ValueError(
                "query_linked_row is currently only implemented using the row_id",
            )
        table = self.__get_linked_table()
        return await table.by_id(self.row_id)

    def __get_linked_table(self) -> T:
        metadata = self.__pydantic_generic_metadata__
        if "args" not in metadata:
            raise PydanticGenericMetadataError.args_missing(
                self.__class__.__name__,
                "linked table",
            )
        if len(metadata["args"]) < 1:
            raise PydanticGenericMetadataError.args_empty(
                self.__class__.__name__,
                "linked table",
            )
        return metadata["args"][0]


class TableLinkField(BaserowField, RootModel[list[RowLink]], Generic[T]):
    """
    A link to table field creates a link between two existing tables by
    connecting data across tables with linked rows.
    """
    root: list[RowLink[T]]
    _cache: Optional[list[T]] = None

    @classmethod
    def default_config(cls) -> FieldConfigType:
        metadata = cls.__pydantic_generic_metadata__
        if "args" not in metadata:
            raise PydanticGenericMetadataError.args_missing(
                cls.__class__.__name__,
                "linked table",
            )
        if len(metadata["args"]) < 1:
            raise PydanticGenericMetadataError.args_empty(
                cls.__class__.__name__,
                "linked table",
            )
        linked_table = metadata["args"][0]
        return LinkFieldConfig(link_row_table_id=linked_table.table_id)

    @classmethod
    def read_only(cls) -> bool:
        return False

    @classmethod
    def from_value(cls, *instances: Union[int, T]):
        """
        Instantiates a link field from a referencing value. Can be used to set a
        link directly when instantiating a table model using a parameter. This
        is a quality of life feature and replace the tedious way of manually
        defining a link. For more information please refer to the example below.

        ```python
        class Author(Table):
            [...] name: str

        class Book(Table):
            [...] title: str author: Optional[TableLinkField[Author]] =
            Field(default=None)

        # Instead of...
        new_book = await Book(
            title="The Great Adventure", author=TableLinkField[Author](
                root=[RowLink[Author](row_id=23, key=None)]
            )
        ).create()

        # ...this method allows this (link to author row with id=23) new_book =
        await Book(
            title="The Great Adventure",
            author=TableLinkField[Author].from_value(23),
        ).create() ```

        Args:
            *instance (int | T): Instance(s) or row id(s) to be
                linked.
        """
        rsl = cls(root=[])
        for item in instances:
            if isinstance(item, int):
                rsl.root.append(RowLink[T](row_id=item, key=None))
            elif item.row_id is None:
                raise RowIDNotSetError(
                    cls.__name__,
                    "TableLinkField.link()",
                )
            else:
                rsl.root.append(RowLink[T](row_id=item.row_id, key=None))
        return rsl

    def id_str(self) -> str:
        """Returns a list of all ID's as string for debugging."""
        return ",".join([str(link.row_id) for link in self.root])

    def append(self, *instances: Union[int, T]):
        """
        Add a link to the given table row(s). Please note that this method does
        not update the record on Baserow. You have to call `Table.update()`
        to apply the changes.

        ```python
        author = await Author.by_id(AUTHOR_ID)
        book = await Book.by_id(BOOK_ROW_ID)
        await book.author.append(ANOTHER_AUTHOR_ID, author)
        await book.update()
        ```

        Args:
            instance (int | T | list[int | T]): Instance(s) or row id(s) to be
                added. When using a `Table` instance make sure that
                `Table.row_id` is set.
        """
        for item in instances:
            if isinstance(item, int):
                row_id = item
            elif item.row_id is None:
                raise RowIDNotSetError(
                    self.__class__.__name__,
                    "TableLinkField.link()",
                )
            else:
                row_id = item.row_id
            self.root.append(RowLink(
                row_id=row_id,
                key=None,
            ))
            self.register_pending_change(f"link to entry {row_id} added")

    def clear(self):
        """
        Deletes all linked entries. After that, `Table.update()` must be called
        to apply the changes.

        ```python
        book = await Book.by_id(BOOK_ROW_ID)
        book.author.clear()
        await book.update()
        print("Removed all authors from the book")
        ```
        """
        self.root.clear()
        self.register_pending_change("all links removed")

    async def query_linked_rows(self) -> list[T]:
        """
        Queries and returns all linked rows.

        ```python
        book = await Book.by_id(BOOK_ROW_ID)
        authors = await book.author.query_linked_rows()
        print(f"Author(s) of book {book.title}: {authors}")
        ```
        """
        rsl: list[T] = []
        for link in self.root:
            rsl.append(await link.query_linked_row())
        self._cache = rsl
        return rsl

    async def cached_query_linked_rows(self) -> list[T]:
        """
        Same as `TableLinkField.query_linked_rows()` with cached results. The
        Baserow API is called only the first time. After that, the cached result
        is returned directly. This will also use the last result of
        `TableLinkField.query_linked_rows()`.
        """
        if self._cache is None:
            self._cache = await self.query_linked_rows()
        return self._cache


class Table(BaseModel, abc.ABC):
    """
    The model derived from pydantic's BaseModel provides ORM-like access to the
    CRUD (create, read, update, delete) functionalities of a table in Baserow.
    The design of the class is quite opinionated. Therefore, if a certain use
    case cannot be well covered with this abstraction, it may be more effective
    to directly use the `Client` class.

    Every inheritance/implementation of this class provides access to a table in
    a Baserow instance. A client instance can be specified; if not, the
    `GlobalClient` is used. Ensure that it is configured before use.
    """

    row_id: Optional[int] = Field(default=None, alias=str("id"))
    """
    All rows in Baserow have a unique ID.
    """

    @property
    @abc.abstractmethod
    def table_id(cls) -> int:  # type: ignore
        """
        The Baserow table ID. Every table in Baserow has a unique ID. This means
        that each model is linked to a specific table. It's not currently
        possible to bind a table model to multiple tables.
        """
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def table_name(cls) -> str:  # type: ignore
        """
        Each table model must have a human-readable table name. The name is used
        for debugging information only and has no role in addressing/interacting
        with the Baserow table. Ideally this should be the same name used for
        the table within the Baserow UI.
        """
        raise NotImplementedError()

    table_id: ClassVar[int]
    table_name: ClassVar[str]

    client: ClassVar[Optional[Client]] = None
    """
    Optional client instance for accessing Baserow. If not set, the
    GlobalClient is used.
    """
    dump_response: ClassVar[bool] = False
    """
    If set to true, the parsed dict of the body of each API response is dumped
    to debug output.
    """
    dump_payload: ClassVar[bool] = False
    """
    If set to true, the data body for the request is dumped to the debug output.
    """
    ignore_fields_during_table_creation: ClassVar[list[str]] = ["order", "id"]
    """Fields with this name are ignored when creating tables."""
    model_config = ConfigDict(ser_json_timedelta="float")

    @classmethod
    def __req_client(cls) -> Client:
        """
        Returns the client for API requests to Baserow. If no specific client is
        set for the model (Table.client is None), the packet-wide GlobalClient
        is used.
        """
        if cls.client is None and not GlobalClient.is_configured:
            raise NoClientAvailableError(cls.table_name)
        if cls.client is None:
            return GlobalClient()
        return cls.client

    @classmethod
    @valid_configuration
    async def by_id(cls: Type[T], row_id: int) -> T:
        """
        Fetch a single row/entry from the table by the row ID.

        Args:
            row_id (int): The ID of the row to be returned.
        """
        return await cls.__req_client().get_row(cls.table_id, row_id, True, cls)

    @classmethod
    @valid_configuration
    async def query(
        cls: Type[T],
        filter: Optional[Filter] = None,
        order_by: Optional[list[str]] = None,
        page: Optional[int] = None,
        size: Optional[int] = None,
    ) -> list[T]:
        """
        Queries for rows in the Baserow table. Note that Baserow uses paging. If
        all rows of a table (in line with the optional filter) are needed, set
        `size` to `-1`. Even though this option allows for resolving paging, it
        should be noted that in Baserow, a maximum of 200 rows can be received
        per API call. This can lead to significant waiting times and system load
        for large datasets. Therefore, this option should be used with caution.

        Args:
            filter (Optional[list[Filter]], optional): Allows the dataset to be
                filtered.
            order_by (Optional[list[str]], optional): A list of field names/IDs
                by which the result should be sorted. If the field name is
                prepended with a +, the sorting is ascending; if with a -, it is
                descending.
            page (Optional[int], optional): The page of the paging.
            size (Optional[int], optional): How many records should be returned
                at max. Defaults to 100 and cannot exceed 200. If set to -1 the
                method wil resolve Baserow's paging and returns all rows
                corresponding to the query.
        """
        if size == -1 and page:
            raise ValueError(
                "it's not possible to request a specific page when requesting all results (potentially from multiple pages) with size=-1",
            )
        if size is not None and size == -1:
            rsl = await cls.__req_client().list_all_table_rows(
                cls.table_id,
                True,
                cls,
                filter=filter,
                order_by=order_by,
            )
        else:
            rsl = await cls.__req_client().list_table_rows(
                cls.table_id,
                True,
                cls,
                filter=filter,
                order_by=order_by,
                page=page,
                size=size,
            )
        return rsl.results

    @classmethod
    @valid_configuration
    async def update_fields_by_id(
        cls: Type[T],
        row_id: int,
        by_alias: bool = True,
        **kwargs: Any,
    ) -> Union[T, MinimalRow]:
        """
        Update the fields in a row (defined by its ID) given by the kwargs
        parameter. The keys provided must be valid field names in the model.
        values will be validated against the model. If the value type is
        inherited by the BaseModel, its serializer will be applied to the value
        and submitted to the database. Please note that custom _Field_
        serializers for any other types are not taken into account.

        The custom model serializer is used in the module because the structure
        of some Baserow fields differs between the GET result and the required
        POST data for modification. For example, the MultipleSelectField returns
        ID, text value, and color with the GET request. However, only a list of
        IDs or values is required for updating the field using a POST request.

        Args:
            row_id (int): ID of row in Baserow to be updated.
            by_alias (bool, optional): Specify whether to use alias values to
                address field names in Baserow. Note that this value is set to
                True by default, contrary to pydantic's usual practice. In the
                context of the table model (which is specifically used to
                represent Baserow tables), setting an alias typically indicates
                that the field name in Baserow is not a valid Python variable
                name.
        """
        payload = cls.__model_dump_subset(by_alias, **kwargs)
        # if cls.dump_payload:
        #     logger.debug(payload)
        return await cls.__req_client().update_row(
            cls.table_id,
            row_id,
            payload,
            True,
        )

    @classmethod
    @valid_configuration
    async def delete_by_id(cls: Type[T], row_id: Union[int, list[int]]):
        """
        Deletes one or more rows in the Baserow table. If a list of IDs is
        passed, deletion occurs as a batch command. To delete a single Table
        instance with the Table.row_id set, the Table.delete() method can also
        be used.

        Args:
            row_id (Union[int, list[int]]): ID or ID list of row(s) in Baserow
            to be deleted.
        """
        await cls.__req_client().delete_row(cls.table_id, row_id)

    @classmethod
    @valid_configuration
    def batch_update(cls, data: dict[int, dict[str, Any]], by_alias: bool = True):
        """
        Updates multiple fields in the database. The given data dict must map
        the unique row id to the data to be updated. The input is validated
        against the model. See the update method documentation for more
        information about its limitations and underlying ideas.

        Args:
            data: A dict mapping the unique row id to the data to be updated.
            by_alias: Please refer to the documentation on the update method to
                learn more about this arg.
        """
        payload = []
        for key, value in data.items():
            entry = cls.__model_dump_subset(by_alias, **value)
            entry["id"] = key
            payload.append(entry)
        # if cls.dump_payload:
        #     logger.debug(payload)
        raise NotImplementedError(
            "Baserow client library currently does not support batch update operations on rows"
        )

    @valid_configuration
    async def create(self) -> MinimalRow:
        """
        Creates a new row in the table with the data from the instance. Please
        note that this method does not check whether the fields defined by the
        model actually exist.
        """
        rsl = await self.__req_client().create_row(
            self.table_id,
            self.model_dump(by_alias=True, mode="json", exclude_none=True),
            True,
        )
        if not isinstance(rsl, MinimalRow):
            raise RuntimeError(
                f" expected MinimalRow instance got {type(rsl)} instead",
            )
        return rsl

    @valid_configuration
    async def update_fields(
        self: T,
        by_alias: bool = True,
        **kwargs: Any,
    ) -> Union[T, MinimalRow]:
        """
        Updates the row with the ID of this instance. Short-hand for the
        `Table.update_by_id()` method, for instances with the `Table.row_id`
        set. For more information on how to use this, please refer to the
        documentation of this method.
        """
        if self.row_id is None:
            raise RowIDNotSetError(self.__class__.__name__, "field_update")
        return await self.update_fields_by_id(self.row_id, by_alias, **kwargs)

    @valid_configuration
    async def update(self: T) -> Union[T, MinimalRow]:
        """
        Updates all fields of a row with the data of this model instance. The
        row_id field must be set.
        """
        if self.row_id is None:
            raise RowIDNotSetError(self.__class__.__name__, "update")

        excluded: list[str] = []
        for key, field in self.__dict__.items():
            if isinstance(field, BaserowField) and field.read_only():
                excluded.append(key)
            elif isinstance(field, uuid.UUID):
                excluded.append(key)

        rsl = await self.__req_client().update_row(
            self.table_id,
            self.row_id,
            self.model_dump(
                by_alias=True,
                mode="json",
                exclude_none=True,
                exclude=set(excluded),
            ),
            True
        )
        for _, field in self.__dict__.items():
            if isinstance(field, BaserowField):
                field.changes_applied()
        return rsl

    @valid_configuration
    async def delete(self):
        """
        Deletes the row with the ID of this instance. Short-hand for the
        `Table.delete_by_id()` method, for instances with the `Table.row_id`
        set. For more information on how to use this, please refer to the
        documentation of this method.
        """
        if self.row_id is None:
            raise RowIDNotSetError(self.__class__.__name__, "delete")
        await self.delete_by_id(self.row_id)

    @classmethod
    async def create_table(cls, database_id: int):
        """
        This method creates a new table in the given database based on the
        structure and fields of the model.

        Args:
            database_id (int): The ID of the database in which the new table
                should be created.
        """
        # Name is needed for table creation.
        if not isinstance(cls.table_name, str):
            raise InvalidTableConfigurationError(
                cls.__name__, "table_name not set")

        # The primary field is determined at this point to ensure that any
        # exceptions (none, more than one primary field) occur before the
        # expensive API calls.
        primary_name, _ = cls.primary_field()

        # Create the new table itself.
        table_rsl = await cls.__req_client().create_database_table(database_id, cls.table_name)
        cls.table_id = table_rsl.id
        primary_id, unused_fields = await cls.__scramble_all_field_names()

        # Create the fields.
        for key, field in cls.model_fields.items():
            await cls.__create_table_field(key, field, primary_id, primary_name)

        # Delete unused fields.
        for field in unused_fields:
            await cls.__req_client().delete_database_table_field(field)

    @classmethod
    def primary_field(cls) -> Tuple[str, FieldInfo]:
        """
        This method returns a tuple of the field name and pydantic.FieldInfo of
        the field that has been marked as the primary field. Only one primary
        field is allowed per table. This is done by adding PrimaryField as a
        type annotation. Example for such a Model:

        ```python
        class Person(Table):
            table_id = 23
            table_name = "Person"
            model_config = ConfigDict(populate_by_name=True)

            name: Annotated[
                str,
                Field(alias=str("Name")),
                PrimaryField(),
            ]
        ```
        """
        rsl: Optional[Tuple[str, FieldInfo]] = None
        for name, field in cls.model_fields.items():
            if any(isinstance(item, PrimaryField) for item in field.metadata):
                if rsl is not None:
                    raise MultiplePrimaryFieldsError(cls.__name__)
                rsl = (name, field)
        if rsl is None:
            raise NoPrimaryFieldError(cls.__name__)
        return rsl

    @classmethod
    async def __create_table_field(cls, name: str, field: FieldInfo, primary_id: int, primary_name: str):
        if name in cls.ignore_fields_during_table_creation or field.alias in cls.ignore_fields_during_table_creation:
            return

        config: Optional[FieldConfigType] = None
        for item in field.metadata:
            if isinstance(item, Config):
                config = item.config
        field_type = cls.__type_for_field(name, field)
        if config is None and field_type in DEFAULT_CONFIG_FOR_BUILT_IN_TYPES:
            config = DEFAULT_CONFIG_FOR_BUILT_IN_TYPES[field_type]
        elif config is None and issubclass(field_type, BaserowField):
            config = field_type.default_config()
        elif config is None:
            raise InvalidFieldForCreateTableError(
                name,
                f"{field_type} is not supported"
            )
        if field.alias is not None:
            config.name = field.alias
        else:
            config.name = name

        config.description = field.description

        if name == primary_name:
            await cls.__req_client().update_database_table_field(primary_id, config)
        else:
            await cls.__req_client().create_database_table_field(cls.table_id, config)

    @staticmethod
    def __type_for_field(name: str, field: FieldInfo) -> Type[Any]:
        if get_origin(field.annotation) is Union:
            args = get_args(field.annotation)
            not_none_args = [arg for arg in args if arg is not type(None)]
            if len(not_none_args) == 1:
                return not_none_args[0]
            else:
                raise InvalidFieldForCreateTableError(
                    name,
                    "Union type is not supported",
                )
        elif field.annotation is not None:
            return field.annotation
        else:
            raise InvalidFieldForCreateTableError(
                name,
                "None type is not supported",
            )

    @classmethod
    async def __scramble_all_field_names(cls) -> Tuple[int, list[int]]:
        """
        Changes the names of all existing fields in a Baserow table to random
        UUIDs and returns the ID of the primary file and a list of the other
        modified fields. This is used to ensure that the automatically created
        fields in a new table do not collide with the names of subsequently
        created fields.
        """
        fields = await cls.__req_client().list_fields(cls.table_id)
        primary: int = -1
        to_delete: list[int] = []
        for field in fields.root:
            if field.root.id is None:
                raise ValueError("field id is None")
            if field.root.primary:
                primary = field.root.id
            else:
                to_delete.append(field.root.id)
            await cls.__req_client().update_database_table_field(
                field.root.id,
                {"name": str(uuid.uuid4())},
            )
        return (primary, to_delete)

    @classmethod
    def __validate_single_field(
        cls,
        field_name: str,
        value: Any,
    ) -> Union[
        dict[str, Any],
        tuple[dict[str, Any], dict[str, Any], set[str]],
        Any,
    ]:
        return cls.__pydantic_validator__.validate_assignment(
            cls.model_construct(), field_name, value
        )

    @classmethod
    def __model_dump_subset(cls, by_alias: bool, **kwargs: Any) -> dict[str, Any]:
        """
        This method takes a dictionary of keyword arguments (kwargs) and
        validates it against the model before serializing it as a dictionary. It
        is used for the update and batch_update methods. If a field value is
        inherited from a BaseModel, it will be serialized using model_dump.

        Please refer to the documentation on the update method to learn more
        about its limitations and underlying ideas.
        """
        rsl = {}
        for key, value in kwargs.items():
            # Check, whether the submitted key-value pairs are in the model and
            # the value passes the validation specified by the field.
            cls.__validate_single_field(key, value)

            # If a field has an alias, replace the key with the alias.
            rsl_key = key
            alias = cls.model_fields[key].alias
            if by_alias and alias:
                rsl_key = alias

            # When the field value is a pydantic model, serialize it.
            rsl[rsl_key] = value
            if isinstance(value, BaseModel):
                rsl[rsl_key] = value.model_dump(by_alias=by_alias)
        return rsl
