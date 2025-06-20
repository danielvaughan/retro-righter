from google.adk.agents import Agent

from . import prompt

from .tools import validate_spectrum_code, exit_loop

MODEL = "gemini-2.5-flash"

validation_agent = Agent(
    model=MODEL,
    name="validation_agent",
    description="Validation agent for ZX Spectrum code",
    instruction=prompt.VALIDATION_PROMPT,
    tools=[validate_spectrum_code, exit_loop],
    output_key="validation_errors",
)
