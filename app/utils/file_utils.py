"""Utility functions for working with files."""

from pathlib import Path


def read_file_to_string(file_path: str) -> str:
    """Read a file and returns its contents as a string.

    Args:
    ----
        file_path (str): The path to the file to be read.

    Returns:
    -------
        str: The contents of the file as a string.
    """
    with Path(file_path).open() as file:
        return file.read()
