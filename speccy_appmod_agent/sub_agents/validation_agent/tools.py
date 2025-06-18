"""
Tools for Spectrum basic validation agent

This module provides tools for validating Spectrum BASIC code.
"""

import subprocess
import tempfile
import os
from typing import Dict, Any

from google.adk.tools import ToolContext

def validate_spectrum_code(current_code: str) -> str:
    """
    Takes Spectrum BASIC code as a string, writes it to a temporary file,
    runs it through bas2tap to validate the code and returns the output from the command.

    Args:
        current_code: A string containing the Spectrum BASIC code.

    Returns:
        The captured stdout and stderr from the bas2tap command as a string.

    Raises:
        FileNotFoundError: If the 'bas2tap' command is not found.
    """
    temp_bas_file = None
    temp_tap_file = None
    try:
        # Create a temporary file for the BASIC code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bas', delete=False, encoding='utf-8') as f:
            temp_bas_file = f.name
            f.write(current_code)

        # Create a temporary file for the TAP output
        with tempfile.NamedTemporaryFile(suffix='.tap', delete=False) as f:
            temp_tap_file = f.name

        # Construct the command to run bas2tap
        command = ['bas2tap', temp_bas_file, temp_tap_file]

        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False  # We'll check the return code manually
        )

        output = ""
        if process.stdout:
            output += f"--- stdout ---\n{process.stdout}\n"
        if process.stderr:
            output += f"--- stderr ---\n{process.stderr}\n"

        if process.returncode != 0:
            output += f"bas2tap exited with a non-zero status: {process.returncode}"

        return output if output else "bas2tap executed successfully with no output."

    finally:
        # Clean up the temporary files
        if temp_bas_file and os.path.exists(temp_bas_file):
            os.remove(temp_bas_file)
        if temp_tap_file and os.path.exists(temp_tap_file):
            os.remove(temp_tap_file)


def exit_loop(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Call this function ONLY when code validation has completed successfully,
    signaling the iterative process should end.

    Args:
        tool_context: Context for tool execution

    Returns:
        Empty dictionary
    """
    print("\n----------- EXIT LOOP TRIGGERED -----------")
    print("Code validation completed successfully")
    print("Loop will exit now")
    print("------------------------------------------\n")

    tool_context.actions.escalate = True
    return {}
