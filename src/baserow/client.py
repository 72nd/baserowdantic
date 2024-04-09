"""
This module handles the interaction with Baserow's API.
"""

from typing import Optional
import aiohttp

from baserow.error import PackageClientAlreadyDefinedError, SingletonAlreadyConfiguredError


def url_join(*parts: str) -> str:
    """Joins given strings into a URL."""
    rsl = [part.strip("/") for part in parts]
    return "/".join(rsl)


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
        self._token: str = token
        self._session: aiohttp.ClientSession = aiohttp.ClientSession()

    def test(self):
        return self._url


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
