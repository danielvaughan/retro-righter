import logging

from google.adk.agents import Agent

from .tools import return_tap

logger = logging.getLogger(__name__)

summary_agent = Agent(
    name="summary_agent",
    model="gemini-2.0-flash",
    description="Summary agent for Spectrum Appmod",
    instruction="""
    You are a summary agent for what has happened in the session
    
    ## INPUTS
    **Current Code:**
    {current_code}
    
    ## OUTPUT INSTRUCTIONS
    Summarise the function of the code extracted and the changes made in well presented markdown
    
    Return the tap file {artifact.zxspectrum.tap}.
    """,
    tools=[],
)
