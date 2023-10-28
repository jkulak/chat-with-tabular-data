"""Utility functions for logging user interactions."""

import logging
import os

from dotenv import load_dotenv


load_dotenv()

BIGQUERY_LOG_EXPORT = os.getenv("BIGQUERY_LOG_EXPORT")


def logging_user_interaction(
    message: str,
    input_characters_count: int,
    output_characters_count: int,
) -> None:
    """Log user interaction to BigQuery, if enabled.

    Args:
    ----
        message (str): The message to log.
        input_characters_count (int): The number of characters in the input.
        output_characters_count (int): The number of characters in the output.

    Returns:
    -------
        None
    """
    if BIGQUERY_LOG_EXPORT is None:
        logging.info(
            message,
            "\ninput_characters_count:",
            input_characters_count,
            "\noutput_characters_count:",
            output_characters_count,
        )
