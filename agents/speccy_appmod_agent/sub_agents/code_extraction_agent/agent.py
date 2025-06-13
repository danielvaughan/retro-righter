from google.adk.agents import Agent, LlmAgent

from .tools.tools import write_bas_file

code_extraction_agent = LlmAgent(
    name="code_extraction_agent",
    model="gemini-2.0-flash",
    description="Code extraction agent for extracting ZX Spectrum code from images and input text",
    instruction="""
    You are a ZX Spectrum basic code extraction agent.
    
    Code can presented to you as text or as part of an image of a book or magazine page.
    
    You task is to accurately extract just the zx spectrum basic code.
    
    ## OUTPUT INSTRUCTIONS
    - ZX spectrum basic code
    - Do not add formatting markers or explanations
    """,
    output_key="extracted_code",
)
