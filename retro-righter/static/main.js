const form = document.getElementById('upload-form');
const responseDiv = document.getElementById('response');
const fileInput = document.getElementById('file');

form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const file = fileInput.files[0];
    if (!file) {
        responseDiv.textContent = 'Please select a PNG image.';
        return;
    }

    responseDiv.innerHTML = 'Processing...';

    const reader = new FileReader();
    reader.onload = async (e) => {
        const base64Image = e.target.result.split(',')[1];

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
                        { "inline_data": { "mime_type": "image/png", "data": base64Image } }
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
                    responseDiv.innerHTML = responseText;
                } else {
                    responseDiv.textContent = 'Could not find a response from the agent.';
                    console.log('Unexpected response structure:', result);
                }
            } else {
                responseDiv.textContent = 'Could not extract code from response.';
                console.log('Unexpected response structure:', result);
            }

        } catch (error) {
            responseDiv.textContent = `An error occurred: ${error.message}`;
            console.error(error);
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

function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}
