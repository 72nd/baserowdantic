"""
This module handles the interaction with Baserow's REST API over HTTP.
"""

import asyncio
from re import I
from typing import Any, Generic, Optional, Protocol, Type, TypeVar
import aiohttp
from pydantic import BaseModel, Field, JsonValue

from baserow.error import BaserowError, PackageClientAlreadyDefinedError, SingletonAlreadyConfiguredError, UnspecifiedBaserowError
from baserow.filter import Filter


API_PREFIX = "api"


def _url_join(*parts: str) -> str:
    """Joins given strings into a URL."""
    rsl = [part.strip("/") for part in parts]
    return "/".join(rsl) + "/"


def _list_to_str(items: list[str]) -> str:
    return ",".join(items)


T = TypeVar("T")


class JsonSerializable(Protocol):
    @classmethod
    def model_validate_json(cls, data: str):
        ...


class Response(BaseModel, Generic[T]):
    """The return object of all API calls."""
    count: int
    next: Optional[str]
    previous: Optional[str]
    results: T


class ErrorResponse(BaseModel):
    """
    The return object from Baserow when the request was unsuccessful. Contains
    information about the reasons for the failure.
    """
    error: str
    """Short error enum."""
    detail: Any
    """Additional information on the error."""


class Client:
    """
    This class manages interaction with the Baserow server via HTTP using REST
    API calls. Authentication is handled through a token, which can be generated
    in Baserow. Currently, authentication via JWT (JSON Web Tokens) is not
    supported, as token-based authentication suffices for CRUD operations.

    This client can also be used directly, without utilizing the ORM
    functionality of the package.

    Args:
        url (str): The base URL of the Baserow instance.
        token (str): An access token (referred to as a database token in
            Baserow's documentation) can be generated in the settings of
            Baserow.
    """

    def __init__(self, url: str, token: str):
        self._url: str = url
        self._headers: dict[str, str] = {"Authorization": f"Token {token}"}
        self._session: aiohttp.ClientSession = aiohttp.ClientSession()

    async def list_table_rows(
        self,
        table_id: int,
        user_field_names: bool,
        result_type: Optional[Type[T]] = None,
        filter: Optional[Filter] = None,
        order_by: Optional[list[str]] = None,
        page: Optional[int] = None,
        size: Optional[int] = None,
    ) -> Response[list[T]]:
        """
        Lists rows in the table with the given ID. Note that Baserow uses
        paging. If all rows of a table are needed, the
        Client.list_all_table_rows method can be used.

        Args:
            table_id (int): The ID of the table to be queried.
            user_field_names (bool): When set to true, the returned fields will
                be named according to their field names. Otherwise, the unique
                IDs of the fields will be used.
            result_type (Optional[Type[T]]): Which type will appear as an item
                in the result list and should be serialized accordingly. If set
                to None, Pydantic will attempt to serialize it to the standard
                types.
            filter (Optional[list[Filter]], optional): Allows the dataset to be
                filtered.
            order_by (Optional[list[str]], optional): A list of field names/IDs
                by which the result should be sorted. If the field name is
                prepended with a +, the sorting is ascending; if with a -, it is
                descending.
            page (Optional[int], optional): The page of the paging.
            size (Optional[int], optional): How many records should be returned
                at max. Defaults to 100 and is 200.
        """
        params: dict[str, str] = {}
        params["user_field_names"] = "true" if user_field_names else "false"
        if filter is not None:
            params["filters"] = filter.model_dump_json(by_alias=True)
        if order_by is not None:
            params["order_by"] = _list_to_str(order_by)
        if page is not None:
            params["page"] = str(page)
        if size is not None:
            params["size"] = str(size)
        url = _url_join(
            self._url, API_PREFIX,
            "database/rows/table",
            str(table_id),
        )
        if result_type is not None:
            return await self._request("get", url, list[result_type], params=params)
        return await self._request("get", url, None, params=params)

    async def list_all_table_rows(
        self,
        table_id: int,
        user_field_names: bool,
        result_type: Optional[Type[T]] = None,
        filter: Optional[Filter] = None,
        order_by: Optional[list[str]] = None,
    ) -> Response[list[T]]:
        """
        Since Baserow uses paging, this method sends as many requests to Baserow
        as needed until all rows are received. This function should only be used
        when all data is truly needed. This should be a rare occurrence, as
        filtering can occur on Baserow's side using the filter parameter.

        Args:
            table_id (int): The ID of the table to be queried. user_field_names
            (bool): When set to true, the returned fields will
                be named according to their field names. Otherwise, the unique
                IDs of the fields will be used.
            result_type (Optional[Type[T]]): Which type will appear as an item
                in the result list and should be serialized accordingly. If set
                to None, Pydantic will attempt to serialize it to the standard
                types.
            filter (Optional[list[Filter]], optional): Allows the dataset to be
                filtered.
            order_by (Optional[list[str]], optional): A list of field names/IDs
                by which the result should be sorted. If the field name is
                prepended with a +, the sorting is ascending; if with a -, it is
                descending.
        """
        count: int = await self.table_row_count(table_id)
        total_calls = (count + 200 - 1) // 200

        requests = []
        for page in range(1, total_calls+1):
            rqs = asyncio.create_task(
                self.list_table_rows(
                    table_id,
                    user_field_names,
                    result_type=result_type,
                    filter=filter,
                    order_by=order_by,
                    page=page,
                    size=200,
                )
            )
            requests.append(rqs)
        responses = await asyncio.gather(*requests)

        rsl: Optional[Response[list[T]]] = None
        for rsp in responses:
            if rsl is None:
                rsl = rsp
            else:
                rsl.results.extend(rsp.results)
        if rsl is None:
            return Response(
                count=0,
                previous=None,
                next=None,
                results=[],
            )
        return rsl

    async def table_row_count(self, table_id: int, filter: Optional[Filter] = None) -> int:
        """
        Determines how many rows or records are present in the table with the
        given ID. Filters can be optionally passed as parameters.

        Args:
            table_id (int): The ID of the table to be queried.
            filter (Optional[list[Filter]], optional): Allows the dataset to be
                filtered. Only rows matching the filter will be counted.
        """
        rsl = await self.list_table_rows(table_id, True, filter=filter, size=1)
        return rsl.count

    async def close(self):
        """Close the session."""
        await self._session.close()

    async def _request(
        self,
        method: str,
        url: str,
        result_type: Optional[Type[T]],
        headers: Optional[dict[str, str]] = None,
        params: Optional[dict[str, str]] = None,
        json: Optional[dict[str, str]] = None,
    ) -> Response[T]:
        """
        Handles the actual HTTP request.

        Args:
            result_type (Type[T]): The pydantic model which should be used to
                serialize the response field of the response. If set to None
                pydantic will try to serialize the response with built-in types.
                Aka `pydantic.JsonValue`.
        """
        request_headers = self._headers
        if headers is not None:
            request_headers = self._headers.copy()
            request_headers.update(headers)
        async with self._session.request(
            method,
            url,
            headers=request_headers,
            params=params,
            json=json,
        ) as rsp:
            if rsp.status == 400:
                err = ErrorResponse.model_validate_json(await rsp.text())
                raise BaserowError(rsp.status, err.error, err.detail)
            if rsp.status != 200:
                raise UnspecifiedBaserowError(rsp.status, await rsp.text())
            if result_type is not None:
                model = Response[result_type]
            else:
                model = Response[Any]
            return model.model_validate_json(await rsp.text())


class SingletonClient(Client):
    """
    The singleton version of the client encapsulates the client in a singleton.
    The parameters (URL and access tokens) can be configured independently of
    the actual instantiation.

    Unless specified otherwise, this singleton is used by all table instances
    for accessing Baserow.

    This is helpful in systems where the client can be configured once at
    program start (e.g., in the `__main__.py`) based on the settings file and
    then used throughout the program without specifying additional parameters.
    The Singleton pattern ensures that only one instance of the client is used
    throughout the entire program, thereby maintaining full control over the
    `aiohttp.ClientSession`.
    """
    _instance: Optional[Client] = None
    _is_initialized: bool = False
    _is_configured: bool = False
    __url: str = ""
    __token: str = ""

    def __new__(cls):
        if not cls._is_configured:
            raise RuntimeError(
                "client singleton has to be configured first using the configure() method"
            )
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._is_initialized:
            super().__init__(self.__url, self.__token)
            self._is_initialized = True

    @classmethod
    def configure(cls, url: str, token: str):
        """
        Set the URL and token before the first use of the client.
        """
        if cls._is_configured:
            raise SingletonAlreadyConfiguredError(
                "singleton client was already configured",
            )
        cls.__url = url
        cls.__token = token
        cls._is_configured = True


global_client = SingletonClient
"""
If the functions of the package should always interact with the same Baserow
instance in an application, the global client can be set. Once configured, this
client will be used for all API calls, unless a different client is specified
for specific functions. To configure this, the client_config method should be
used.

To prevent unpredictable behavior, the package-wide client can only be set once
per runtime.
"""


def client_config(url: str, token: str):
    """
    This method can be used to set up the package-wide client, which will then
    be utilized by default unless a specific client is designated for a given
    method. The client can only be configured once.
    """
    try:
        global_client.configure(url, token)
    except SingletonAlreadyConfiguredError:
        raise PackageClientAlreadyDefinedError(global_client()._url, url)
