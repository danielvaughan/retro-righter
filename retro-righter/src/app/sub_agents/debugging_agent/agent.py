from google.adk.agents import Agent

from . import prompt

MODEL = "gemini-2.5-flash"

debugging_agent = Agent(
    model=MODEL,
    name="debugging_agent",
    description="Debugging agent for ZX Spectrum code",
    instruction=prompt.DEBUGGING_PROMPT,
    output_key="current_code",
    tools=[],
)
