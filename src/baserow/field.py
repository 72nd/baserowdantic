"""
The module contains definitions for the values of table fields that do not
directly translate into built-in types.
"""

from __future__ import annotations
import abc
import enum
from io import BufferedReader
from typing import TYPE_CHECKING, Generic, Optional, TypeVar, Union

from pydantic import BaseModel, ConfigDict, Field, RootModel, model_serializer, model_validator

from baserow.client import GlobalClient
from baserow.error import PydanticGenericMetadataError
from baserow.field_config import CreatedByFieldConfig, FieldConfigType, FileFieldConfig, LastModifiedByFieldConfig, MultipleCollaboratorsFieldConfig, MultipleSelectFieldConfig, SelectEntryConfig, SingleSelectFieldConfig
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

    _pending_changes: list[str] = []

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


class LastModifiedByField(User, BaserowField):
    @classmethod
    def default_config(cls) -> FieldConfigType:
        return LastModifiedByFieldConfig()


class CreatedByField(User, BaserowField):
    @classmethod
    def default_config(cls) -> FieldConfigType:
        return CreatedByFieldConfig()


class MultipleCollaboratorsField(BaserowField, RootModel[list[User]]):
    """
    A table field that contains one or multiple Baserow system user(s).
    """
    root: list[User]

    @classmethod
    def default_config(cls) -> FieldConfigType:
        return MultipleCollaboratorsFieldConfig()


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
    async def from_file(
        cls,
        file: BufferedReader,
        name: Optional[str] = None,
        client: Client | None = None,
    ):
        """
        TODO.
        """
        rsl = cls(root=[])
        await rsl.append_file(file, name, client, register_pending_change=False)
        return rsl

    @classmethod
    async def from_url(
        cls,
        url: str,
        name: Optional[str] = None,
        client: Client | None = None,
    ):
        """
        TODO.
        """
        rsl = cls(root=[])
        await rsl.append_file_from_url(url, name, client, register_pending_change=False)
        return rsl

    async def append_file(
        self,
        file: BufferedReader,
        name: Optional[str] = None,
        client: Client | None = None,
        register_pending_change: bool = True,
    ):
        """
        TODO: HAS TO BE REWRITTEN!
        Client/GlobalClient. Table.update() has to be called.

        Uploads a new file to Baserow and adds it to the local field instance.
        Afterwards, this instance can be used with `Client.update_row()` to update
        the file field in a row. Further information about uploading and setting
        files can be found in the documentation of `client.upload_file()`.

        Args:
            client (Client): Instance of a Baserow client to upload the file.
            file (BufferedReader): A BufferedReader containing the file to be
                uploaded.
            name (str, optional): Optional file name, which will be displayed in
                the Baserow user interface. This name is also used when a file
                is downloaded from Baserow.
        """
        if client is None:
            client = GlobalClient()
        new_file = await client.upload_file(file)
        if name is not None:
            new_file.original_name = name
        self.root.append(new_file)
        if register_pending_change:
            self.register_pending_change(
                f"file '{new_file.original_name}' added")

    async def append_file_from_url(
        self,
        url: str,
        name: Optional[str] = None,
        client: Client | None = None,
        register_pending_change: bool = True,
    ):
        """
        TODO: HAS TO BE REWRITTEN!
        Client/GlobalClient. Table.update() has to be called.

        Uploads a new file from a url to Baserow and adds it to the local field
        instance. Afterwards, this instance can be used with `Client.update_row()`
        to update the file field in a row. Further information about uploading
        and setting files can be found in the documentation of
        `client.upload_file_via_url()`.

        Args:
            client (Client): Instance of a Baserow client to upload the file.
            url (str): The URL of the file.
            name (str, optional): Optional file name, which will be displayed in
                the Baserow user interface. This name is also used when a file
                is downloaded from Baserow.
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
        """
        self = FileField(root=[])
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
        i = 0
        for value in cls._get_all_possible_values():
            rsl.append(SelectEntryConfig(id=i, value=value))
            i += 1
        return rsl


class SingleSelectField(SelectEntry[SelectEnum], BaserowField):
    """Single select field in a table."""
    @classmethod
    def default_config(cls) -> FieldConfigType:
        options = super(SingleSelectField, cls)._options_config()
        return SingleSelectFieldConfig(select_options=options)

    @classmethod
    def from_enum(cls, select_enum: SelectEnum):
        """
        This function can be used to directly obtain the correct instance of the
        field abstraction from an enum. Primarily, this function is a quality of
        life feature for directly setting a field value in a model
        initialization. This replaces the somewhat unergonomic and unintuitive
        syntax which would be used otherwise.

        ```python class Genre(str, enum.Enum):
            FICTION = "Fiction" EDUCATION = "Education"

        class Book(Table):
            [...] genre: Optional[SingleSelectField[Genre]] =
            Field(default=None)

        # Can use this... await Book(
            genre=SingleSelectField.from_enum(Genre.FICTION),
        ).create()

        # ...instead of
        await Book(
            genre=SingleSelectField[Genre](value=Genre.FICTION)
        ).create() ```

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
        i = 0
        for item in select_enum:
            rsl.append(SelectEntryConfig(id=i, value=item.value))
            i += 1
        return MultipleSelectFieldConfig(select_options=rsl)
