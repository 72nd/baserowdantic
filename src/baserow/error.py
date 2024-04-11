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
