import unittest
from unittest.mock import MagicMock, patch, call
import base64

from retro_righter.tools import _save_uploaded_image_to_state, _decode_b64_str # _decode_b64_str is used by the SUT

# Helper to create a dummy image bytes
def create_dummy_image_bytes(content: str = "dummy_image_content") -> bytes:
    return content.encode('utf-8')

# Helper to create a base64 encoded string from bytes
def encode_to_b64_string(data: bytes) -> str:
    return base64.b64encode(data).decode('utf-8')

class TestSaveUploadedImageToState(unittest.TestCase):

    def _create_mock_callback_context(self, parts_data=None):
        callback_context = MagicMock()
        callback_context.state = {}  # Simulate the state dictionary
        callback_context.user_content = MagicMock()

        if parts_data is None:
            callback_context.user_content.parts = None
        else:
            mock_parts = []
            for part_info in parts_data:
                mock_part = MagicMock()
                if 'mime_type' in part_info:
                    mock_part.inline_data = MagicMock()
                    mock_part.inline_data.mime_type = part_info["mime_type"]
                    mock_part.inline_data.data = part_info.get("raw_data")
                    mock_part.inline_data.b64_json = part_info.get("b64_json")
                else:
                    if part_info.get("no_inline_data", False):
                        del mock_part.inline_data
                    else:
                        mock_part.inline_data = MagicMock(spec=['mime_type', 'data', 'b64_json'])
                        mock_part.inline_data.mime_type = None
                mock_parts.append(mock_part)
            callback_context.user_content.parts = mock_parts
        return callback_context

    @patch('retro_righter.tools.logger')
    def test_no_user_content(self, mock_logger):
        callback_context = self._create_mock_callback_context()
        callback_context.user_content = None
        _save_uploaded_image_to_state(callback_context)
        self.assertNotIn("uploaded_image_b64", callback_context.state)
        self.assertNotIn("uploaded_image_parts", callback_context.state)
        mock_logger.info.assert_any_call("Callback: No content or parts found in user_content.")

    @patch('retro_righter.tools.logger')
    def test_user_content_parts_is_none(self, mock_logger):
        callback_context = self._create_mock_callback_context(parts_data=None)
        _save_uploaded_image_to_state(callback_context)
        self.assertNotIn("uploaded_image_b64", callback_context.state)
        self.assertNotIn("uploaded_image_parts", callback_context.state)
        mock_logger.info.assert_any_call("Callback: No content or parts found in user_content.")

    @patch('retro_righter.tools.logger')
    def test_user_content_parts_is_empty(self, mock_logger):
        callback_context = self._create_mock_callback_context(parts_data=[])
        _save_uploaded_image_to_state(callback_context)
        self.assertNotIn("uploaded_image_b64", callback_context.state)
        self.assertNotIn("uploaded_image_parts", callback_context.state)
        mock_logger.info.assert_any_call("Callback: No content or parts found in user_content.")

    @patch('retro_righter.tools.logger')
    def test_no_image_parts(self, mock_logger):
        parts_data = [{"mime_type": "text/plain"}]
        callback_context = self._create_mock_callback_context(parts_data)
        _save_uploaded_image_to_state(callback_context)
        self.assertNotIn("uploaded_image_b64", callback_context.state)
        self.assertTrue(callback_context.state.get("uploaded_image_parts") is None or \
                        len(callback_context.state.get("uploaded_image_parts")) == 0)
        mock_logger.info.assert_any_call("Callback: No valid image parts found to save to the list.")

    @patch('retro_righter.tools.logger')
    def test_single_image_raw_bytes(self, mock_logger):
        dummy_bytes = create_dummy_image_bytes("raw_image_1")
        expected_b64 = encode_to_b64_string(dummy_bytes)
        parts_data = [{"mime_type": "image/jpeg", "raw_data": dummy_bytes}]
        callback_context = self._create_mock_callback_context(parts_data)
        _save_uploaded_image_to_state(callback_context)
        self.assertEqual(callback_context.state.get("uploaded_image_b64"), expected_b64)
        self.assertIsNotNone(callback_context.state.get("uploaded_image_parts"))
        self.assertEqual(len(callback_context.state["uploaded_image_parts"]), 1)
        self.assertEqual(callback_context.state["uploaded_image_parts"][0]["b64"], expected_b64)
        self.assertEqual(callback_context.state["uploaded_image_parts"][0]["mime_type"], "image/jpeg")
        mock_logger.info.assert_any_call(f"Callback: Saved first image base64 string (len: {len(expected_b64)}) to state['uploaded_image_b64'].")
        mock_logger.info.assert_any_call("Callback: Saved list of 1 image parts to state['uploaded_image_parts'].")

    @patch('retro_righter.tools.logger')
    def test_single_image_b64_json(self, mock_logger):
        original_bytes = create_dummy_image_bytes("b64_image_1_needs_padding")
        b64_str_input = base64.b64encode(original_bytes).decode('utf-8').rstrip('=')
        parts_data = [{"mime_type": "image/png", "b64_json": b64_str_input}]
        callback_context = self._create_mock_callback_context(parts_data)
        _save_uploaded_image_to_state(callback_context)
        expected_final_b64 = encode_to_b64_string(original_bytes)
        self.assertEqual(callback_context.state.get("uploaded_image_b64"), expected_final_b64)
        self.assertIsNotNone(callback_context.state.get("uploaded_image_parts"))
        self.assertEqual(len(callback_context.state["uploaded_image_parts"]), 1)
        self.assertEqual(callback_context.state["uploaded_image_parts"][0]["b64"], expected_final_b64)
        self.assertEqual(callback_context.state["uploaded_image_parts"][0]["mime_type"], "image/png")

    @patch('retro_righter.tools.logger')
    @patch('retro_righter.tools._decode_b64_str')
    def test_single_image_b64_json_with_data_url_prefix(self, mock_decode_b64_str, mock_logger):
        dummy_bytes = create_dummy_image_bytes("data_url_image")
        mock_decode_b64_str.return_value = dummy_bytes
        b64_str_with_prefix = "data:image/gif;base64," + encode_to_b64_string(dummy_bytes)
        parts_data = [{"mime_type": "image/gif", "b64_json": b64_str_with_prefix}]
        callback_context = self._create_mock_callback_context(parts_data)
        _save_uploaded_image_to_state(callback_context)
        mock_decode_b64_str.assert_called_once_with(b64_str_with_prefix)
        expected_final_b64 = encode_to_b64_string(dummy_bytes)
        self.assertEqual(callback_context.state.get("uploaded_image_b64"), expected_final_b64)
        self.assertIsNotNone(callback_context.state.get("uploaded_image_parts"))
        self.assertEqual(len(callback_context.state["uploaded_image_parts"]), 1)
        self.assertEqual(callback_context.state["uploaded_image_parts"][0]["b64"], expected_final_b64)
        self.assertEqual(callback_context.state["uploaded_image_parts"][0]["mime_type"], "image/gif")

    @patch('retro_righter.tools.logger')
    def test_multiple_images(self, mock_logger):
        img1_bytes = create_dummy_image_bytes("multi_img_1_raw")
        img1_b64_expected = encode_to_b64_string(img1_bytes)
        img2_original_bytes = create_dummy_image_bytes("multi_img_2_b64")
        img2_b64_input = encode_to_b64_string(img2_original_bytes)
        img2_b64_expected = encode_to_b64_string(img2_original_bytes)
        parts_data = [
            {"mime_type": "image/jpeg", "raw_data": img1_bytes},
            {"mime_type": "image/png", "b64_json": img2_b64_input}
        ]
        callback_context = self._create_mock_callback_context(parts_data)
        _save_uploaded_image_to_state(callback_context)
        self.assertEqual(callback_context.state.get("uploaded_image_b64"), img1_b64_expected)
        self.assertIsNotNone(callback_context.state.get("uploaded_image_parts"))
        self.assertEqual(len(callback_context.state["uploaded_image_parts"]), 2)
        self.assertEqual(callback_context.state["uploaded_image_parts"][0]["b64"], img1_b64_expected)
        self.assertEqual(callback_context.state["uploaded_image_parts"][0]["mime_type"], "image/jpeg")
        self.assertEqual(callback_context.state["uploaded_image_parts"][1]["b64"], img2_b64_expected)
        self.assertEqual(callback_context.state["uploaded_image_parts"][1]["mime_type"], "image/png")
        mock_logger.info.assert_any_call("Callback: Saved list of 2 image parts to state['uploaded_image_parts'].")

    @patch('retro_righter.tools.logger')
    def test_image_part_missing_data_and_b64_json(self, mock_logger):
        parts_data = [{"mime_type": "image/webp"}]
        callback_context = self._create_mock_callback_context(parts_data)
        _save_uploaded_image_to_state(callback_context)
        self.assertIsNone(callback_context.state.get("uploaded_image_b64"))
        self.assertTrue(callback_context.state.get("uploaded_image_parts") is None or \
                        len(callback_context.state.get("uploaded_image_parts")) == 0)
        mock_logger.warning.assert_any_call("Callback: Image part 0 found but no suitable data/b64_json.")
        mock_logger.info.assert_any_call("Callback: No valid image parts found to save to the list.")

    @patch('retro_righter.tools.logger')
    @patch('retro_righter.tools._decode_b64_str')
    def test_image_part_invalid_b64_json(self, mock_decode_b64_str, mock_logger):
        mock_decode_b64_str.side_effect = Exception("Simulated decode error")
        parts_data = [{"mime_type": "image/bmp", "b64_json": "this_is_not_valid_b64"}]
        callback_context = self._create_mock_callback_context(parts_data)
        _save_uploaded_image_to_state(callback_context)
        self.assertIsNone(callback_context.state.get("uploaded_image_b64"))
        self.assertTrue(callback_context.state.get("uploaded_image_parts") is None or \
                        len(callback_context.state.get("uploaded_image_parts")) == 0)
        mock_logger.error.assert_any_call("Callback: Failed to decode base64 from part 0: Simulated decode error")
        mock_logger.info.assert_any_call("Callback: No valid image parts found to save to the list.")

    @patch('retro_righter.tools.logger')
    def test_state_clearing_before_processing(self, mock_logger):
        initial_state = {
            "uploaded_image_b64": "old_image_data",
            "uploaded_mask_b64": "old_mask_data",
            "uploaded_image_parts": [{"b64": "old_part_data", "mime_type": "image/gif"}],
            "unrelated_key": "should_remain"
        }
        new_image_bytes = create_dummy_image_bytes("new_image")
        new_image_b64 = encode_to_b64_string(new_image_bytes)
        parts_data = [{"mime_type": "image/png", "raw_data": new_image_bytes}]
        callback_context = self._create_mock_callback_context(parts_data)
        callback_context.state = initial_state
        _save_uploaded_image_to_state(callback_context)
        self.assertEqual(callback_context.state.get("uploaded_image_b64"), new_image_b64)
        self.assertIsNone(callback_context.state.get("uploaded_mask_b64"))
        self.assertIsNotNone(callback_context.state.get("uploaded_image_parts"))
        self.assertEqual(len(callback_context.state["uploaded_image_parts"]), 1)
        self.assertEqual(callback_context.state["uploaded_image_parts"][0]["b64"], new_image_b64)
        self.assertEqual(callback_context.state.get("unrelated_key"), "should_remain")
        mock_logger.debug.assert_any_call("Cleared key 'uploaded_image_b64' in session state by setting to None.")
        mock_logger.debug.assert_any_call("Cleared key 'uploaded_mask_b64' in session state by setting to None.")
        mock_logger.debug.assert_any_call("Cleared key 'uploaded_image_parts' in session state by setting to None.")

    @patch('retro_righter.tools.logger')
    def test_state_after_no_valid_images_found_when_previously_set(self, mock_logger):
        initial_state = {
            "uploaded_image_b64": "old_image_data",
            "uploaded_image_parts": [{"b64": "old_part_data", "mime_type": "image/jpeg"}]
        }
        parts_data_with_no_valid_images = [{"mime_type": "text/plain"}]
        callback_context = self._create_mock_callback_context(parts_data_with_no_valid_images)
        callback_context.state = initial_state
        _save_uploaded_image_to_state(callback_context)
        self.assertIsNone(callback_context.state.get("uploaded_image_b64"))
        self.assertIsNone(callback_context.state.get("uploaded_image_parts"))
        mock_logger.info.assert_any_call("Callback: No valid image parts found to save to the list.")
        mock_logger.debug.assert_any_call("Cleared key 'uploaded_image_b64' in session state by setting to None.")
        mock_logger.debug.assert_any_call("Cleared key 'uploaded_image_parts' in session state by setting to None.")

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
