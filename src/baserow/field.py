"""
The module contains definitions for the values of table fields that do not
directly translate into built-in types.
"""

from __future__ import annotations
import abc
from datetime import datetime
import enum
from io import BufferedReader
from typing import TYPE_CHECKING, Generic, Optional, TypeVar, Union, get_args, get_origin, get_overloads

from pydantic import BaseModel, ConfigDict, Field, RootModel, model_serializer, model_validator

from baserow.error import PydanticGenericMetadataError
from baserow.field_config import CreatedByFieldConfig, FieldConfigType, FileFieldConfig, LastModifiedByFieldConfig, MultipleCollaboratorsFieldConfig, MultipleSelectFieldConfig, SelectEntryConfig, SingleSelectFieldConfig

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
    """

    @classmethod
    @abc.abstractmethod
    def default_config(cls) -> FieldConfigType:
        """Returns the default field config for a given field type."""


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


class FileThumbnail(BaseModel):
    """
    Data model for thumbnails. These are used in the `field.File` model.
    """
    url: str
    width: Optional[int]
    height: Optional[int]


class File(BaseModel):
    """A single file with its metadata stored in Baserow."""
    url: Optional[str] = None
    mime_type: Optional[str]
    thumbnails: Optional[dict[str, FileThumbnail]] = None
    name: str
    size: Optional[int] = None
    is_image: Optional[bool] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    uploaded_at: Optional[datetime] = None
    original_name: Optional[str] = None

    @classmethod
    async def upload_file(cls, client: Client, file: BufferedReader) -> "File":
        """
        Uploads a file to Baserow and returns the result. For more information
        see the `Client.upload_file` documentation.

        Args:
            client (Client): Instance of a Baserow client to upload the file.
            file (BufferedReader): A BufferedReader containing the file to be
                uploaded.
        """
        return await client.upload_file(file)

    @classmethod
    async def upload_file_via_url(cls, client: Client, url: str) -> "File":
        """
        Loads a file from the given URL into Baserow. For more information see
        the `Client.upload_file_via_url()` documentation.

        Args:
            client (Client): Instance of a Baserow client to upload the file.
            url (str): The URL of the file.
        """
        return await client.upload_file_via_url(url)


class FileField(BaserowField, RootModel[list[File]]):
    """
    A file field allows you to easily upload one or more files from your device
    or from a URL.
    """
    root: list[File]

    @classmethod
    def default_config(cls) -> FieldConfigType:
        return FileFieldConfig()

    async def add_file(
        self,
        client: Client,
        file: BufferedReader,
        name: Optional[str] = None
    ):
        """
        Uploads a new file to Baserow and adds it to the local field instance.
        Afterwards, this instance can be used with `Client.update_row()` to update
        the file field in a row. Further information about uploading and setting
        files can be found in the documentation of `client.upload_file()`.

        **Caution:** While this method is public, it is primarily part of the
        implementation of `Table.upload_file()`. If you are not using the
        ORM-like functionality of `Table`, it is recommended to use the
        `Client.upload_file()` method directly. As mentioned above, after
        executing this method, the file is only uploaded to Baserow's storage
        but not yet linked to the file field. Therefore, the value of the field
        in the desired row must be manually updated with the value of this field
        instance afterwards.

        Args:
            client (Client): Instance of a Baserow client to upload the file.
            file (BufferedReader): A BufferedReader containing the file to be
                uploaded.
            name (str, optional): Optional file name, which will be displayed in
                the Baserow user interface. This name is also used when a file
                is downloaded from Baserow.
        """
        new_file = await File.upload_file(client, file)
        if name is not None:
            new_file.original_name = name
        self.root.append(new_file)

    async def add_file_via_url(
        self,
        client: Client,
        url: str,
        name: Optional[str] = None
    ):
        """
        Uploads a new file from a url to Baserow and adds it to the local field
        instance. Afterwards, this instance can be used with `Client.update_row()`
        to update the file field in a row. Further information about uploading
        and setting files can be found in the documentation of
        `client.upload_file_via_url()`.

        **Caution:** While this method is public, it is primarily part of the
        implementation of `Table.upload_file()`. If you are not using the
        ORM-like functionality of `Table`, it is recommended to use the
        `Client.upload_file()` method directly. As mentioned above, after
        executing this method, the file is only uploaded to Baserow's storage
        but not yet linked to the file field. Therefore, the value of the field
        in the desired row must be manually updated with the value of this field
        instance afterwards.

        Args:
            client (Client): Instance of a Baserow client to upload the file.
            url (str): The URL of the file.
            name (str, optional): Optional file name, which will be displayed in
                the Baserow user interface. This name is also used when a file
                is downloaded from Baserow.
        """
        new_file = await File.upload_file_via_url(client, url)
        if name is not None:
            new_file.original_name = name
        self.root.append(new_file)


SelectEnum = TypeVar("SelectEnum", bound=enum.Enum)
"""
Instances of a SelectEntry have to be bound to a enum which contain the possible
values of the select entry.
"""


class SelectEntry(BaseModel, Generic[SelectEnum]):
    """A entry in a single or multiple select field."""
    entry_id: Optional[int] = Field(alias="id")
    value: Optional[SelectEnum]
    color: Optional[str]

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
        for value in cls._get_all_possible_values():
            rsl.append(SelectEntryConfig(value=value))
        return rsl


class SingleSelectField(SelectEntry[SelectEnum], BaserowField):
    """Single select field in a table."""
    @classmethod
    def default_config(cls) -> FieldConfigType:
        options = super(SingleSelectField, cls)._options_config()
        return SingleSelectFieldConfig(select_options=options)


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
        for item in select_enum:
            rsl.append(SelectEntryConfig(value=item.value))
        return MultipleSelectFieldConfig(select_options=rsl)
