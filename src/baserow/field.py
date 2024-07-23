"""
The module contains definitions for the values of table fields that do not
directly translate into built-in types.
"""

from __future__ import annotations
import abc
import datetime
import enum
from io import BufferedReader
from pathlib import Path
from typing import TYPE_CHECKING, Generic, Optional, TypeVar, Union

from pydantic import BaseModel, ConfigDict, Field, RootModel, model_serializer, model_validator

from baserow.client import GlobalClient
from baserow.color import ColorSequence
from baserow.error import PydanticGenericMetadataError
from baserow.field_config import CreatedByFieldConfig, CreatedOnFieldConfig, FieldConfigType, FileFieldConfig, LastModifiedByFieldConfig, LastModifiedFieldConfig, MultipleCollaboratorsFieldConfig, MultipleSelectFieldConfig, SelectEntryConfig, SingleSelectFieldConfig
from baserow.file import File

if TYPE_CHECKING:
    from baserow.client import Client


class FieldType(str, enum.Enum):
    """The various types that Baserow fields can have."""
    TEXT = "text"
    NUMBER = "number"
    LONG_TEXT = "long_text"
    LINK_ROW = "link_row"
    BOOLEAN = "boolean"
    DATE = "date"
    RATING = "rating"
    LAST_MODIFIED = "last_modified"
    LAST_MODIFIED_BY = "last_modified_by"
    CREATED_ON = "created_on"
    CREATED_BY = "created_by"
    DURATION = "duration"
    URL = "url"
    EMAIL = "email"
    FILE = "file"
    SINGLE_SELECT = "single_select"
    MULTIPLE_SELECT = "multiple_select"
    PHONE_NUMBER = "phone_number"
    FORMULA = "formula"
    ROLLUP = "rollup"
    LOOKUP = "lookup"
    MULTIPLE_COLLABORATORS = "multiple_collaborators"
    UUID = "uuid"
    AUTONUMBER = "autonumber"
    PASSWORD = "password"


class BaserowField(BaseModel, abc.ABC):
    """
    Abstract base class for all Baserow fields that are not covered by the
    built-in types.

    This class also handles tracking changes, which are initially local and only
    applied to Baserow when Table.update() is called. For example, the method
    TableLinkField.append() adds a new link to a record, but this change is only
    written to Baserow when Table.update() is invoked. Such actions can be
    registered with BaserowField.register_pending_change(). If an object with
    pending changes is deleted (__del__), a corresponding warning is issued.
    """

    @classmethod
    @abc.abstractmethod
    def default_config(cls) -> FieldConfigType:
        """Returns the default field config for a given field type."""

    @classmethod
    @abc.abstractmethod
    def read_only(cls) -> bool:
        """
        Read only fields (like modification date or UUID fields) will be ignored
        during update calls like `Table.update()`.
        """

    _pending_changes: list[str] = []
    """See documentation of `BaserowField.register_pending_changes()`."""

    def register_pending_change(self, description: str):
        """
        Registers a change to the field, which is currently only stored locally
        and must be explicitly applied to Baserow using `Table.update()`.

        Args:
            description (str): A description of the change in data.
        """
        self._pending_changes.append(description)

    def changes_applied(self):
        """
        Is called by `Table.update()` after all pending changes have been
        written to Baserow.
        """
        self._pending_changes = []

    def __del__(self):
        if len(self._pending_changes) != 0:
            changes = ["- " + change for change in self._pending_changes]
            print(f"WARNING: THERE ARE STILL PENDING CHANGES IN FIELD {self.__class__.__name__}")  # noqa: F821
            print("\n".join(changes))
            print(
                "It looks like `Table.update()` was not called to apply these changes to Baserow.",
            )


class User(BaseModel):
    """
    A table field that contains one Baserow system user.
    """
    user_id: Optional[int] = Field(alias=str("id"))
    name: Optional[str] = Field(alias=str("name"))


class CreatedByField(User, BaserowField):
    """
    Field tracking the user who created an entry.
    """
    @classmethod
    def default_config(cls) -> FieldConfigType:
        return CreatedByFieldConfig()

    @classmethod
    def read_only(cls) -> bool:
        return True


class LastModifiedByField(User, BaserowField):
    """
    Field tracking the user who last modified a record.
    """
    @classmethod
    def default_config(cls) -> FieldConfigType:
        return LastModifiedByFieldConfig()

    @classmethod
    def read_only(cls) -> bool:
        return True


class CreatedOnField(BaserowField, RootModel[datetime.datetime]):
    """
    Field containing the creation timestamp of a row.
    """
    root: datetime.datetime

    @classmethod
    def default_config(cls) -> FieldConfigType:
        return CreatedOnFieldConfig()

    @classmethod
    def read_only(cls) -> bool:
        return True


class LastModifiedOnField(BaserowField, RootModel[datetime.datetime]):
    """
    Field containing the last modification timestamp of a row.
    """
    root: datetime.datetime

    @classmethod
    def default_config(cls) -> FieldConfigType:
        return LastModifiedFieldConfig()

    @classmethod
    def read_only(cls) -> bool:
        return True


class MultipleCollaboratorsField(BaserowField, RootModel[list[User]]):
    """
    A table field that contains one or multiple Baserow system user(s).
    """
    root: list[User]

    @classmethod
    def default_config(cls) -> FieldConfigType:
        return MultipleCollaboratorsFieldConfig()

    @classmethod
    def read_only(cls) -> bool:
        return False


class FileField(BaserowField, RootModel[list[File]]):
    """
    A file field allows you to easily upload one or more files from your device
    or from a URL.
    """
    root: list[File]

    @classmethod
    def default_config(cls) -> FieldConfigType:
        return FileFieldConfig()

    @classmethod
    def read_only(cls) -> bool:
        return False

    @classmethod
    async def from_file(
        cls,
        file: BufferedReader | str | Path,
        name: Optional[str] = None,
        client: Optional[Client] = None,
    ):
        """
        This method takes a local file (either as a `BufferedReader` or as a
        path) and uploads it to Baserow's media storage, handling the linkage
        between the field and the stored file. A `FileField` instance containing
        the uploaded file is returned. Calling this method initiates the file
        upload, which may take some time depending on the file size.

        Note that this method does not use the client associated with the table.

        ```python
        # By path.
        await Book(
            cover=await FileField.from_file("path/to/image.png"),
        ).create()

        # With BufferedReader.
        await Book(
            cover=await FileField.from_file(open("path/to/image.png", "rb")),
        ).create()
        ```

        Args:
            file (BufferedReader | str | Path): File to be uploaded.
            name (str | None): Optional human-readable name of the file, as it
                should be displayed in the Baserow frontend.
            client (Client | None): Specifies which API client should be used.
                If none is provided, the `GlobalClient` will be used. Note that
                this method does not automatically use the client associated
                with the table.
        """
        rsl = cls(root=[])
        await rsl.append_file(file, name, client, register_pending_change=False)
        return rsl

    @classmethod
    async def from_url(
        cls,
        url: str,
        name: Optional[str] = None,
        client: Optional[Client] = None,
    ):
        """
        This method takes the URL of a publicly accessible file on the internet
        and uploads it to Baserow's media storage, managing the linkage between
        the field and the stored file. Calling this method initiates the file
        upload, which may take some time depending on the file size.

        Note that this method does not use the client associated with the table.

        ```python
        await Book(
            cover=await FileField.from_url("https://example.com/image.png"),
        ).create()
        ```

        Args:
            url (str): URL of the file to be uploaded.
            name (str | None): Optional human-readable name of the file, as it
                should be displayed in the Baserow frontend.
            client (Client | None): Specifies which API client should be used.
                If none is provided, the `GlobalClient` will be used. Note that
                this method does not automatically use the client associated
                with the table.
        """
        rsl = cls(root=[])
        await rsl.append_file_from_url(url, name, client, register_pending_change=False)
        return rsl

    async def append_file(
        self,
        file: BufferedReader | str | Path,
        name: Optional[str] = None,
        client: Optional[Client] = None,
        register_pending_change: bool = True,
    ):
        """
        This method takes a local file (either as a `BufferedReader` or as a
        path) and uploads it to Baserow's media storage and adds it to the file
        field.Calling this method initiates the file upload, which may take some
        time depending on the file size.

        Further information about uploading and setting files can be found in
        the documentation of `client.upload_file()`. After this method
        `Table.update()` must be called manually to apply the changes.

        ```python
        book = Book.by_id(ROW_ID)

        # By path.
        await book.cover.append_file("path/to/image.png")

        # With BufferedReader.
        await book.cover.append_file(open("path/to/image.png", "rb"))

        book.update()
        ```

        Args:
            file (BufferedReader | str | Path): File to be uploaded.
            name (str | None): Optional human-readable name of the file, as it
                should be displayed in the Baserow frontend.
            client (Client | None): Specifies which API client should be used.
                If none is provided, the `GlobalClient` will be used. Note that
                this method does not automatically use the client associated
                with the table.
            register_pending_change (bool): Internal option for the
                `FileField.from_file()` and `FileField.from_url()` methods. When
                set to false, tracking of pending changes for this call is
                disabled. This is only useful in situations where
                `Table.update()` will be called anyway, such as when the method
                is invoked within the initialization of a model.
        """
        if not isinstance(file, BufferedReader):
            file = open(file, "rb")
        if client is None:
            client = GlobalClient()
        new_file = await client.upload_file(file)
        if name is not None:
            new_file.original_name = name
        self.root.append(new_file)
        if register_pending_change:
            self.register_pending_change(
                f"file '{new_file.original_name}' added",
            )

    async def append_file_from_url(
        self,
        url: str,
        name: Optional[str] = None,
        client: Optional[Client] = None,
        register_pending_change: bool = True,
    ):
        """
        This method takes the URL of a publicly accessible file on the internet
        and uploads it to Baserow's media storage and adds it to the file
        field.Calling this method initiates the file upload, which may take some
        time depending on the file size.

        Further information about uploading and setting files can be found in
        the documentation of `client.upload_file()`. After this method
        `Table.update()` must be called manually to apply the changes.

        ```python
        book = Book.by_id(ROW_ID)
        await book.cover.append_file_from_url("https://example.com/image.png")
        book.update()
        ```

        Args:
            url (str): The URL of the file.
            name (str | None): Optional human-readable name of the file, as it
                should be displayed in the Baserow frontend.
            client (Client | None): Specifies which API client should be used.
                If none is provided, the `GlobalClient` will be used. Note that
                this method does not automatically use the client associated
                with the table.
            register_pending_change (bool): Internal option for the
                `FileField.from_file()` and `FileField.from_url()` methods. When
                set to false, tracking of pending changes for this call is
                disabled. This is only useful in situations where
                `Table.update()` will be called anyway, such as when the method
                is invoked within the initialization of a model.
        """
        if client is None:
            client = GlobalClient()
        new_file = await client.upload_file_via_url(url)
        if name is not None:
            new_file.original_name = name
        self.root.append(new_file)
        if register_pending_change:
            self.register_pending_change(f"file from url '{url}' added")

    def clear(self):
        """
        Removes all files from field. After that, `Table.update()` must be called
        to apply the changes.

        ```python
        book = Book.by_id(ROW_ID)
        await book.cover.clear()
        book.update()
        ```
        """
        self.root.clear()
        self.register_pending_change("remove all files in field")


SelectEnum = TypeVar("SelectEnum", bound=enum.Enum)
"""
Instances of a SelectEntry have to be bound to a enum which contain the possible
values of the select entry.
"""


class SelectEntry(BaseModel, Generic[SelectEnum]):
    """A entry in a single or multiple select field."""
    entry_id: Optional[int] = Field(default=None, alias="id")
    value: Optional[SelectEnum] = None
    color: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def id_or_value_must_be_set(self: "SelectEntry") -> "SelectEntry":
        if self.entry_id is None and self.value is None:
            raise ValueError(
                "At least one of the entry_id and value fields must be set"
            )
        return self

    @model_serializer
    def serialize(self) -> Union[int, str]:
        """
        Serializes the field into the data structure required by the Baserow
        API. If an entry has both an id and a value set, the id is used.
        Otherwise the set field is used.

        From the Baserow API documentation: Accepts an integer or a text value
        representing the chosen select option id or option value. A null value
        means none is selected. In case of a text value, the first matching
        option is selected. 
        """
        if self.entry_id is not None:
            return self.entry_id
        if self.value is not None:
            return self.value.value
        raise ValueError("both fields id and value are unset for this entry")

    @classmethod
    def _get_all_possible_values(cls) -> list[str]:
        metadata = cls.__pydantic_generic_metadata__
        if "args" not in metadata:
            raise PydanticGenericMetadataError.args_missing(
                cls.__class__.__name__,
                "select entry enum",
            )
        if len(metadata["args"]) < 1:
            raise PydanticGenericMetadataError.args_empty(
                cls.__class__.__name__,
                "select entry enum",
            )
        select_enum = metadata["args"][0]
        return [item.value for item in select_enum]

    @classmethod
    def _options_config(cls) -> list[SelectEntryConfig]:
        rsl: list[SelectEntryConfig] = []
        color_sequence = ColorSequence()
        i = 0
        for value in cls._get_all_possible_values():
            rsl.append(SelectEntryConfig(
                id=i,
                value=value,
                color=color_sequence.get_color(),
            ))
            i += 1
        return rsl


class SingleSelectField(SelectEntry[SelectEnum], BaserowField):
    """Single select field in a table."""
    @classmethod
    def default_config(cls) -> FieldConfigType:
        options = super(SingleSelectField, cls)._options_config()
        return SingleSelectFieldConfig(select_options=options)

    @classmethod
    def read_only(cls) -> bool:
        return False

    @classmethod
    def from_enum(cls, select_enum: SelectEnum):
        """
        This function can be used to directly obtain the correct instance of the
        field abstraction from an enum. Primarily, this function is a quality of
        life feature for directly setting a field value in a model
        initialization. This replaces the somewhat unergonomic and unintuitive
        syntax which would be used otherwise.

        ```python
        class Genre(str, enum.Enum):
            FICTION = "Fiction"
            EDUCATION = "Education"

        class Book(Table):
            [...]
            genre: Optional[SingleSelectField[Genre]] = Field(default=None)

        # Can use this...
        await Book(
            genre=SingleSelectField.from_enum(Genre.FICTION),
        ).create()

        # ...instead of
        await Book(
            genre=SingleSelectField[Genre](value=Genre.FICTION)
        ).create()
        ```

        Args:
            select_enum (SelectEnum): Enum to which the field should be set.add 
        """
        return SingleSelectField[type(select_enum)](value=select_enum)

    def set(self, instance: SelectEnum):
        """
        Set the value of the field. Please note that this method does not update
        the record on Baserow. You have to call `Table.update()` afterwards.

        Args:
            instance (SelectEnum): The enum which should be set in this field.
        """
        self.entry_id = None
        self.value = instance
        self.color = None
        self.register_pending_change(f"set SingleSelect to '{instance.value}'")


class MultipleSelectField(BaserowField, RootModel[list[SelectEntry]], Generic[SelectEnum]):
    """Multiple select field in a table."""
    root: list[SelectEntry[SelectEnum]]

    @classmethod
    def read_only(cls) -> bool:
        return False

    @classmethod
    def from_enums(cls, *select_enums: SelectEnum):
        """
        This function can be used to directly obtain the correct instance of the
        field abstraction from one or multiple enum(s). Primarily, this function
        is a quality of life feature for directly setting a field value in a
        model initialization. This replaces the somewhat unergonomic and
        unintuitive syntax which would be used otherwise.

        ```python
        class Keyword(str, enum.Enum):
            ADVENTURE = "Adventure"
            FICTION = "Fiction"
            TECH = "Text"

        class Book(Table):
            [...]
            keywords: Optional[MultipleSelectField[Keyword]] = Field(default=None)

        await Book(
            keywords=MultipleSelectField.from_enums(Keyword.ADVENTURE, Keyword.FICTION)
        ).create()
        ```

        Args:
            *select_enum (SelectEnum | list[SelectEnum]): Enum(s) value(s) to be part
                of the select field.
        """
        if not select_enums:
            raise ValueError("At least one enum must be provided")
        select_enum_type = type(select_enums[0])
        enums: list[SelectEntry[SelectEnum]] = []
        for enum in select_enums:
            enums.append(SelectEntry[type(enum)](value=enum))
        return MultipleSelectField[select_enum_type](root=enums)

    def append(self, *select_enums: SelectEnum):
        """
        Append one or multiple enum(s) to the field. Please note that this
        method does not update the record on Baserow. You have to call
        `Table.update()` afterwards.

        Args:
            *select_enum (SelectEnum | list[SelectEnum]): Enum(s) value(s) to be
                added the the select field.
        """
        names: list[str] = []
        for enum in select_enums:
            self.root.append(SelectEntry(value=enum))
            names.append(enum.name)
        self.register_pending_change(
            f"append enum(s) {', '.join(names)} to multiple select field",
        )

    def clear(self):
        """
        Remove all enums currently set for this field. Please note that this
        method does not update the record on Baserow. You have to call
        `Table.update()` afterwards.
        """
        self.root.clear()
        self.register_pending_change(
            f"removed all enum(s) from multiple select field",
        )

    def remove(self, *select_enums: SelectEnum):
        """
        Remove one or multiple enum(s) from the field. Please note that this
        method does not update the record on Baserow. You have to call
        `Table.update()` afterwards.

        Args:
            *select_enum (SelectEnum | list[SelectEnum]): Enum(s) value(s) to be
                removed the the select field.
        """
        to_be_removed = [
            entry for entry in self.root if entry. value in select_enums]
        self.root = [
            entry for entry in self.root if entry not in to_be_removed
        ]
        names = [
            entry.value.name for entry in to_be_removed if entry.value is not None]
        self.register_pending_change(
            f"removed enum(s) {', '.join(names)} from multiple select field",
        )

    @classmethod
    def default_config(cls) -> FieldConfigType:
        metadata = cls.__pydantic_generic_metadata__
        if "args" not in metadata:
            raise PydanticGenericMetadataError.args_missing(
                cls.__class__.__name__,
                "select entry enum",
            )
        if len(metadata["args"]) < 1:
            raise PydanticGenericMetadataError.args_empty(
                cls.__class__.__name__,
                "select entry enum",
            )
        select_enum = metadata["args"][0]
        rsl: list[SelectEntryConfig] = []
        color_sequence = ColorSequence()
        i = 0
        for item in select_enum:
            rsl.append(SelectEntryConfig(
                id=i,
                value=item.value,
                color=color_sequence.get_color(),
            ))
            i += 1
        return MultipleSelectFieldConfig(select_options=rsl)
