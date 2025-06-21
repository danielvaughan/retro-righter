import base64
import logging
import os
import datetime
from google.cloud import storage

from google.adk.agents.callback_context import CallbackContext

logger = logging.getLogger(__name__)


# --- Helper function to decode base64 ---
def _decode_b64_str(s: str) -> bytes:
    """Decode a base64 string, stripping data URL prefixes, and adding padding."""
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
        raise


# --- Callback to save uploaded image(s) to state ---
def _save_uploaded_image_to_state(callback_context: CallbackContext):
    """Extracts image data from an incoming request, base64 encodes it, and saves to session state."""
    logger.info("--- Entering _save_uploaded_image_to_state callback ---")
    state = callback_context.state
    user_content = callback_context.user_content

    if not user_content or not user_content.parts:
        logger.info("Callback: No content or parts found in user_content.")
        return

    # Clears image session state
    image_parts_list = []
    first_image_b64 = None

    keys_to_clear = [
        "uploaded_image_b64",
        "uploaded_mask_b64",
        "uploaded_image_parts",
    ]
    cleared_keys_log = []

    for key in keys_to_clear:
        if state.get(key) is not None:
            state[key] = None
            logger.debug(f"Cleared key '{key}' in session state by setting to None.")
            cleared_keys_log.append(key)
        else:
            logger.debug(
                f"Key '{key}' not found or already None in session state, skipping."
            )

    confirmation_msg = (
        f"Image session state cleared. Cleared keys: {cleared_keys_log}"
        if cleared_keys_log
        else "Image session state was already clear (or no relevant keys found)."
    )
    logger.info(confirmation_msg)

    # Iterate through parts of the user_content
    for i, part in enumerate(user_content.parts):
        if hasattr(part, "inline_data") and getattr(
            part.inline_data, "mime_type", ""
        ).startswith("image/"):
            mime_type = part.inline_data.mime_type
            logger.debug(f"Callback: Found image part {i} with mime_type: {mime_type}")
            part_data_container = part.inline_data
            current_data_bytes = None

            # Try extracting raw bytes first
            raw_bytes = getattr(part_data_container, "data", None)
            if raw_bytes and isinstance(raw_bytes, (bytes, bytearray)):
                current_data_bytes = raw_bytes
                logger.debug(
                    f"Callback: Extracted raw bytes ({len(current_data_bytes)}) from inline_data for part {i}."
                )
            else:
                # Fallback to base64 string
                b64_data = getattr(part_data_container, "b64_json", None)
                if b64_data and isinstance(b64_data, str):
                    logger.debug(
                        f"Callback: Found base64 string in inline_data for part {i}. Decoding..."
                    )
                    try:
                        current_data_bytes = _decode_b64_str(b64_data)
                        logger.debug(
                            f"Callback: Decoded base64 part {i}. Length: {len(current_data_bytes)}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Callback: Failed to decode base64 from part {i}: {e}"
                        )
                        continue  # Skip this part if decoding fails
                else:
                    logger.warning(
                        f"Callback: Image part {i} found but no suitable data/b64_json."
                    )
                    continue

            # If data was successfully obtained, process and add to list
            if current_data_bytes:
                try:
                    # Re-encode to ensure clean base64 for state
                    current_b64_str = base64.b64encode(current_data_bytes).decode(
                        "utf-8"
                    )
                    image_part_info = {"b64": current_b64_str, "mime_type": mime_type}
                    image_parts_list.append(image_part_info)
                    logger.debug(
                        f"Callback: Added image part {i} info (mime: {mime_type}, b64 len: {len(current_b64_str)}) to list."
                    )

                    # Save the first image separately for compatibility
                    if first_image_b64 is None:
                        first_image_b64 = current_b64_str
                        logger.debug(
                            f"Callback: Storing part {i} as the first image for single-edit compatibility."
                        )

                except Exception as e:
                    logger.error(
                        f"Callback: Error processing/encoding image part {i}: {e}"
                    )
                    continue

    # Save the collected image parts list and the first image to state
    if image_parts_list:
        state["uploaded_image_parts"] = image_parts_list
        logger.info(
            f"Callback: Saved list of {len(image_parts_list)} image parts to state['uploaded_image_parts']."
        )
    else:
        logger.info("Callback: No valid image parts found to save to the list.")

    if first_image_b64:
        state["uploaded_image_b64"] = first_image_b64
        logger.info(
            f"Callback: Saved first image base64 string (len: {len(first_image_b64)}) to state['uploaded_image_b64']."
        )
    else:
        # If no images were found at all, ensure the key is removed
        if "uploaded_image_b64" in state:
            del state["uploaded_image_b64"]
        logger.info(
            "Callback: No first image found, ensuring state['uploaded_image_b64'] is clear."
        )
    logger.info("--- Exiting _save_uploaded_image_to_state callback ---")


def _upload_to_gcs_and_get_url(callback_context: CallbackContext):
    """Uploads a file to GCS and generates a temporary signed URL.

    The bucket name is read from the 'GCS_BUCKET_NAME' environment variable.
    The generated URL is valid for 1 hour.

    Args:
        callback_context: The context containing state with 'tap_file_path'.

    Raises:
        ValueError: If the GCS_BUCKET_NAME environment variable is not set.
        FileNotFoundError: If the file at tap_file_path does not exist.
        google.api_core.exceptions.GoogleAPICallError: For GCS API errors.
    """
    state = callback_context.state
    tap_file_path = state.get("tap_file_path")
    logger.info(f"Attempting to upload file '{tap_file_path}' to GCS.")

    bucket_name = os.environ.get("GCS_BUCKET_NAME")
    if not bucket_name:
        logger.error("GCS_BUCKET_NAME environment variable not set.")
        raise ValueError("GCS_BUCKET_NAME environment variable is not set.")

    if not tap_file_path or not os.path.exists(tap_file_path):
        logger.error(f"File not found at path: {tap_file_path}")
        raise FileNotFoundError(f"The specified file does not exist: {tap_file_path}")

    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)

        # Use the filename as the destination blob name
        blob_name = os.path.basename(tap_file_path)
        blob = bucket.blob(blob_name)

        logger.debug(f"Uploading '{blob_name}' to bucket '{bucket_name}'...")
        blob.upload_from_filename(tap_file_path)
        logger.info(
            f"Successfully uploaded '{blob_name}' to GCS bucket '{bucket_name}'."
        )

        try:
            # Attempt to generate a signed URL (valid for 1 hour)
            expiration_time = datetime.timedelta(hours=1)
            signed_url = blob.generate_signed_url(
                version="v4",
                expiration=expiration_time,
                method="GET",
            )
            logger.info(
                f"Generated signed URL for '{blob_name}', valid for {expiration_time}."
            )
            state["tap_public_url"] = signed_url
        except Exception as e_signed_url:
            logger.warning(
                f"Failed to generate signed URL for '{blob_name}': {e_signed_url}. "
                f"Attempting to make the file public and use its public URL instead."
            )
            try:
                blob.make_public()
                public_url = blob.public_url
                logger.info(
                    f"Successfully made '{blob_name}' public. Public URL: {public_url}"
                )
                state["tap_public_url"] = public_url
            except Exception as e_make_public:
                logger.error(
                    f"Failed to make '{blob_name}' public or get its public URL for {tap_file_path}: {e_make_public}",
                    exc_info=True,
                )
                # Re-raise the error encountered during the fallback attempt.
                # This will be caught by the outer 'except Exception as e' below.
                raise e_make_public
    except Exception as e:
        logger.error(
            f"Failed to process file '{tap_file_path}' with GCS: {e}", exc_info=True
        )
        raise

    finally:
        # Delete the local file after successful upload
        if tap_file_path and os.path.exists(tap_file_path):
            os.remove(tap_file_path)
            logger.debug(f"Deleted local file '{tap_file_path}' after upload attempt.")
