import logging

from google.adk.agents import Agent

from .tools import validate_spectrum_code, exit_loop

logger = logging.getLogger(__name__)

validation_agent = Agent(
    name="validation_agent",
    model="gemini-2.0-flash",
    description="Validation agent for ZX Spectrum code",
    instruction="""
    You are a ZX spectrum code validation agent.
    
    You task is to validate if ZX Spectrum code is valid and if not provide an error message.
    
    ## INPUTS
    **Current Code:**
    {current_code}
    
    ## OUTPUT INSTRUCTIONS
    IF the code fails:
      - Output any error message from the stderr output of the validate_spectrum_code function
      
    ELSE IF the validate_spectrum_code function does not contain anything in the stderr output:
      - Call the exit_loop function
      - Return "Code meets all requirements. Exiting the refinement loop."
    """,
    tools=[validate_spectrum_code, exit_loop],
    output_key="validation_errors",
)
