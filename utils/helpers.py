"""Utility helpers for the dashboard project."""

import re


def normalize_error_message(message):
    """Return a generic error message without variable identifiers.

    Many error messages include dynamic information such as user IDs or
    other numbers. To group errors effectively we strip any digits and
    collapse extra whitespace so that messages differing only by those
    identifiers map to the same generic text.

    Parameters
    ----------
    message: str or any
        Original error message. Non-string values are returned as-is.

    Returns
    -------
    str or any
        Normalized error message with digits removed and consecutive
        whitespace collapsed. Non-string inputs are returned unchanged.
    """

    if not isinstance(message, str):
        return message

    # Remove any sequence of digits and collapse multiple spaces
    normalized = re.sub(r"\d+", "", message)
    normalized = " ".join(normalized.split())
    return normalized

