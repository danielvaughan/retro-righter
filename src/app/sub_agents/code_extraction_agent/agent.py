from google.adk.agents import LlmAgent

from . import prompt

MODEL = "gemini-2.5-flash"

code_extraction_agent = LlmAgent(
    model=MODEL,
    name="code_extraction_agent",
    description="Code extraction agent for extracting ZX Spectrum code from images and input text",
    instruction=prompt.CODE_EXTRACTION_PROMPT,
    output_key="current_code",
)
