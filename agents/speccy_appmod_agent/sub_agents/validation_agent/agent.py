from google.adk.agents import Agent

validation_agent = Agent(
    name="validation_agent",
    model="gemini-2.0-flash",
    description="Validation agent for ZX Spectrum code",
    instruction="""
    You are a helpful agent that validates if ZX Spectrum code is valid.
    
    You should only output valid ZX Spectrum basic code
    
    You should echo back only the valid code is valid formatted as a .bas text file.
    
    If the code is not valid you should return a helpful error message for debugging.
    """,
    tools=[],
)
