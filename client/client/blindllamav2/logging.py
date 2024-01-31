import logging
import os

from rich.logging import RichHandler

LOG_LEVEL = os.getenv("BLINDLLAMA_LOG_LEVEL")
if LOG_LEVEL is None or LOG_LEVEL not in [
    "CRITICAL",
    "ERROR",
    "WARNING",
    "INFO",
    "DEBUG",
]:
    LOG_LEVEL = "WARNING"


logging.basicConfig(
    level=LOG_LEVEL,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)

log = logging.getLogger()
