"""
This module contains the custom exceptions of the package.
"""


class SingletonAlreadyConfiguredError(Exception):
    """
    Thrown when an attempt is made to call the configuration method on an already configured singleton again.
    """


class PackageClientAlreadyDefinedError(Exception):
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

    def __str__(self):
        return f"attempted to configure the package-wide client with the URL '{self.new_url}', even though it was already configured with the URL '{self.old_url}'"


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

    def __str__(self):
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

    def __str__(self):
        return f"Baserow returned an error with status code {self.status_code}: {self.body}"
