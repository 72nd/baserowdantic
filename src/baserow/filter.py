"""
Everything related to defining and using filters on data.
"""

import enum
from typing import Optional, Self, Union
from pydantic import BaseModel, ConfigDict, Field, aliases


class FilterMode(str, enum.Enum):
    """
    The filter type (also called mode) defines the behavior of the filter,
    determining how the filter value is applied to the field. Naming follows the
    Baserow UI convention and therefore may differ from the values in some
    instances.
    """
    EQUALS = "equal"
    EQUALS_NOT = "not_equal"
    CONTAINS = "contains"
    DOES_NOT_CONTAIN = "contains_not"
    CONTAIN_WORD = "contains_word"
    DOES_NOT_CONTAIN_WORD = "doesnt_contain_word"
    LENGTH_IS_LOWER_THAN = "length_is_lower_than"
    IS_EMPTY = "empty"
    IS_NOT_EMPTY = "not_empty"


class Condition(BaseModel):
    """
    A filter condition is a single filter condition that can be applied to a
    field.
    """
    model_config = ConfigDict(populate_by_name=True)

    field: Union[int, str]
    """
    Field name with `user_field_names`, otherwise field ID as an integer.
    """
    mode: FilterMode = Field(alias=str("type"))
    value: Optional[str]
    """The value that the filter should check against."""


class Operator(str, enum.Enum):
    """
    Defines how multiple filter items within a filter interact with each other.
    """
    AND = "AND"
    """All filter items must be true."""
    OR = "OR"
    """At least one filter item in the filter must be true."""


class Filter(BaseModel):
    """
    A filter tree allows for the construction of complex filter queries. The
    object serves as a container for individual filter conditions, all of which
    must be true (AND) or at least one must be true (OR).
    """
    operator: Operator = Field(alias=str("filter_type"))
    conditions: list[Condition] = Field(default=[], alias=str("filters"))

    def equals(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Retrieve all records where the specified field exactly matches the given
        value.
        """
        self.conditions.append(
            Condition(field=field, mode=FilterMode.EQUALS, value=value),
        )
        return self

    def not_equals(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Retrieve all records where the specified field does not match the given
        value.
        """
        self.conditions.append(
            Condition(field=field, mode=FilterMode.EQUALS_NOT, value=value),
        )
        return self

    def contains(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Retrieve all records where the specified field contains the given value.
        """
        self.conditions.append(
            Condition(field=field, mode=FilterMode.CONTAINS, value=value),
        )
        return self

    def does_not_contain(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Retrieve all records where the specified field does not contain the
        given value.
        """
        self.conditions.append(
            Condition(field=field, mode=FilterMode.DOES_NOT_CONTAIN, value=value),
        )
        return self

    def contain_word(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Retrieve all records where the specified field contains the given word.
        """
        self.conditions.append(
            Condition(field=field, mode=FilterMode.CONTAIN_WORD, value=value),
        )
        return self

    def does_not_contain_word(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Retrieve all records where the specified field does not contain the
        given word.
        """
        self.conditions.append(
            Condition(
                field=field, mode=FilterMode.DOES_NOT_CONTAIN_WORD, value=value),
        )
        return self

    def length_is_lower_than(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Retrieve all records where the specified field does not exceed the given
        length.
        """
        self.conditions.append(
            Condition(
                field=field, mode=FilterMode.LENGTH_IS_LOWER_THAN, value=value),
        )
        return self

    def is_empty(self, field: Union[int, str]) -> Self:
        """
        Retrieve all records that are empty.
        """
        self.conditions.append(
            Condition(field=field, mode=FilterMode.IS_EMPTY, value=None),
        )
        return self

    def is_not_empty(self, field: Union[int, str]) -> Self:
        """
        Retrieve all records that are not empty.
        """
        self.conditions.append(
            Condition(field=field, mode=FilterMode.IS_NOT_EMPTY, value=None),
        )
        return self


class AndFilter(Filter):
    """
    A filter tree allows for the construction of complex filter queries. The
    object serves as a container for individual filter conditions, all of which
    must be true (AND filter).
    """
    operator: Operator = Field(
        default=Operator.AND, alias=str("filter_type"), frozen=True)


class OrFilter(Filter):
    """
    A filter tree allows for the construction of complex filter queries. The
    object serves as a container for individual filter conditions, all of any
    can be true (OR filter).
    """
    operator: Operator = Field(
        default=Operator.OR, alias=str("filter_type"), frozen=True)
