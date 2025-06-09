from google.adk.agents import Agent

code_extraction_agent = Agent(
    name="code_extraction_agent",
    model="gemini-2.0-flash",
    description="Code extraction agent for extracting ZX Spectrum code from images",
    instruction="""
    
    """,
    tools=[],
)
