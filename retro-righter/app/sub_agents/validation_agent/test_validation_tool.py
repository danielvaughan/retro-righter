import unittest
from unittest.mock import patch, MagicMock
from speccy_appmod_agent.sub_agents.validation_agent.tools import validate_spectrum_code


class TestValidateSpectrumCode(unittest.TestCase):

    @patch('subprocess.run')
    def test_successful_execution(self, mock_subprocess_run):
        """Tests successful execution of bas2tap."""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "success"
        mock_process.stderr = ""
        mock_subprocess_run.return_value = mock_process

        result = validate_spectrum_code('10 PRINT "hello"')
        self.assertIn("--- stdout ---", result)
        self.assertIn("success", result)
        self.assertNotIn("--- stderr ---", result)
        mock_subprocess_run.assert_called_once()

    @patch('subprocess.run')
    def test_execution_with_error(self, mock_subprocess_run):
        """Tests execution of bas2tap with an error."""
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stdout = ""
        mock_process.stderr = "error"
        mock_subprocess_run.return_value = mock_process

        result = validate_spectrum_code('10 PRNT "hello"')
        self.assertIn("--- stderr ---", result)
        self.assertIn("error", result)
        self.assertIn("non-zero status: 1", result)
        mock_subprocess_run.assert_called_once()

    @patch('subprocess.run', side_effect=FileNotFoundError("bas2tap not found"))
    def test_bas2tap_not_found(self, mock_subprocess_run):
        """Tests that FileNotFoundError is raised if bas2tap is not found."""
        with self.assertRaises(FileNotFoundError):
            validate_spectrum_code('10 PRINT "hello"')

    @patch('os.path.exists')
    @patch('os.remove')
    def test_temp_files_are_cleaned_up_on_success(self, mock_os_remove, mock_os_path_exists):
        """Tests that temporary files are cleaned up on success."""
        mock_os_path_exists.return_value = True
        with patch('subprocess.run') as mock_subprocess_run:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_subprocess_run.return_value = mock_process

            validate_spectrum_code('10 PRINT "hello"')

            self.assertEqual(mock_os_remove.call_count, 2)

    @patch('os.path.exists')
    @patch('os.remove')
    def test_temp_files_are_cleaned_up_on_error(self, mock_os_remove, mock_os_path_exists):
        """Tests that temporary files are cleaned up on error."""
        mock_os_path_exists.return_value = True
        with patch('subprocess.run') as mock_subprocess_run:
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_subprocess_run.return_value = mock_process

            validate_spectrum_code('10 PRINT "hello"')

            self.assertEqual(mock_os_remove.call_count, 2)


if __name__ == '__main__':
    unittest.main()
