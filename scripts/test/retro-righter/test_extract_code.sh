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
#       "role": "model",
#       "parts": [
#         {
#           "functionResponse": {
#             "name": "text_to_speech",
#             "response": {
#               "result": {
#                 "content": [
#                   {"type": "text", "text": "File saved as: /tmp/audio_output/audio_xyz.mp3."}
#                 ]
#               }
#             }
#           }
#         }
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

