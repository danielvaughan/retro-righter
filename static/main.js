document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('upload-form');
    const fileInput = document.getElementById('file');
    const dropZone = document.getElementById('drop-zone');
    const fileInfo = document.getElementById('file-info');
    const responseDiv = document.getElementById('response');
    const submitButton = document.getElementById('submit-button');
    const buttonText = document.getElementById('button-text');
    const loadingSpinner = document.getElementById('loading-spinner');

    // Function to update file info display
    function updateFileInfo(file) {
        if (file) {
            fileInfo.textContent = `Selected file: ${file.name}`;
        } else {
            fileInfo.textContent = '';
        }
    }

    // Handle file selection via file input
    fileInput.addEventListener('change', () => {
        updateFileInfo(fileInput.files[0]);
    });

    // Drag and drop event listeners
    dropZone.addEventListener('dragover', (event) => {
        event.preventDefault();
        dropZone.classList.add('border-indigo-400');
        dropZone.classList.remove('border-gray-500');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('border-indigo-400');
        dropZone.classList.add('border-gray-500');
    });

    dropZone.addEventListener('drop', (event) => {
        event.preventDefault();
        dropZone.classList.remove('border-indigo-400');
        dropZone.classList.add('border-gray-500');

        const files = event.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files; // Assign dropped file to the input
            updateFileInfo(files[0]);
        }
    });

    // Handle form submission
    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        const file = fileInput.files[0];
        if (!file) {
            fileInfo.textContent = 'Please select an image file first.';
            fileInfo.classList.add('text-red-400');
            return;
        }
        fileInfo.classList.remove('text-red-400');

        // Update button state to show loading
        submitButton.disabled = true;
        buttonText.classList.add('hidden');
        loadingSpinner.classList.remove('hidden');
        responseDiv.innerHTML = '<p class="text-gray-500">Processing your image... please wait.</p>';

        const reader = new FileReader();
        reader.onload = async (e) => {
            const base64Image = e.target.result.split(',')[1];
            const mimeType = file.type;

            const APP_NAME = "app";
            const USER_ID = "user-from-ui";
            const SESSION_ID = generateUUID();

            try {
                // Step 1: Create a new session
                const sessionResponse = await fetch(`/apps/${APP_NAME}/users/${USER_ID}/sessions/${SESSION_ID}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({})
                });

                if (!sessionResponse.ok) {
                    const errorText = await sessionResponse.text();
                    throw new Error(`Session creation failed: ${sessionResponse.status} ${sessionResponse.statusText}. ${errorText}`);
                }
                console.log('Session created:', SESSION_ID);

                // Step 2: Send the image for processing
                const payload = {
                    app_name: APP_NAME,
                    user_id: USER_ID,
                    session_id: SESSION_ID,
                    new_message: {
                        parts: [
                            { "text": "extract" },
                            { "inline_data": { "mime_type": mimeType, "data": base64Image } }
                        ],
                        role: "user"
                    }
                };

                const runResponse = await fetch('/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (!runResponse.ok) {
                    const errorText = await runResponse.text();
                    throw new Error(`Processing failed: ${runResponse.status} ${runResponse.statusText}. ${errorText}`);
                }

                const result = await runResponse.json();

                if (result && Array.isArray(result)) {
                    const agentMessage = result.find(m => m.author === 'summary_agent');

                    if (agentMessage && agentMessage.content && agentMessage.content.parts && agentMessage.content.parts[0] && agentMessage.content.parts[0].text) {
                        const responseText = agentMessage.content.parts[0].text;
                        // Use marked.js to parse the Markdown response
                        responseDiv.innerHTML = marked.parse(responseText);
                    } else {
                        responseDiv.innerHTML = '<p class="text-red-400">Error: Could not find a valid response from the agent.</p>';
                        console.log('Unexpected response structure:', result);
                    }
                } else {
                    responseDiv.innerHTML = '<p class="text-red-400">Error: Could not extract data from the response.</p>';
                    console.log('Unexpected response structure:', result);
                }

            } catch (error) {
                responseDiv.innerHTML = `<p class="text-red-400">An error occurred: ${error.message}</p>`;
                console.error(error);
            } finally {
                // Restore button state
                submitButton.disabled = false;
                buttonText.classList.remove('hidden');
                loadingSpinner.classList.add('hidden');
            }
        };

        reader.readAsDataURL(file);
    });

    function generateUUID() { // Public Domain/MIT
        var d = new Date().getTime();//Timestamp
        var d2 = ((typeof performance !== 'undefined') && performance.now && (performance.now()*1000)) || 0;//Time in microseconds since page-load or 0 if unsupported
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            var r = Math.random() * 16;//random number between 0 and 16
            if(d > 0){//Use timestamp until depleted
                r = (d + r)%16 | 0;
                d = Math.floor(d/16);
            } else {//Use microseconds since page-load if supported
                r = (d2 + r)%16 | 0;
                d2 = Math.floor(d2/16);
            }
            return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
        });
    }
});
