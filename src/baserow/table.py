"""
The module provides the ORM-like functionality of Baserowdantic.
"""


import abc
from typing import ClassVar, Optional, Type, TypeVar

from pydantic import BaseModel, computed_field, field_validator, model_validator

from baserow.client import Client, GlobalClient
from baserow.error import InvalidTableConfiguration, NoClientAvailableError
from baserow.filter import Filter


def valid_configuration(func):
    """
    This decorator checks whether the model configuration has been done
    correctly. In addition to validating the class vars Table.table_id and
    Table.table_name, it also verifies whether the model config is set with
    populate_by_name=True.
    """

    def wrapper(cls, *args, **kwargs):
        if not isinstance(cls.table_id, int):
            raise InvalidTableConfiguration(cls.__name__, "table_id not set")
        if not isinstance(cls.table_name, str):
            raise InvalidTableConfiguration(cls.__name__, "table_name not set")
        if "populate_by_name" not in cls.model_config:
            raise InvalidTableConfiguration(
                cls.__name__,
                "populate_by_name is not set in the model config; it should most likely be set to true"
            )
        return func(cls, *args, **kwargs)
    return wrapper


T = TypeVar("T", bound="Table")


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
    async def query(
        cls: Type[T],
        filter: Optional[Filter] = None,
        order_by: Optional[list[str]] = None,
        page: Optional[int] = None,
        size: Optional[int] = None,
    ):
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
