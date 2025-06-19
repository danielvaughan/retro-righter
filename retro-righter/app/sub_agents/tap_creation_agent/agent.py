import logging

from google.adk.agents import Agent

from .tools import create_tap

logger = logging.getLogger(__name__)

tap_creation_agent = Agent(
    name="tap_generation_agent",
    model="gemini-2.0-flash",
    description="Tap creation agent for ZX Spectrum code",
    instruction="""
    You are an agent that creates a TAP file from Spectrum BASIC code.
    
    ## INPUTS
    **Current Code:**
    {current_code}
    
    ## OUTPUT INSTRUCTIONS
    - Output ONLY the path to the generated TAP file
    - Do not add explanations or justifications
    """,
    tools=[create_tap],
    output_key="tap_file_path",
)
