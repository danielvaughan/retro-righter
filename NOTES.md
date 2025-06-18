# Notes

All agents are called agent.py

## Flow

1. Prompt with image
2. code_extraction_agent - extract code from image and stores in `current_code`.
3. validation_agent - takes `current_code` and validates it using the `validate_spectrum_code` which wraps the `bas2tap` command, storing any errors in `validation_errors`.
4. debugging_agent - takes `current_code` and `validation_errors` and stores the fixed code in `current_code`.
5. tap_creation_agent - takes `current_code` and creates a TAP file using the `tap_creation` tool which also wraps the `bas2tap` command storing the file path in ``

## Bugs

- [X] display_name parameter is not supported in Gemini API - https://github.com/google/adk-python/issues/1182