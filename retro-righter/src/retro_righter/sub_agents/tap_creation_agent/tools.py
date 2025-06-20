"""
Tools for tap creation agent

This module provides tools for creating TAP files.
"""

import subprocess
import tempfile
import os
import logging

from google.cloud import storage

logger = logging.getLogger(__name__)

def create_tap(current_code: str) -> dict[str, str]:
    """Creates a TAP file from Spectrum BASIC code.

    This function takes a string of Spectrum BASIC code, writes it to a temporary
    file with a .bas extension, and then uses the `bas2tap` command-line tool
    to convert it into a TAP file. The path to the resulting TAP file is returned.

    The caller is responsible for deleting the created TAP file when it's no
    longer needed.

    Args:
        current_code: The Spectrum BASIC code as a string.

    Returns:
        A dictionary with the key 'tap_file_path' holding the absolute path
        to the created TAP file.

    Raises:
        RuntimeError: If `bas2tap` is not found or if it fails to execute.
    """
    logger.info("Attempting to create TAP file.")
    # Create a temporary file for the output TAP file.
    # We use delete=False because we want to return its path to the caller.
    # The caller is responsible for deleting this file.
    tap_file_handle, tap_file_path = tempfile.mkstemp(suffix='.tap')
    os.close(tap_file_handle)  # We just need the path, bas2tap will write to it.
    logger.debug(f"Temporary TAP file path created: {tap_file_path}")

    with tempfile.NamedTemporaryFile(mode='w', suffix='.bas', delete=True) as bas_file:
        logger.debug(f"Writing BASIC code to temporary file: {bas_file.name}")
        bas_file.write(current_code)
        bas_file.flush()  # Ensure data is written to disk before bas2tap is called.

        command = ['bas2tap', bas_file.name, tap_file_path]
        logger.info(f"Executing command: {' '.join(command)}")

        try:
            subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"Successfully created TAP file: {tap_file_path}")
        except FileNotFoundError as e:
            logger.error("`bas2tap` command not found. Ensure it's installed and in PATH.", exc_info=True)
            os.remove(tap_file_path)
            logger.debug(f"Cleaned up temporary TAP file due to FileNotFoundError: {tap_file_path}")
            raise RuntimeError(
                "`bas2tap` command not found. "
                "Please ensure it is installed and in your system's PATH."
            ) from e
        except subprocess.CalledProcessError as e:
            logger.error(f"bas2tap failed with exit code {e.returncode}. Stderr: {e.stderr.strip()}", exc_info=True)
            os.remove(tap_file_path)
            logger.debug(f"Cleaned up temporary TAP file due to CalledProcessError: {tap_file_path}")
            error_message = (
                f"bas2tap failed with exit code {e.returncode}.\n"
                f"Stderr: {e.stderr.strip()}"
            )
            raise RuntimeError(error_message) from e

    return {
        "tap_file_path": tap_file_path
    }