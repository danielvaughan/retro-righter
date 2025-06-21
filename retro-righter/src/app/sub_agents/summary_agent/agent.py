from google.adk.agents import Agent

from . import prompt

MODEL = "gemini-2.5-flash"

summary_agent = Agent(
    model=MODEL,
    name="summary_agent",
    description="Summary agent for explaining what has happened in the session",
    instruction=prompt.SUMMARY_PROMPT,
    tools=[],
)
