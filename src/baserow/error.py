"""
This module contains the custom exceptions of the package.
"""


from pydantic_core.core_schema import model_field


class PackageClientNotConfiguredError(Exception):
    """
    Thrown when the PackageClient is intended to be used but has not been
    configured yet.
    """

    def __str__(self) -> str:
        return "the package-wide GlobalClient is not defined; it must first be configured with configure()"


class PackageClientAlreadyConfiguredError(Exception):
    """
    This exception is thrown if the package user attempts to call the
    baserow.config_client() method multiple times. To prevent unpredictable
    behavior, the package-wide client can only be set once per runtime.

    Args:
        old_url (str): The URL that has already been set for the package-wide
            client.
        new_url (str): The URL that the user is attempting to set anew.
    """

    def __init__(self, old_url: str, new_url: str):
        self.old_url = old_url
        self.new_url = new_url

    def __str__(self) -> str:
        return f"attempted to configure the package-wide client with the URL '{self.new_url}', even though it was already configured with the URL '{self.old_url}'"


class NoClientAvailableError(Exception):
    """
    Thrown when a Table instance is not given a client, and the GlobalClient of
    the package is not configured. This would implicitly raise a
    PackageClientNotConfiguredError, but this behavior is not transparent to the
    package user and could be confusing. Therefore, this exception was created
    for this case (when using the ORM-like abstraction).

    Args:
        table_name (str): Name of the table.
    """

    def __init__(self, table_name: str):
        self.table_name = table_name

    def __str__(self) -> str:
        return f"there is no API client available for the table '{self.table_name}'. Either configure the package-wide GlobalClient or use the client property of your Table model"


class JWTAuthRequiredError(Exception):
    """
    Thrown when an operation with the API is only possible with user credentials
    authentication.

    Args:
        name (str): Name or short description of the operation.
    """

    def __init__(self, name: str):
        self.name = name

    def __str__(self) -> str:
        return f"the {self.name} method only works with a JWT (username and password) authentication"


class BaserowError(Exception):
    """
    Exception thrown when an HTTP request to the Baserow REST API returns an
    error.

    Args:
        status_code (int): HTTP status code.
        name (str): Name/title of the error.
        detail (str): Additional detail.
    """

    def __init__(self, status_code: int, name: str, detail: str):
        self.status_code = status_code
        self.name = name
        self.detail = detail

    def __str__(self) -> str:
        return f"Baserow returned an {self.name} error with status code {self.status_code}: {self.detail}"


class UnspecifiedBaserowError(Exception):
    """
    Thrown when the Baserow HTTP call returns a non-success state but not with
    status code 400.

    Args:
        status_code (int): HTTP status code.
        body (str): String representation of the body.
    """

    def __init__(self, status_code: int, body: str):
        self.status_code = status_code
        self.body = body

    def __str__(self) -> str:
        return f"Baserow returned an error with status code {self.status_code}: {self.body}"


class InvalidTableConfiguration(Exception):
    """
    Raised when a Table model is not implemented correctly.

    Args:
        model_name (str): Name of the model.
        reason (str): Reason for the exception.
    """

    def __init__(self, model_name: str, reason: str):
        self.model_name = model_name
        self.reason = reason

    def __str__(self) -> str:
        return f"the configuration of the '{self.model_name}' table model is incorrect, {self.reason}"
