import warnings
from contextlib import contextmanager

from .logging import log


class FluoriteException(Exception):
    """Generic AICert exception."""

    def __init__(self, message: str, *args: object) -> None:
        self.message = message
        super().__init__(self.message, *args)


class FluoriteInvalidAttestationFormatException(FluoriteException):
    """Fluorite attestation parsing error (json)."""

    def __init__(self) -> None:
        self.message = f"Invalid attestation format\n"
        super().__init__(self.message)


class FluoriteInvalidAttestationException(FluoriteException):
    """Invalid attestation error."""

    def __init__(self, msg="") -> None:
        self.message = f"Attestation validation failed\n {msg}"
        super().__init__(self.message)


@contextmanager
def log_errors_and_warnings():
    """Context manager that intercepts Fluorite errors and warnings and that logs them.

    Only errors that inherit from FluoriteClientException are caught.
    They are used to display a nice error message before cleanly exiting the program.
    All warnings are caught and logged (and the program continues).

    Example usage:
    ```py
    with log_errors_and_warnings():
        # Potential errors are logged
        # and the program is properly terminated
        function_that_may_fail()
    ```
    """
    try:
        yield None
    except FluoriteException as e:
        log.error(f"{e.message}")
        exit(1)
    finally:
        with warnings.catch_warnings(record=True) as ws:
            for w in ws:
                log.warning(w.message)


class ValidationError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class APIKeyException(Exception):
    """A custom exception class for wrapping API Key verification errors."""

    def __init__(self, key, msg):
        self.key = key
        self.msg = msg

    def __str__(self):
        return f"{self.msg}"


class PredictionException(Exception):
    """A custom exception class for wrapping predictions errors."""

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return f"{self.msg}"
