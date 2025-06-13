import base64
import logging

from google.adk.agents import Agent, SequentialAgent, LoopAgent
from google.adk.agents.callback_context import CallbackContext

from .sub_agents.debugging_agent import debugging_agent
from .sub_agents.code_extraction_agent.agent import code_extraction_agent
from .sub_agents.validation_agent import validation_agent

logger = logging.getLogger(__name__)

# --- Helper function to decode base64 ---
def _decode_b64_str(s: str) -> bytes:
    """Decode a base64 string, stripping data URL prefixes and adding padding."""
    if isinstance(s, str) and s.startswith("data:"):
        parts = s.split(",", 1)
        if len(parts) == 2:
            s = parts[1]
    s = s.strip()
    padding = len(s) % 4
    if padding:
        s += "=" * (4 - padding)
    try:
        return base64.b64decode(s)
    except Exception as e:
        logger.error(f"Base64 decoding failed in callback: {e}", exc_info=True)
        raise  # Re-raise to indicate failure


# --- Callback to save uploaded image(s) to state ---
def _save_uploaded_image_to_state(callback_context: CallbackContext):
    """Extracts image data from incoming message, base64 encodes it, and saves to session state."""
    logger.info("--- Entering _save_uploaded_image_to_state callback ---")
    state = callback_context.state
    user_content = callback_context.user_content

    if not user_content or not user_content.parts:
        logger.info("Callback: No content or parts found in user_content.")
        return

    image_parts_list = []  # NEW: List to store all image parts
    first_image_b64 = None  # To maintain compatibility with single-edit tools

    keys_to_clear = [
        "uploaded_image_b64",
        "uploaded_mask_b64",
        "uploaded_image_parts",
        # Add any other image-specific state keys you might introduce later
    ]
    cleared_keys_log = []

    for key in keys_to_clear:
        # Set to None instead of pop/del
        if state.get(key) is not None:
            state[key] = None
            logger.debug(f"Cleared key '{key}' in session state by setting to None.")
            cleared_keys_log.append(key)
        else:
            logger.debug(f"Key '{key}' not found or already None in session state, skipping.")

    confirmation_msg = f"Image session state cleared. Cleared keys: {cleared_keys_log}" if cleared_keys_log else "Image session state was already clear (or no relevant keys found)."
    logger.info(confirmation_msg)

    # Iterate through parts of the user_content
    for i, part in enumerate(user_content.parts):
        if hasattr(part, 'inline_data') and getattr(part.inline_data, 'mime_type', '').startswith('image/'):
            mime_type = part.inline_data.mime_type
            logger.debug(f"Callback: Found image part {i} with mime_type: {mime_type}")
            part_data_container = part.inline_data
            current_data_bytes = None

            # Try extracting raw bytes first
            raw_bytes = getattr(part_data_container, 'data', None)
            if raw_bytes and isinstance(raw_bytes, (bytes, bytearray)):
                current_data_bytes = raw_bytes
                logger.debug(
                    f"Callback: Extracted raw bytes ({len(current_data_bytes)}) from inline_data for part {i}.")
            else:
                # Fallback to base64 string
                b64_data = getattr(part_data_container, 'b64_json', None)
                if b64_data and isinstance(b64_data, str):
                    logger.debug(f"Callback: Found base64 string in inline_data for part {i}. Decoding...")
                    try:
                        current_data_bytes = _decode_b64_str(b64_data)
                        logger.debug(f"Callback: Decoded base64 part {i}. Length: {len(current_data_bytes)}")
                    except Exception as e:
                        logger.error(f"Callback: Failed to decode base64 from part {i}: {e}")
                        continue  # Skip this part if decoding fails
                else:
                    logger.warning(f"Callback: Image part {i} found but no suitable data/b64_json.")
                    continue

            # If data was successfully obtained, process and add to list
            if current_data_bytes:
                try:
                    # Re-encode to ensure clean base64 for state
                    current_b64_str = base64.b64encode(current_data_bytes).decode('utf-8')
                    image_part_info = {"b64": current_b64_str, "mime_type": mime_type}
                    image_parts_list.append(image_part_info)
                    logger.debug(
                        f"Callback: Added image part {i} info (mime: {mime_type}, b64 len: {len(current_b64_str)}) to list.")

                    # Save the first image separately for compatibility
                    if first_image_b64 is None:
                        first_image_b64 = current_b64_str
                        logger.debug(f"Callback: Storing part {i} as the first image for single-edit compatibility.")

                except Exception as e:
                    logger.error(f"Callback: Error processing/encoding image part {i}: {e}")
                    continue

    # Save the collected image parts list and the first image to state
    if image_parts_list:
        state["uploaded_image_parts"] = image_parts_list
        logger.info(f"Callback: Saved list of {len(image_parts_list)} image parts to state['uploaded_image_parts'].")
    else:
        logger.info("Callback: No valid image parts found to save to the list.")

    if first_image_b64:
        state["uploaded_image_b64"] = first_image_b64
        logger.info(
            f"Callback: Saved first image base64 string (len: {len(first_image_b64)}) to state['uploaded_image_b64'].")
    else:
        # If no images were found at all, ensure the key is removed
        if "uploaded_image_b64" in state:
            del state["uploaded_image_b64"]
        logger.info("Callback: No first image found, ensuring state['uploaded_image_b64'] is clear.")
    logger.info("--- Exiting _save_uploaded_image_to_state callback ---")


code_refinement_loop = LoopAgent(
    name="CodeRefinementLoop",
    max_iterations=10,
    sub_agents=[
        validation_agent,
        debugging_agent,
    ],
    description="Iteratively reviews and refines a the code until it can generate a valid tap file",
)

root_agent = SequentialAgent(
    name="TapCreationPipeline",
    sub_agents=[
        code_extraction_agent,
        code_refinement_loop,
    ],
    before_agent_callback=_save_uploaded_image_to_state
)
