"""
Tools for Spectrum basic validation agent

This module provides tools for validating Spectrum BASIC code.
"""

import subprocess
import tempfile
import os
import logging
from typing import Dict, Any

from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)

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
    logger.info("Validating Spectrum BASIC code.")
    temp_bas_file = None
    temp_tap_file = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bas', delete=False, encoding='utf-8') as f:
            temp_bas_file = f.name
            logger.debug(f"Created temporary BASIC file: {temp_bas_file}")
            f.write(current_code)

        with tempfile.NamedTemporaryFile(suffix='.tap', delete=False) as f:
            temp_tap_file = f.name
            logger.debug(f"Created temporary TAP file: {temp_tap_file}")

        command = ['bas2tap', temp_bas_file, temp_tap_file]
        logger.info(f"Executing command: {' '.join(command)}")

        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False  # We'll check the return code manually
        )

        output = ""
        if process.stdout:
            logger.debug(f"bas2tap stdout:\n{process.stdout}")
            output += f"--- stdout ---\n{process.stdout}\n"
        if process.stderr:
            logger.warning(f"bas2tap stderr:\n{process.stderr}") # Using warning for stderr
            output += f"--- stderr ---\n{process.stderr}\n"

        if process.returncode != 0:
            logger.error(f"bas2tap exited with a non-zero status: {process.returncode}")
            output += f"bas2tap exited with a non-zero status: {process.returncode}"
        else:
            logger.info("bas2tap executed successfully.")

        final_output = output if output else "bas2tap executed successfully with no output."
        logger.debug(f"Validation result: {final_output}")
        return final_output

    finally:
        if temp_bas_file and os.path.exists(temp_bas_file):
            os.remove(temp_bas_file)
            logger.debug(f"Removed temporary BASIC file: {temp_bas_file}")
        if temp_tap_file and os.path.exists(temp_tap_file):
            os.remove(temp_tap_file)
            logger.debug(f"Removed temporary TAP file: {temp_tap_file}")


def exit_loop(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Call this function ONLY when code validation has completed successfully,
    signaling the iterative process should end.

    Args:
        tool_context: Context for tool execution

    Returns:
        Empty dictionary
    """
    logger.info("----------- EXIT LOOP TRIGGERED -----------")
    logger.info("Code validation completed successfully")
    logger.info("Loop will exit now")
    logger.info("------------------------------------------")

    tool_context.actions.escalate = True
    return {}
