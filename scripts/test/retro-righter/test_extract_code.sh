#!/bin/bash

# Test script that extracts audio file path from the response
# This helps verify the format of audio responses from the speaker agent
# when accessed via the standard ADK API Server.

# Expected Response Structure (from ADK API Server /run):
# A stream of JSON events. The script looks for specific structures within these events:
# - A functionResponse event for 'text_to_speech' containing the path in its result text.
# - OR - General text output that might contain the path (less reliable).
# Example Event Fragment (simplified):
# [
#   ...
#   {
#     "content": {
#       "parts": [
      #        {
      #          "text": "### ZX Spectrum Code Session Report\n\nThis report summarizes the process of extracting, validating, and generating a TAP file for the provided ZX Spectrum BASIC code.\n\n#### 1. Code Functionality Overview\nThe code implements a \"satellite launch\" game. The player must launch a satellite to a randomly generated target height (H) within 8 attempts. For each attempt, the player inputs an angle and a speed. The program then calculates the difference between the player's input and the ideal angle/speed for the target height, providing feedback (\"TOO SHALLOW\", \"TOO STEEP\", \"TOO SLOW\", \"TOO FAST\"). If the player's inputs are within acceptable error margins for both angle and speed, they win. Otherwise, after 8 failed attempts, the game ends with a \"YOU'VE FAILED\" message.\n\n#### 2. Session Activity Breakdown\n-   **Initial Code State:** The BASIC code was initially extracted from an image. No immediate errors were apparent during the initial extraction.\n-   **Validation and Debugging Process:**\n    -   The code required validation and debugging.\n    -   A syntax error was identified on line 120, related to the conditional branching statement (`THEN GOTO` or `THEN <linenumber>`). The validator initially reported errors for both `THEN GOTO 200` and `THEN 200` variations.\n    -   Through two iterations of debugging, the issue was addressed. The final syntax for line 120, `IF ABS(A)<2 AND ABS(V)<100 THEN GOTO 200`, was successfully processed for TAP file generation, indicating its validity within the system's pipeline.\n    -   The code successfully passed all ZX Spectrum BASIC validation checks required for TAP file creation.\n-   **TAP File Generation:** The TAP file was successfully created from the validated code.\n\n#### 3. Access Your TAP File\n\nYou can download the generated ZX Spectrum TAP file here:\n[Download TAP File](https://storage.googleapis.com/retro-righter-taps/tmpl2wyrzgn.tap)"
      #        }
      #      ],
      #      "role": "model"
      #    },
#       ]
#     }
#   }
#   ...
# ]

# The app_name should match the full Python import path from the project root
APP_NAME="app"
USER_ID="anonymous"
SESSION_ID="test-extract-$(date +%s)"  # Unique session ID

# Step 1: Create session explicitly
echo "Creating a new session..."
curl -X POST "http://localhost:8000/apps/$APP_NAME/users/$USER_ID/sessions/$SESSION_ID" \
  -H "Content-Type: application/json" \
  -d "{}" | jq .

sleep 2  # Brief pause between requests


IMAGE_BASE64=$(base64 -i intergalactic_games.png)

cat << EOF > /tmp/adk_payload.json
{
  "app_name": "$APP_NAME",
  "user_id": "$USER_ID",
  "session_id": "$SESSION_ID",
  "new_message": {
    "parts": [
      {"text": "extract"},
      {
        "inlineData": {
          "mimeType": "image/png",
          "data": "$IMAGE_BASE64"
        }
      }
    ],
    "role": "user"
  }
}
EOF

# 3. Call curl, telling it to read the data from the file
RESPONSE=$(curl -s -X POST "http://localhost:8000/run" \
  -H "Content-Type: application/json" \
  -d @/tmp/adk_payload.json)

# 4. (Optional) Clean up the temporary file
rm /tmp/adk_payload.json

echo "Full response:"
echo "$RESPONSE" | jq .

