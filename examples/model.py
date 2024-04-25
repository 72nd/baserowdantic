from datetime import datetime, timedelta
import enum
from typing import Annotated, Optional

from baserow.field import CreatedByField, FileField, LastModifiedByField, MultipleCollaboratorsField, MultipleSelectField, SingleSelectField
from baserow.table import Table, TableLinkField
from baserow.field_config import Config, LongTextFieldConfig, PrimaryField, RatingFieldConfig, RatingStyle
from pydantic import UUID4, ConfigDict, Field


class Company(Table):
    table_id = 1203
    table_name = "Company"
    model_config = ConfigDict(populate_by_name=True)

    row_id: Optional[int] = Field(alias=str("id"), default=None)
    name: str = Field(alias=str("Name"))
    email: Optional[str] = Field(default=None, alias=str("E-Mail"))


class State(str, enum.Enum):
    INTERN = "Intern"
    TEMPORARY = "Temporary"
    PERMANENT = "Permanent employee"
    TERMINATED = "Terminated"


class Qualification(str, enum.Enum):
    ABITUR = "Abitur"
    FIRST_AIDER = "First aider"
    FIREFIGHTER = "Firefighter"
    SOCIAL_WORKER = "Social worker"


class PersonTable(Table):
    table_id = 1201
    table_name = "Person"
    model_config = ConfigDict(populate_by_name=True)

    name: Annotated[
        str,
        Field(alias=str("Name")),
        PrimaryField(),
    ]
    age: int = Field(alias=str("Age"))
    cv: Annotated[
        Optional[str],
        Config(LongTextFieldConfig()),
        Field(alias=str("CV")),
    ]
    former_employees: Optional[TableLinkField[Company]] = Field(
        default=None,
        alias=str("Former Employers"),
    )
    nda_signed: bool = Field(alias=str("NDA Signed"))
    employed_since: Optional[datetime] = Field(
        default=None, alias=str("Employed since"))
    rating: Annotated[
        int,
        Config(RatingFieldConfig(max_value=5, style=RatingStyle.HEART)),
        Field(alias=str("Rating")),
    ]
    last_modified: Optional[datetime] = Field(
        default=None, alias=str("Last modified"),
    )
    last_modified_by: Optional[LastModifiedByField] = Field(
        default=None, alias=str("Last modified by"),
    )
    created_on: Optional[datetime] = Field(
        default=None, alias=str("Created on"))
    created_by: Optional[CreatedByField] = Field(
        default=None, alias=str("Created by"))
    workhours_per_day: Optional[timedelta] = Field(
        default=None, alias=str("Workhours per day"))
    personal_website: Optional[str] = Field(
        default=None, alias=str("Personal Website"))
    email: Optional[str] = Field(default=None, alias=str("E-Mail"))
    contract: Optional[FileField] = Field(default=None, alias=str("Contract"))
    collaborators: Optional[MultipleCollaboratorsField] = Field(
        default=None, alias=str("Collaborators"))
    state: Optional[SingleSelectField[State]] = Field(
        default=None, alias=str("State"),
    )
    qualifications: Optional[MultipleSelectField[Qualification]] = Field(
        default=None, alias=str("Qualifications"),
    )
    phone: Optional[str] = Field(default=None, alias=str("Phone"))
    uuid: Optional[UUID4] = Field(default=None, alias=str("UUID"))
