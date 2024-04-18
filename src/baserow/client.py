"""
This module handles the interaction with Baserow's REST API over HTTP.
"""

import asyncio
from contextvars import Token
import enum
from re import I
from typing import Any, Generic, Optional, Protocol, Type, TypeVar, Union
import aiohttp
from pydantic import BaseModel, Field, RootModel

from baserow.error import BaserowError, JWTAuthRequiredError, PackageClientAlreadyDefinedError, SingletonAlreadyConfiguredError, UnspecifiedBaserowError
from baserow.field import FieldType
from baserow.field_config import FieldConfig, FieldConfigType
from baserow.filter import Filter


API_PREFIX: str = "api"
"""URL prefix for all API call URLs."""

CONTENT_TYPE_JSON: dict[str, str] = {"Content-Type": "application/json"}
"""HTTP Header when content type is JSON."""


def _url_join(*parts: str) -> str:
    """Joins given strings into a URL."""
    rsl = [part.strip("/") for part in parts]
    return "/".join(rsl) + "/"


def _list_to_str(items: list[str]) -> str:
    return ",".join(items)


T = TypeVar("T", bound=Union[BaseModel, RootModel])

A = TypeVar("A")


class JsonSerializable(Protocol):
    @classmethod
    def model_validate_json(cls, data: str):
        ...


class RowResponse(BaseModel, Generic[T]):
    """The return object of list row API calls."""
    count: int
    next: Optional[str]
    previous: Optional[str]
    results: list[T]


class MinimalRow(BaseModel):
    """The minimal result items of a `RowResponse`."""
    id: int


class TokenResponse(BaseModel):
    """Result of an authentication token call."""
    user: Any
    access_token: str
    refresh_token: str


class DatabaseTableResponse(BaseModel):
    """Describes a table within a database in Baserow."""
    id: int
    name: str
    order: int
    database_id: int


class DatabaseTablesResponse(RootModel[list[DatabaseTableResponse]]):
    """Contains all tables for a database in Baserow."""
    root: list[DatabaseTableResponse]


class FieldResponse(RootModel[list[FieldConfig]]):
    """
    The response for the list field call. Contains all fields of a table.
    """
    root: list[FieldConfig]


class BatchResponse(BaseModel, Generic[A]):
    """
    Response for batch mode. The results of a batch call are encapsulated in
    this response.
    """
    items: list[A]


class ErrorResponse(BaseModel):
    """
    The return object from Baserow when the request was unsuccessful. Contains
    information about the reasons for the failure.
    """
    error: str
    """Short error enum."""
    detail: Any
    """Additional information on the error."""


class AuthMethod(int, enum.Enum):
    """
    Differentiates between the two authentication methods for the client.
    Internal use only. For more information on the two different authentication
    methods, refer to the documentation for the `Client` class.
    """

    DATABASE_TOKEN = 0
    """Authentication with the database token."""
    JWT = 1
    """Authentication with user credentials."""


def jwt_only(func):
    """
    Decorator for operations that can only be executed with a JWT token
    (authenticated via login credentials). If a database token is used,
    `TokenAuthNotAllowedError` is thrown.
    """

    def wrapper(self, *args, **kwargs):
        if self._auth_method is not AuthMethod.JWT:
            raise JWTAuthRequiredError(func.__name__)
        return func(self, *args, **kwargs)
    return wrapper


class Client:
    """
    This class manages interaction with the Baserow server via HTTP using REST
    API calls. Access to the Baserow API requires authentication, and there are
    tow methods available: Database Tokens and JWT Tokens.

    Database tokens are designed for delivering data to frontends and, as such,
    can only perform CRUD (Create, Read, Update, Delete) operations on a
    database. New tokens can be created in the User Settings, where their
    permissions can also be configured. JWT Tokens are required for all other
    functionalities, which can be obtained by providing login credentials (email
    address and password) to the Baserow API. A client can only be initialized
    with either the database token OR the login credentials.

    This client can also be used directly, without utilizing the ORM
    functionality of the package.

    Args:
        url (str): The base URL of the Baserow instance.
        token (str, optional): An access token (referred to as a database token
            in Baserow's documentation) can be generated in the user settings
            within Baserow.
        email (str, optional): Email address of a Baserow user for the JWT
            authentication.
        password (str, optional): Password of a Baserow user for the JWT
            authentication.
    """

    def __init__(
        self,
        url: str,
        token: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
    ):
        if not token and not email and not password:
            raise ValueError(
                "you must either provide a database token or the login credentials (email, password) of a user"
            )
        if token and (email or password):
            raise ValueError(
                "passing parameters for both types of authentication (database token and login credentials) simultaneously is not allowed"
            )
        if not token and (not email or not password):
            missing = "email" if not email else "password"
            raise ValueError(
                f"""incomplete authentication with login credentials, {
                    missing} is missing"""
            )
        self._url = url
        self._token = token
        self._email = email
        self._password = password
        self._session: aiohttp.ClientSession = aiohttp.ClientSession()
        self._auth_method = AuthMethod.DATABASE_TOKEN if token else AuthMethod.JWT
        # Cache is only accessed by __header() method.
        self.__headers_cache: Optional[dict[str, str]] = None

    async def token_auth(self, email: str, password: str) -> TokenResponse:
        """
        Authenticates an existing user based on their email and their password.
        If successful, an access token will be returned.

        This method is designed to function even with a partially initialized
        instance, as it's used for optional JWT token retrieval during class
        initialization.

        Args:
            email (str): Email address of a Baserow user for the JWT
                authentication.
            password (str): Password of a Baserow user for the JWT
                authentication.
            url (url, optional): Optional base url.
            session (aiohttp.ClientSession, optional): Optional client session.
        """
        return await self._typed_request(
            "post",
            _url_join(self._url, API_PREFIX, "user/token-auth"),
            TokenResponse,
            headers=CONTENT_TYPE_JSON,
            json={"email": email, "password": password},
            use_default_headers=False,
        )

    async def list_table_rows(
        self,
        table_id: int,
        user_field_names: bool,
        result_type: Optional[Type[T]] = None,
        filter: Optional[Filter] = None,
        order_by: Optional[list[str]] = None,
        page: Optional[int] = None,
        size: Optional[int] = None,
    ) -> RowResponse[T]:
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
        params: dict[str, str] = {
            "user_field_names": "true" if user_field_names else "false",
        }
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
        if result_type:
            model = RowResponse[result_type]
        else:
            model = RowResponse[Any]
        return await self._typed_request("get", url, model, params=params)

    async def list_all_table_rows(
        self,
        table_id: int,
        user_field_names: bool,
        result_type: Optional[Type[T]] = None,
        filter: Optional[Filter] = None,
        order_by: Optional[list[str]] = None,
    ) -> RowResponse[T]:
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

        rsl: Optional[RowResponse[T]] = None
        for rsp in responses:
            if rsl is None:
                rsl = rsp
            else:
                rsl.results.extend(rsp.results)
        if rsl is None:
            return RowResponse(
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

    async def list_fields(self, table_id: int) -> FieldResponse:
        """
        Lists all fields (»columns«) of a table.

        Args:
            table_id (int): The ID of the table to be queried.
        """
        return await self._typed_request(
            "get",
            _url_join(
                self._url,
                API_PREFIX,
                "database/fields/table/",
                str(table_id),
            ),
            FieldResponse,
        )

    async def get_row(
        self,
        table_id: int,
        row_id: int,
        user_field_names: bool,
        result_type: Optional[Type[T]] = None,
    ) -> T:
        """
        Fetch a single row/entry from the given table by the row ID.

        Args:
            table_id (int): The ID of the table to be queried.
            row_id (int): The ID of the row to be returned.
            user_field_names (bool): When set to true, the fields in the
                provided data parameter are named according to their field
                names. Otherwise, the unique IDs of the fields will be used.
            result_type (Optional[Type[T]]): Which type will appear as an item
                in the result list and should be serialized accordingly. If set
                to None, Pydantic will attempt to serialize it to the standard
                types.
        """
        if result_type:
            model = result_type
        else:
            model = Any
        return await self._typed_request(
            "get",
            _url_join(
                self._url,
                API_PREFIX,
                "database/rows/table",
                str(table_id),
                str(row_id),
            ),
            model,
            params={"user_field_names": "true" if user_field_names else "false"}
        )

    async def create_row(
        self,
        table_id: int,
        data: Union[T, dict[str, Any]],
        user_field_names: bool,
        before: Optional[int] = None,
    ) -> Union[T, MinimalRow]:
        """
        Creates a new row in the table with the given ID. The data can be
        provided either as a dictionary or as a Pydantic model. Please note that
        this method does not check whether the fields provided with `data`
        actually exist.

        The return value depends on the `data` parameter: If a Pydantic model is
        passed, the return value is an instance of this model with the values as
        they are in the newly created row. If any arbitrary dictionary is
        passed, `MinimalRow` is returned, which contains only the ID field.

        Args:
            table_id (int): The ID of the table where the new row should be
                created.
            data (Union[T, dict[str, Any]]): The data of the new row.
            user_field_names (bool): When set to true, the fields in the
                provided data parameter are named according to their field
                names. Otherwise, the unique IDs of the fields will be used.
            before (Optional[int], optional):  If provided then the newly
                created row will be positioned before the row with the provided
                id. 
        """
        params: dict[str, str] = {
            "user_field_names": "true" if user_field_names else "false",
        }
        if before is not None:
            params["before"] = str(before)

        if not isinstance(data, dict):
            json = data.model_dump(by_alias=True)
        else:
            json = data

        return await self._typed_request(
            "post",
            _url_join(
                self._url,
                API_PREFIX,
                "database/rows/table",
                str(table_id),
            ),
            type(data) if not isinstance(data, dict) else MinimalRow,
            CONTENT_TYPE_JSON,
            params,
            json,
        )

    async def create_rows(
        self,
        table_id: int,
        data: Union[list[T], list[dict[str, Any]]],
        user_field_names: bool,
        before: Optional[int] = None,
    ) -> Union[BatchResponse[T], BatchResponse[MinimalRow]]:
        """
        Creates one or multiple new row(w) in the table with the given ID using
        Baserow's batch functionality. The data can be provided either as a list
        of dictionaries or as a Pydantic models. Please note that this method
        does not check whether the fields provided with `data` actually exist.

        The return value depends on the `data` parameter: If a Pydantic model is
        passed, the return value is an instance of this model with the values as
        they are in the newly created row. If any arbitrary dictionary is
        passed, `MinimalRow` is returned, which contains only the ID field.

        If the given list is empty, no call is executed; instead, an empty
        response is returned.

        Args:
            table_id (int): The ID of the table where the new row should be
                created.
            data (Union[list[T], list[dict[str, Any]]]): The data of the new
                row.
            user_field_names (bool): When set to true, the fields in the
                provided data parameter are named according to their field
                names. Otherwise, the unique IDs of the fields will be used.
            before (Optional[int], optional):  If provided then the newly
                created row will be positioned before the row with the provided
                id. 
        """
        if len(data) == 0:
            return BatchResponse(items=[])
        params: dict[str, str] = {
            "user_field_names": "true" if user_field_names else "false",
        }
        if before is not None:
            params["before"] = str(before)
        if len(data) == 0:
            raise ValueError("data parameter cannot be empty list")
        if not isinstance(data[0], dict):
            result_type = BatchResponse[type(data[0])]
        else:
            result_type = BatchResponse[MinimalRow]
        items: list[dict[str, Any]] = []
        for item in data:
            if not isinstance(item, dict):
                items.append(item.model_dump(by_alias=True))
            else:
                items.append(item)
        json = {"items": items}
        return await self._typed_request(
            "post",
            _url_join(
                self._url,
                API_PREFIX,
                "database/rows/table",
                str(table_id),
                "batch",
            ),
            result_type,
            CONTENT_TYPE_JSON,
            params,
            json,
        )

    async def update_row(
        self,
        table_id: int,
        row_id: int,
        data: Union[T, dict[str, Any]],
        user_field_names: bool,
    ) -> Union[T, MinimalRow]:
        """ 
        Updates a row by it's ID in the table with the given ID. The data can be
        provided either as a dictionary or as a Pydantic model. Please note that
        this method does not check whether the fields provided with `data`
        actually exist.

        The return value depends on the `data` parameter: If a Pydantic model is
        passed, the return value is an instance of this model with the values as
        they are in the newly created row. If any arbitrary dictionary is
        passed, `MinimalRow` is returned, which contains only the ID field.

        Args:
            table_id (int): The ID of the table where the new row should be
                created.
            row_id (int): The ID of the row which should be updated.
            data (Union[T, dict[str, Any]]): The data of the new row.
            user_field_names (bool): When set to true, the fields in the
                provided data parameter are named according to their field
                names. Otherwise, the unique IDs of the fields will be used.
        """
        params: dict[str, str] = {
            "user_field_names": "true" if user_field_names else "false",
        }

        if not isinstance(data, dict):
            json = data.model_dump(by_alias=True)
        else:
            json = data

        return await self._typed_request(
            "patch",
            _url_join(
                self._url,
                API_PREFIX,
                "database/rows/table",
                str(table_id),
                str(row_id),
            ),
            type(data) if not isinstance(data, dict) else MinimalRow,
            CONTENT_TYPE_JSON,
            params,
            json
        )

    async def delete_row(
        self,
        table_id: int,
        row_id: Union[int, list[int]],
    ):
        """
        Deletes a row with the given ID in the table with the given ID. It's
        also possible to delete more than one row simultaneously. For this, a
        list of IDs can be passed using the row_id parameter.

        Args:
            table_id (int): The ID of the table where the row should be deleted.
            row_id (Union[int, list[int]]): The ID(s) of the row(s) which should
                be deleted.
        """
        if isinstance(row_id, int):
            return await self._request(
                "delete",
                _url_join(
                    self._url,
                    API_PREFIX,
                    "database/rows/table",
                    str(table_id),
                    str(row_id),
                ),
                None,
            )
        return await self._request(
            "post",
            _url_join(
                self._url,
                API_PREFIX,
                "database/rows/table",
                str(table_id),
                "batch-delete",
            ),
            None,
            CONTENT_TYPE_JSON,
            None,
            {"items": row_id},
        )

    @jwt_only
    async def list_database_tables(
        self,
        database_id: int,
    ) -> DatabaseTablesResponse:
        """
        Lists all the tables that are in the database related to the database
        given by it's ID. Please note that this method only works when access is
        through a JWT token, meaning login credentials are used for
        authentication. Additionally, the account being used must have access to
        the database/workspace.

        Args:
            database_id (int): The ID of the database from which one wants to
                retrieve a listing of all tables. 
        """
        return await self._typed_request(
            "get",
            _url_join(
                self._url,
                API_PREFIX,
                "database/tables/database",
                str(database_id),
            ),
            DatabaseTablesResponse,
        )

    @jwt_only
    async def create_database_table(
        self,
        database_id: int,
        name: str,
        client_session_id: Optional[str] = None,
        client_undo_redo_action_group_id: Optional[str] = None,
    ):
        """
        Creates synchronously a new table with the given for the database
        related to the provided database_id parameter.

        Args:
            database_id (int): The ID of the database in which the new table
                should be created.
            name (str): Human readable name for the new table.
            client_session_id (str, optional): An optional UUID that marks
                the action performed by this request as having occurred in a
                particular client session. Then using the undo/redo endpoints
                with the same ClientSessionId header this action can be
                undone/redone.
            client_undo_redo_action_group_id (str, optional): An optional UUID
                that marks the action performed by this request as having
                occurred in a particular action group.Then calling the undo/redo
                endpoint with the same ClientSessionId header, all the actions
                belonging to the same action group can be undone/redone together
                in a single API call.
        """
        headers: dict[str, str] = CONTENT_TYPE_JSON.copy()
        if client_session_id:
            headers["ClientSessionId"] = client_session_id
        if client_undo_redo_action_group_id:
            headers["ClientUndoRedoActionGroupId"] = client_undo_redo_action_group_id
        return await self._typed_request(
            "post",
            _url_join(
                self._url,
                API_PREFIX,
                "database/tables/database",
                str(database_id),
            ),
            DatabaseTableResponse,
            headers=headers,
            json={"name": name},
        )

    async def create_database_table_field(
        self,
        table_id: int,
        field: FieldConfigType,
        client_session_id: Optional[str] = None,
        client_undo_redo_action_group_id: Optional[str] = None,
    ) -> FieldConfig:
        """
        Adds a new field to a table specified by its ID.

        Args:
            table_id (int): The ID of the table to be altered.
            field (FieldConfigType): The config of the field to be added.
            client_session_id (str, optional): An optional UUID that marks
                the action performed by this request as having occurred in a
                particular client session. Then using the undo/redo endpoints
                with the same ClientSessionId header this action can be
                undone/redone.
            client_undo_redo_action_group_id (str, optional): An optional UUID
                that marks the action performed by this request as having
                occurred in a particular action group.Then calling the undo/redo
                endpoint with the same ClientSessionId header, all the actions
                belonging to the same action group can be undone/redone together
                in a single API call.
        """
        headers: dict[str, str] = CONTENT_TYPE_JSON.copy()
        if client_session_id:
            headers["ClientSessionId"] = client_session_id
        if client_undo_redo_action_group_id:
            headers["ClientUndoRedoActionGroupId"] = client_undo_redo_action_group_id
        return await self._typed_request(
            "post",
            _url_join(
                self._url,
                API_PREFIX,
                "database/fields/table",
                str(table_id),
            ),
            FieldConfig,
            headers=headers,
            json=field.model_dump(),
        )

    async def close(self):
        """
        The connection session with the client is terminated. Subsequently, the
        client object cannot be used anymore. It is necessary to explicitly and
        manually close the session only when the client object is directly
        instantiated.
        """
        await self._session.close()

    async def __headers(
        self,
        parts: Optional[dict[str, str]],
    ) -> dict[str, str]:
        if self.__headers_cache is not None:
            if parts is not None:
                rsl = self.__headers_cache.copy()
                rsl.update(parts)
                return rsl
            return self.__headers_cache

        if self._token:
            token = f"Token {self._token}"
        elif self._email and self._password:
            rsp = await self.token_auth(self._email, self._password)
            token = f"JWT {rsp.access_token}"
        else:
            raise RuntimeError("logic error, shouldn't be possible")

        self.__headers_cache = {"Authorization": token}
        return await self.__headers(parts)

    async def _typed_request(
        self,
        method: str,
        url: str,
        result_type: Optional[Type[T]],
        headers: Optional[dict[str, str]] = None,
        params: Optional[dict[str, str]] = None,
        json: Optional[dict[str, Any]] = None,
        use_default_headers: bool = True,
    ) -> T:
        """
        Wrap the _request method for all cases where the return value of the
        request must not be None under any circumstances. If it is, a ValueError
        will be raised.
        """
        rsl = await self._request(
            method,
            url,
            result_type,
            headers,
            params,
            json,
            use_default_headers,
        )
        if not rsl:
            raise ValueError("request result shouldn't be None")
        return rsl

    async def _request(
        self,
        method: str,
        url: str,
        result_type: Optional[Type[T]],
        headers: Optional[dict[str, str]] = None,
        params: Optional[dict[str, str]] = None,
        json: Optional[dict[str, Any]] = None,
        use_default_headers: bool = True,
    ) -> Optional[T]:
        """
        Handles the actual HTTP request.

        Args:
            result_type (Type[T]): The pydantic model which should be used to
                serialize the response field of the response. If set to None
                pydantic will try to serialize the response with built-in types.
                Aka `pydantic.JsonValue`.
        """
        if use_default_headers:
            headers = await self.__headers(headers)
        else:
            headers = {}
        async with self._session.request(
            method,
            url,
            headers=headers,
            params=params,
            json=json,
        ) as rsp:
            if rsp.status == 400:
                err = ErrorResponse.model_validate_json(await rsp.text())
                raise BaserowError(rsp.status, err.error, err.detail)
            if rsp.status == 204:
                return None
            if rsp.status != 200:
                raise UnspecifiedBaserowError(rsp.status, await rsp.text())
            body = await rsp.text()
            if result_type is not None:
                rsl = result_type.model_validate_json(body)
                return rsl
            return None


class GlobalClient(Client):
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
    __token: Optional[str] = None
    __email: Optional[str] = None
    __password: Optional[str] = None

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
            super().__init__(
                self.__url,
                token=self.__token,
                email=self.__email,
                password=self.__password,
            )
            self._is_initialized = True

    @classmethod
    def configure(
        cls,
        url: str,
        token: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Set the URL and token before the first use of the client.

        Args:
            token (str, optional): An access token (referred to as a database token
                in Baserow's documentation) can be generated in the user settings
                within Baserow.
            email (str, optional): Email address of a Baserow user for the JWT
                authentication.
            password (str, optional): Password of a Baserow user for the JWT
                authentication.
        """
        if cls._is_configured:
            raise SingletonAlreadyConfiguredError(
                "singleton client was already configured",
            )
        cls.__url = url
        cls.__token = token
        cls.__email = email
        cls.__password = password
        cls._is_configured = True


global_client = GlobalClient
"""
If the functions of the package should always interact with the same Baserow
instance in an application, the global client can be set. Once configured, this
client will be used for all API calls, unless a different client is specified
for specific functions. To configure this, the client_config method should be
used.

To prevent unpredictable behavior, the package-wide client can only be set once
per runtime.
"""


def client_config(
    url: str,
    token: Optional[str] = None,
    email: Optional[str] = None,
    password: Optional[str] = None,
):
    """
    This method can be used to set up the package-wide client, which will then
    be utilized by default unless a specific client is designated for a given
    method. The client can only be configured once.

    Args:
        token (str, optional): An access token (referred to as a database token
            in Baserow's documentation) can be generated in the user settings
            within Baserow.
        email (str, optional): Email address of a Baserow user for the JWT
            authentication.
        password (str, optional): Password of a Baserow user for the JWT
            authentication.
    """
    try:
        global_client.configure(
            url,
            token=token,
            email=email,
            password=password,
        )
    except SingletonAlreadyConfiguredError:
        raise PackageClientAlreadyDefinedError(global_client()._url, url)
