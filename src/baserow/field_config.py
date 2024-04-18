"""
This module handles the config/properties of individual fields. These classes
cannot be used to parse/validate data coming from Baserow.
"""


import enum
from os import fchdir
import random

from typing import Annotated, Literal, Optional, Union
from pydantic import BaseModel, Field, RootModel


def random_color() -> str:
    """Returns a random color as a hex-string."""
    min_delta = 30
    red, green, blue = 0, 0, 0
    while abs(red - green) < min_delta or abs(green-blue) < min_delta or abs(red-blue) < min_delta:
        red = random.randint(0, 255)
        green = random.randint(0, 255)
        blue = random.randint(0, 255)
    return f"#{red:02x}{green:02x}{blue:02x}"


class FieldConfigBasic(BaseModel):
    """
    Many of the fields (or rows) in Baserow tables have certain properties that
    can be set. These are managed with this class. Each field type implements
    its own Config class. Using these config classes, new fields can be created
    in a table.
    """
    name: str = Field(max_length=255)


class TextFieldConfig(FieldConfigBasic):
    """
    A single line text field is a type of field that allows you to input short
    and unique pieces of text into your table.
    """
    type: Literal["text"]
    text_default: str = Field(default="", max_length=255)


class LongTextFieldConfig(FieldConfigBasic):
    """
    A long text field can contain long paragraphs or multiple lines of text.
    """
    type: Literal["long_text"]
    long_text_enable_rich_text: bool = False


class URLFieldConfig(FieldConfigBasic):
    """The URL field holds a single URL."""
    type: Literal["url"]


class EMailFieldConfig(FieldConfigBasic):
    """
    An email field is a type of field that allows input of a single email
    address in a cell in the right format. When you click on an email address
    inside of an email field, your computer's default email client will launch
    with the clicked email's To: address in the To: field.
    """
    type: Literal["email"]


class NumberFieldConfig(FieldConfigBasic):
    """The number field is a field type that holds numerical values."""
    type: Literal["number"]
    number_decimal_places: int = 0
    """The amount of digits allowed after the point."""
    number_negative: bool = True
    """Indicates if negative values are allowed."""


class RatingStyle(str, enum.Enum):
    """Style of rating symbols."""
    STAR = "star"
    HEART = "heart"
    THUMBS_UP = "thumbs-up"
    FLAG = "flag"
    SMILE = "smile"


class RatingFieldConfig(FieldConfigBasic):
    """
    A rating field is used to rate your rows in order to rank or evaluate their
    quality.
    """
    type: Literal["rating"]
    max_value: int = Field(default=5, ge=1, le=10)
    """Maximum value the rating can take."""
    color: str = ""
    """Color of the symbols."""
    style: RatingStyle = RatingStyle.STAR
    """Style of rating symbols."""


class BooleanFieldConfig(FieldConfigBasic):
    """
    The boolean field represents information in a binary true/false format.
    """
    type: Literal["boolean"]


class DateFormat(str, enum.Enum):
    """Format of the date-string."""
    EU = "EU"
    """European, D/M/Y, 20/02/2020."""
    US = "US"
    """US, M/D/Y, 02/20/2022."""
    ISO = "ISO"
    """ISO, Y-M-D, 2020-02-20."""


class TimeFormat(int, enum.Enum):
    """Format of the time. 24 or 23 hour."""
    HOUR_24 = 24
    HOUR_12 = 12


class GenericDateFieldConfig(FieldConfigBasic):
    """
    Generic date field config for all field types handling date(-time) values.
    """
    date_format: DateFormat = DateFormat.ISO
    """EU, US or ISO."""
    date_include_time: bool = False
    """Indicates if the field also includes a time."""
    date_time_format: TimeFormat = TimeFormat.HOUR_24
    """12 (am/pm) or 24 hour format."""
    date_show_tzinfo: bool = False
    """Indicates if the timezone should be shown."""
    date_force_timezone: Optional[str] = Field(default=None, max_length=255)
    """Force a timezone for the field overriding user profile settings."""
    date_force_timezone_offset: Optional[int] = Field(default=None)
    """A UTC offset in minutes to add to all the field datetimes values."""


class DateFieldConfig(GenericDateFieldConfig):
    """
    A UTC offset in minutes to add to all the field datetimes values.
    """
    type: Literal["date"]


class LastModifiedFieldConfig(GenericDateFieldConfig):
    """
    The last modified field type returns the most recent date and time that a
    row was modified. 
    """
    type: Literal["last_modified"]


class LastModifiedByFieldConfig(FieldConfigBasic):
    """
    Track decisions and actions to specific individuals for historical reference
    or follow-up.
    """
    type: Literal["last_modified_by"]


class CreatedOnFieldConfig(GenericDateFieldConfig):
    """
    The created on field type will automatically show the date and time that a
    row was created by a user.
    """
    type: Literal["created_on"]


class CreatedByFieldConfig(FieldConfigBasic):
    """
    Automatically tracks and displays the name of the collaborator who created
    each row within a table.
    """
    type: Literal["created_by"]


class DurationFormat(str, enum.Enum):
    """Possible display formats for durations."""
    HOURS_MINUTES = "h:mm"
    HOURS_MINUTES_SECONDS = "h:mm:ss"
    HOURS_MINUTES_SECONDS_DECISECONDS = "h:mm:ss.s"
    HOURS_MINUTES_SECONDS_CENTISECONDS = "h:mm:ss.ss"
    HOURS_MINUTES_SECONDS_MILLISECONDS = "h:mm:ss.sss"
    DAYS_HOURS = "d h"
    DAYS_HOURS_MINUTES = "d h:mm"
    DAYS_HOURS_MINUTES_SECONDS = "d h:mm:ss"


class DurationFieldConfig(FieldConfigBasic):
    """
    Stores time durations measured in hours, minutes, seconds, or milliseconds.
    """
    type: Literal["duration"]
    duration_format: DurationFormat = DurationFormat.HOURS_MINUTES_SECONDS
    """Possible display formats."""


class LinkFieldConfig(FieldConfigBasic):
    """
    A link to table field creates a link between two existing tables by
    connecting data across tables with linked rows.
    """
    type: Literal["link_row"]
    link_row_table_id: Optional[int] = None
    """The id of the linked table."""
    has_related_field: bool = False


class FileFieldConfig(FieldConfigBasic):
    """
    A file field allows you to easily upload one or more files from your device
    or from a URL.
    """
    type: Literal["file"]


class SelectEntryConfig(BaseModel):
    """Config for a entry in a single or multiple select field."""
    id: Optional[int] = None
    value: str = Field(max_length=255)
    color: str = Field(max_length=255, default_factory=random_color)


class SingleSelectFieldConfig(FieldConfigBasic):
    """
    The single select field type is a field type containing defined options to
    choose only one option from a set of options.
    """
    type: Literal["single_select"]
    select_options: list[SelectEntryConfig]


class MultipleSelectFieldConfig(FieldConfigBasic):
    """
    A multiple select field contains a list of tags to choose multiple options
    from a set of options. 
    """
    type: Literal["multiple_select"]


class PhoneNumberFieldConfig(FieldConfigBasic):
    """
    The phone number field will format a string of numbers as a phone number, in
    the form (XXX) XXX-XXXX.
    """
    type: Literal["phone_number"]


class FormulaType(str, enum.Enum):
    """Types of formula result value."""
    INVALID = "invalid"
    TEXT = "text"
    CHAR = "char"
    BUTTON = "button"
    LINK = "link"
    DATE_INTERVAL = "date_interval"
    DURATION = "duration"
    DATE = "date"
    BOOLEAN = "boolean"
    NUMBER = "number"
    ARRAY = "array"
    SINGLE_SELECT = "single_select"
    MULTIPLE_SELECT = "multiple_select"
    SINGLE_FILE = "single_file"


class GenericFormulaFieldConfig(FieldConfigBasic):
    """
    Generic type for fields which can contain all multiple fields types.
    """
    date_show_tzinfo: bool = False
    """Indicates if the timezone should be shown."""
    number_decimal_places: int = 0
    """The amount of digits allowed after the point."""
    duration_format: DurationFormat = DurationFormat.HOURS_MINUTES_SECONDS
    """Possible display formats."""
    date_force_timezone: Optional[str] = Field(default=None, max_length=255)
    """Force a timezone for the field overriding user profile settings."""
    array_formula_type: Optional[list[FormulaType]]
    """
    The type of the values within the array if `formula_type` is set to array.
    Please note that the type array is not allowed. As an array within an array
    is not possible in Baserow.
    """
    error: Optional[str] = None
    date_format: DateFormat = DateFormat.ISO
    """EU, US or ISO."""
    date_include_time: bool = False
    """Indicates if the field also includes a time."""
    date_time_format: TimeFormat = TimeFormat.HOUR_24
    """12 (am/pm) or 24 hour format."""
    formula: str
    """The actual formula."""
    formula_type: FormulaType
    """Type of the formula result."""


class FormulaFieldConfig(GenericFormulaFieldConfig):
    """
    A value in each row can be calculated using a formula based on values in
    cells in the same row.
    """
    type: Literal["formula"]


class CountFieldConfig(GenericFormulaFieldConfig):
    """
    The count field will automatically count the number of rows linked to a
    particular row in your database.
    """
    type: Literal["count"]


class RollupFieldConfig(GenericFormulaFieldConfig):
    """Aggregate data and gain valuable insights from linked tables."""
    type: Literal["rollup"]


class LookupFieldConfig(GenericFormulaFieldConfig):
    """
    You can look for a specific field in a linked row using a lookup field.
    """
    type: Literal["lookup"]


class MultipleCollaboratorsFieldConfig(FieldConfigBasic):
    """
    Assign collaborators by selecting names from a list of workspace members.
    """
    type: Literal["multiple_collaborators"]
    notify_user_when_added: bool = False


class UUIDFieldConfig(FieldConfigBasic):
    """Create and work with unique record identifiers within a table."""
    type: Literal["uuid"]


class AutonumberFieldConfig(FieldConfigBasic):
    """
    Automatically generates unique and sequential numbers for each record in a
    table.
    """
    type: Literal["autonumber"]
    view: Optional[int] = None
    """The id of the view to use for the initial ordering."""


class PasswordFieldConfig(FieldConfigBasic):
    """
    Ensure robust security measures for your data. Currently only used for the
    application builder.
    """
    type: Literal["password"]


class AIFieldConfig(FieldConfigBasic):
    """
    Generate creative briefs, summarize information, and more.
    """
    type: Literal["ai"]
    ai_generative_ai_type: Optional[str] = Field(default=None, max_length=32)
    ai_generative_ai_model: Optional[str] = Field(default=None, max_length=32)
    ai_prompt: str = ""
    """The prompt that must run for each row. Must be an formula."""


FieldConfigType = Annotated[
    Union[
        TextFieldConfig,
        LongTextFieldConfig
    ],
    Field(discriminator="type"),
]


class FieldConfig(RootModel[FieldConfigType]):
    root: FieldConfigType
