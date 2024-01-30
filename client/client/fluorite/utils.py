import subprocess
import textwrap

from .logging import log


def run_command(*args):
    log.info(f"run: {' '.join(args)}")
    try:
        return subprocess.run(args, text=True, capture_output=True, check=True).stdout
    except subprocess.CalledProcessError as e:
        command = " ".join(args)
        indented_stderr = textwrap.indent(e.stderr, prefix="   ")
        indented_stdout = textwrap.indent(e.stdout, prefix="   ")
        error_message = (
            f"Command '{command}' failed.\n"
            f"Stdout:\n{indented_stdout}"
            f"Stderr:\n{indented_stderr}"
        )

        raise RuntimeError(error_message) from e
