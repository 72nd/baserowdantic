"""
Everything related to defining and using filters on data.
"""

import enum
from typing import Optional, Union

from typing_extensions import Self
from pydantic import BaseModel, ConfigDict, Field


class FilterMode(str, enum.Enum):
    """
    The filter type (also called mode) defines the behavior of the filter,
    determining how the filter value is applied to the field. Naming follows the
    Baserow UI convention and therefore may differ from the values in some
    instances.
    """
    EQUAL = "equal"
    NOT_EQUAL = "not_equal"
    DATE_IS = "date_is"
    DATE_IS_NOT = "date_is_not"
    DATE_IS_BEFORE = "date_is_before"
    DATE_IS_ON_OR_BEFORE = "date_is_on_or_before"
    DATE_IS_AFTER = "date_is_after"
    DATE_IS_ON_OR_AFTER = "date_is_on_or_after"
    DATE_IS_WITHIN = "date_is_within"
    DATE_EQUALS_DAY_OF_MONTH = "date_equals_day_of_month"
    CONTAINS = "contains"
    CONTAINS_NOT = "contains_not"
    CONTAINS_WORD = "contains_word"
    DOESNT_CONTAIN_WORD = "doesnt_contain_word"
    FILENAME_CONTAINS = "filename_contains"
    HAS_FILE_TYPE = "has_file_type"
    FILES_LOWER_THAN = "files_lower_than"
    LENGTH_IS_LOWER_THAN = "length_is_lower_than"
    HIGHER_THAN = "higher_than"
    HIGHER_THAN_OR_EQUAL = "higher_than_or_equal"
    LOWER_THAN = "lower_than"
    LOWER_THAN_OR_EQUAL = "lower_than_or_equal"
    IS_EVEN_AND_WHOLE = "is_even_and_whole"
    SINGLE_SELECT_EQUAL = "single_select_equal"
    SINGLE_SELECT_NOT_EQUAL = "single_select_not_equal"
    SINGLE_SELECT_IS_ANY_OF = "single_select_is_any_of"
    SINGLE_SELECT_IS_NONE_OF = "single_select_is_none_of"
    BOOLEAN = "boolean"
    LINK_ROW_HAS = "link_row_has"
    LINK_ROW_HAS_NOT = "link_row_has_not"
    LINK_ROW_CONTAINS = "link_row_contains"
    LINK_ROW_NOT_CONTAINS = "link_row_not_contains"
    MULTIPLE_SELECT_HAS = "multiple_select_has"
    MULTIPLE_SELECT_HAS_NOT = "multiple_select_has_not"
    MULTIPLE_COLLABORATORS_HAS = "multiple_collaborators_has"
    MULTIPLE_COLLABORATORS_HAS_NOT = "multiple_collaborators_has_not"
    EMPTY = "empty"
    NOT_EMPTY = "not_empty"
    USER_IS = "user_is"
    USER_IS_NOT = "user_is_not"


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

    def equal(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Retrieve all records where the specified field exactly matches the given
        value.
        """
        self.conditions.append(
            Condition(field=field, mode=FilterMode.EQUAL, value=value),
        )
        return self

    def not_equal(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Retrieve all records where the specified field does not match the given
        value.
        """
        self.conditions.append(
            Condition(field=field, mode=FilterMode.NOT_EQUAL, value=value),
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

    def date_is(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Adds a condition with date_is to the filter.
        """
        self.conditions.append(
            Condition(field=field, mode=FilterMode.DATE_IS, value=value),
        )
        return self

    def date_is_not(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Adds a condition with date_is_not to the filter.
        """
        self.conditions.append(
            Condition(field=field, mode=FilterMode.DATE_IS_NOT, value=value),
        )
        return self

    def date_is_before(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Adds a condition with date_is_before to the filter.
        """
        self.conditions.append(
            Condition(field=field, mode=FilterMode.DATE_IS_BEFORE, value=value),
        )
        return self

    def date_is_on_or_before(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Adds a condition with date_is_on_or_before to the filter.
        """
        self.conditions.append(
            Condition(
                field=field, mode=FilterMode.DATE_IS_ON_OR_BEFORE, value=value),
        )
        return self

    def date_is_after(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Adds a condition with date_is_after to the filter.
        """
        self.conditions.append(
            Condition(field=field, mode=FilterMode.DATE_IS_AFTER, value=value),
        )
        return self

    def date_is_on_or_after(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Adds a condition with date_is_on_or_after to the filter.
        """
        self.conditions.append(
            Condition(
                field=field, mode=FilterMode.DATE_IS_ON_OR_AFTER, value=value),
        )
        return self

    def date_is_within(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Adds a condition with date_is_within to the filter.
        """
        self.conditions.append(
            Condition(field=field, mode=FilterMode.DATE_IS_WITHIN, value=value),
        )
        return self

    def date_equals_day_of_month(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Adds a condition with date_equals_day_of_month to the filter.
        """
        self.conditions.append(
            Condition(
                field=field, mode=FilterMode.DATE_EQUALS_DAY_OF_MONTH, value=value),
        )
        return self

    def contains_not(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Retrieve all records where the specified field does not contain the
        given value.
        """
        self.conditions.append(
            Condition(field=field, mode=FilterMode.CONTAINS_NOT, value=value),
        )
        return self

    def contains_word(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Retrieve all records where the specified field contains the given word.
        """
        self.conditions.append(
            Condition(field=field, mode=FilterMode.CONTAINS_WORD, value=value),
        )
        return self

    def doesnt_contain_word(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Retrieve all records where the specified field does not contain the
        given word.
        """
        self.conditions.append(
            Condition(
                field=field, mode=FilterMode.DOESNT_CONTAIN_WORD, value=value),
        )
        return self

    def filename_contains(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Adds a condition with filename_contains to the filter.
        """
        self.conditions.append(
            Condition(field=field, mode=FilterMode.FILENAME_CONTAINS,
                      value=value),
        )
        return self

    def has_file_type(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Adds a condition with has_file_type to the filter.
        """
        self.conditions.append(
            Condition(field=field, mode=FilterMode.HAS_FILE_TYPE, value=value),
        )
        return self

    def files_lower_than(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Adds a condition with files_lower_than to the filter.
        """
        self.conditions.append(
            Condition(field=field, mode=FilterMode.FILES_LOWER_THAN, value=value),
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

    def higher_than(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Adds a condition with higher_than to the filter.
        """
        self.conditions.append(
            Condition(field=field, mode=FilterMode.HIGHER_THAN, value=value),
        )
        return self

    def higher_than_or_equal(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Adds a condition with higher_than_or_equal to the filter.
        """
        self.conditions.append(
            Condition(
                field=field, mode=FilterMode.HIGHER_THAN_OR_EQUAL, value=value),
        )
        return self

    def lower_than(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Adds a condition with lower_than to the filter.
        """
        self.conditions.append(
            Condition(field=field, mode=FilterMode.LOWER_THAN, value=value),
        )
        return self

    def lower_than_or_equal(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Adds a condition with lower_than_or_equal to the filter.
        """
        self.conditions.append(
            Condition(
                field=field, mode=FilterMode.LOWER_THAN_OR_EQUAL, value=value),
        )
        return self

    def is_even_and_whole(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Adds a condition with is_even_and_whole to the filter.
        """
        self.conditions.append(
            Condition(field=field, mode=FilterMode.IS_EVEN_AND_WHOLE,
                      value=value),
        )
        return self

    def single_select_equal(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Adds a condition with single_select_equal to the filter.
        """
        self.conditions.append(
            Condition(
                field=field, mode=FilterMode.SINGLE_SELECT_EQUAL, value=value),
        )
        return self

    def single_select_not_equal(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Adds a condition with single_select_not_equal to the filter.
        """
        self.conditions.append(
            Condition(
                field=field, mode=FilterMode.SINGLE_SELECT_NOT_EQUAL, value=value),
        )
        return self

    def single_select_is_any_of(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Adds a condition with single_select_is_any_of to the filter.
        """
        self.conditions.append(
            Condition(
                field=field, mode=FilterMode.SINGLE_SELECT_IS_ANY_OF, value=value),
        )
        return self

    def single_select_is_none_of(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Adds a condition with single_select_is_none_of to the filter.
        """
        self.conditions.append(
            Condition(
                field=field, mode=FilterMode.SINGLE_SELECT_IS_NONE_OF, value=value),
        )
        return self

    def boolean(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Adds a condition with boolean to the filter.
        """
        self.conditions.append(
            Condition(field=field, mode=FilterMode.BOOLEAN, value=value),
        )
        return self

    def link_row_has(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Adds a condition with link_row_has to the filter.
        """
        self.conditions.append(
            Condition(field=field, mode=FilterMode.LINK_ROW_HAS, value=value),
        )
        return self

    def link_row_has_not(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Adds a condition with link_row_has_not to the filter.
        """
        self.conditions.append(
            Condition(field=field, mode=FilterMode.LINK_ROW_HAS_NOT, value=value),
        )
        return self

    def link_row_contains(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Adds a condition with link_row_contains to the filter.
        """
        self.conditions.append(
            Condition(field=field, mode=FilterMode.LINK_ROW_CONTAINS,
                      value=value),
        )
        return self

    def link_row_not_contains(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Adds a condition with link_row_not_contains to the filter.
        """
        self.conditions.append(
            Condition(
                field=field, mode=FilterMode.LINK_ROW_NOT_CONTAINS, value=value),
        )
        return self

    def multiple_select_has(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Adds a condition with multiple_select_has to the filter.
        """
        self.conditions.append(
            Condition(
                field=field, mode=FilterMode.MULTIPLE_SELECT_HAS, value=value),
        )
        return self

    def multiple_select_has_not(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Adds a condition with multiple_select_has_not to the filter.
        """
        self.conditions.append(
            Condition(
                field=field, mode=FilterMode.MULTIPLE_SELECT_HAS_NOT, value=value),
        )
        return self

    def multiple_collaborators_has(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Adds a condition with multiple_collaborators_has to the filter.
        """
        self.conditions.append(
            Condition(
                field=field, mode=FilterMode.MULTIPLE_COLLABORATORS_HAS, value=value),
        )
        return self

    def multiple_collaborators_has_not(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Adds a condition with multiple_collaborators_has_not to the filter.
        """
        self.conditions.append(
            Condition(
                field=field, mode=FilterMode.MULTIPLE_COLLABORATORS_HAS_NOT, value=value),
        )
        return self

    def empty(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Retrieve all records that are empty.
        """
        self.conditions.append(
            Condition(field=field, mode=FilterMode.EMPTY, value=value),
        )
        return self

    def not_empty(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Retrieve all records that are not empty.
        """
        self.conditions.append(
            Condition(field=field, mode=FilterMode.NOT_EMPTY, value=value),
        )
        return self

    def user_is(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Adds a condition with user_is to the filter.
        """
        self.conditions.append(
            Condition(field=field, mode=FilterMode.USER_IS, value=value),
        )
        return self

    def user_is_not(self, field: Union[int, str], value: Optional[str]) -> Self:
        """
        Adds a condition with user_is_not to the filter.
        """
        self.conditions.append(
            Condition(field=field, mode=FilterMode.USER_IS_NOT, value=value),
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
