"""
Tools for summary agent

"""
from google.adk.agents.callback_context import CallbackContext  # Or ToolContext


async def return_tap(context: CallbackContext):
    """Loads the tapfile."""
    filename = "zxspectrum.tap"
    try:
        # Load the latest version
        tap_artifact = await context.load_artifact(filename=filename)

        if tap_artifact and tap_artifact.inline_data:
            print(f"Successfully tap_artifact latest Python artifact '{filename}'.")
            print(f"MIME Type: {tap_artifact.inline_data.mime_type}")
            # Process the report_artifact.inline_data.data (bytes)
            pdf_bytes = tap_artifact.inline_data.data
            print(f"Report size: {len(pdf_bytes)} bytes.")
            # ... further processing ...
        else:
            print(f"Python artifact '{filename}' not found.")
    except ValueError as e:
        print(f"Error loading Python artifact: {e}. Is ArtifactService configured?")
    except Exception as e:
        # Handle potential storage errors
        print(f"An unexpected error occurred during Python artifact load: {e}")
