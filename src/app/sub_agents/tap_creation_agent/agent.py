from google.adk.agents import Agent

from . import prompt
from .tools import create_tap

MODEL = "gemini-2.5-flash"

tap_creation_agent = Agent(
    name="tap_generation_agent",
    model=MODEL,
    description="Tap creation agent for ZX Spectrum code",
    instruction=prompt.TAP_CREATION_PROMPT,
    tools=[create_tap],
    output_key="tap_file_path",
)
