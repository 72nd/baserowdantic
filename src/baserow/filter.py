"""
Everything related to defining and using filters on data.
"""

import enum
from typing import Optional, Union
from pydantic import BaseModel


class FilterMode(str, enum.Enum):
    """
    The filter type (also called mode) defines the behavior of the filter,
    determining how the filter value is applied to the field. Naming follows the
    Baserow UI convention and therefore may differ from the values in some
    instances.
    """
    IS = "equal"
    IS_NOT = "not_equal"
    CONTAINS = "contains"
    DOES_NOT_CONTAIN = "contains_not"
    CONTAIN_WORD = "contains_word"
    DOES_NOT_CONTAIN_WORD = "doesnt_contain_word"
    LENGTH_IS_LOWER_THAN = "length_is_lower_than"
    IS_EMPTY = "empty"
    IS_NOT_EMPTY = "not_empty"


class FilterItem(BaseModel):
    """A Filter object is a single filter that can be applied to a field."""
    field: Union[int, str]
    """
    Field name with `user_field_names`, otherwise field ID as an integer.
    """
    type: FilterMode
    value: Optional[str]
    """The value that the filter should check against."""


class FilterType(str, enum.Enum):
    """
    Defines how multiple filter items within a filter interact with each other.
    """
    AND = "and"
    """All filter items must be true."""
    OR = "or"
    """At least one filter item in the filter must be true."""


class Filter(BaseModel):
    """
    A filter tree allows for the construction of complex filter queries. The
    Tree object serves as a container for individual filter conditions, all of
    which must be true (AND) or at least one must be true (OR).
    """
    filter_type: FilterType
    filters: list[FilterItem]
