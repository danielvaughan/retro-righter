# Project Story

## Inspiration

My journey into computing began with the **ZX Spectrum 128K**. I remember the frustrating experience of meticulously typing code listings from books, only to discover errors, like missing closing quotes. This led to the idea of building a system that could **automatically verify and fix these code listings** in the books before publication, something challenging 40 years ago but now a lot easier with GenAI.

## What it does

Retro Righter is a multi-agent system built with the **Google Agent Development Kit (ADK)**. It extracts, validates, debugs, and creates functional executables from images of old computer code listings.

Specifically, it:

* **Extracts code** from an image of a code listing using Gemini's multimodal capabilities.
* **Validates the extracted code** using `bas2tap`, a tool that creates tap (tape) files for Spectrum emulators and validates code during conversion.
* **Debugs any issues** identified during validation, iterating through a cycle until the code is correct.
* **Creates a tap file** from the validated code, again using `bas2tap`.
* **Provides a summary** of the code, any corrections made, and a link to download the generated tap file for use in a Spectrum emulator.

## How we built it

I built the solution using the **Python version of the Google ADK**. The architecture consists of several specialised agents, each with a single job:

* **`code_extraction_agent`**: Extracts code from an image.
* **`validation_agent`**: Validates Spectrum code using `bas2tap`.
* **`debugging_agent`**: Corrects validation errors.
* **`tap_creation_agent`**: Creates a tap file from valid code `bas2tap`.
* **`summary_agent`**: Generates a summary report and provides a link to the tap file.

To handle iterative validation and debugging, I put the `validation_agent` and `debugging_agent` inside a **LoopAgent**. This loop and the code_extraction_agent and tap_creation_agent form a **Sequential Agent**, creating an "Image to Tap pipeline."

All agents use **Gemini 2.5 Flash** as their Large Language Model (LLM).

I used **ADK callbacks**: a `before_agent_callback` to load the image into the system state and an `after_agent_callback` to upload the generated tap file to a **Google Cloud Storage bucket**, returning its URL.

A root Sequential Agent orchestrated the entire process, calling the Image to Tap pipeline and then the summary agent.

For the **UI**, I used **Windsurf and Gemini 2.5 Pro** to create a simple frontend for image uploads and display the summary report. This UI interacts with the agents through the **FastAPI** framework provided by Google ADK.

I deployed the application on **Google Cloud Run**, packaging the backend and front end into a single Docker container for efficient hosting.

## Challenges we ran into

A challenging part of this project was understanding agent callbacks, how to get the image into state, and how to upload the generated tap file to Google Cloud storage. Initially, the image file upload failed in ADK due to a bug in ADK, but this was fixed in the 1.3.0 release.

The most challenging part was that this is a different type of development. Whereas conventional development is deterministic, that is, the computer executes the code as written, with agents, it is a lot more like I am instructing a person with instructions and tools, and it is up to the agent how it performs the task. The results, however, are generally positive, with the agents often going beyond my expectations.

## Accomplishments that we're proud of

I'm proud of building an application that extracted, validated, debugged, and converted old code listings into functional tap files as planned. This includes:

* Successfully leveraging **Gemini's multimodal capabilities** for accurate code extraction.
* Integrating external tools like `bas2tap` using **Google ADK's tool-calling functionality**.
* Creating an **agentic system** that can automatically iterate through debugging cycles.
* Developing a functional **UI** and deploying the entire application on **Google Cloud Run** with a user-friendly URL.
* The project demonstrates Google ADK's potential for automating complex, multi-step business processes involving information extraction and correction from documents.

## What we learned

Several key learnings emerged from this project:

* **Google ADK's Potential**: The project showcased the power of Google ADK for building multi-agent systems and automating processes that traditionally involve manual data extraction and correction.
* **Gemini's Unexpected Capabilities**: Gemini often did more than expected. For instance, with Google Search enabled during prompt development, Gemini not only extracted code but also found and used an external GitHub listing to validate it. Another example involved Gemini generating valid Spectrum code for "say hello" when given a text prompt instead of an image. This experience felt much like managing a human with initiative rather than traditional programming.
* **Automation of Manual Processes**: The project illustrated how multimodal LLMs like Gemini make it cheap and easy to fully automate previously unfeasible processes, especially those involving paper documents and information extraction.

## What's next for Retro Righter

Retro Righter follows a "happy path" for code extraction and correction. To take it forward, it needs to be tested on a lot more examples, and the debugging agent in particular could be enhanced greatly. 

I also like the system's "vibe coding" abilities when given the "say hello" prompt. This could be built upon to generate and validate complete spectrum programs from prompts.