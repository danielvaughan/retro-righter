"""
Tools for tap creation agent

This module provides tools for creating TAP files.
"""

import subprocess
import tempfile
import os
import stat

from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import ToolContext


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
    # Create a temporary file for the output TAP file.
    # We use delete=False because we want to return its path to the caller.
    # The caller is responsible for deleting this file.
    tap_file_handle, tap_file_path = tempfile.mkstemp(suffix='.tap')
    os.close(tap_file_handle)  # We just need the path, bas2tap will write to it.

    # Create a temporary file for the BASIC code.
    with tempfile.NamedTemporaryFile(mode='w', suffix='.bas', delete=True) as bas_file:
        bas_file.write(current_code)  # Write the Spectrum BASIC code to the file (if available)
        bas_file.flush()  # Ensure data is written to disk before bas2tap is called.

        command = ['bas2tap', bas_file.name, tap_file_path]

        try:
            subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True
            )
            add_read_permission(tap_file_path)
        except FileNotFoundError as e:
            # Clean up the tap file if bas2tap wasn't found
            os.remove(tap_file_path)
            raise RuntimeError(
                "`bas2tap` command not found. "
                "Please ensure it is installed and in your system's PATH."
            ) from e
        except subprocess.CalledProcessError as e:
            # Clean up the tap file on error
            os.remove(tap_file_path)
            error_message = (
                f"bas2tap failed with exit code {e.returncode}.\n"
                f"Stderr: {e.stderr.strip()}"
            )
            raise RuntimeError(error_message) from e

    return {
        "tap_file_path": tap_file_path
    }

def add_read_permission(filepath):
    """
    Adds read permission for the owner, group, and others to a file.

    Args:
        filepath (str): The path to the file.
    """
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' does not exist.")
        return

    try:
        # Get the current file permissions
        current_permissions = os.stat(filepath).st_mode

        # Define the read permissions for owner, group, and others
        read_permissions = stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH

        # Combine the current permissions with the new read permissions
        # We use a bitwise OR to add the read permissions without removing existing ones
        new_permissions = current_permissions | read_permissions

        # Apply the new permissions
        os.chmod(filepath, new_permissions)
        print(f"Read permission added to '{filepath}'.")

    except OSError as e:
        print(f"Error changing permissions for '{filepath}': {e}")