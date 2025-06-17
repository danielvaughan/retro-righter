from google.adk.agents import Agent
import argparse

from .tools import validate_spectrum_code, exit_loop

validation_agent = Agent(
    name="validation_agent",
    model="gemini-2.0-flash",
    description="Validation agent for ZX Spectrum code",
    instruction="""
    You are a helpful agent that validates if ZX Spectrum code is valid.
    
    If the code is not valid you should return an error message for debugging.
    
    ## OUTPUT INSTRUCTIONS
    IF the code fails:
      - Output any error message from the stderr output of the validate_spectrum_code function
      
    ELSE IF the validate_spectrum_code function does not contain anything in the stderr output:
      - Call the exit_loop function
      - Return "Code meets all requirements. Exiting the refinement loop."
      
    Do not embellish your response. Either provide an error message OR call exit_loop and return the valid code.
    
    ## CODE TO VALIDATE
    {current_code}
    """,
    tools=[validate_spectrum_code, exit_loop],
    output_key="validation_errors",
)
