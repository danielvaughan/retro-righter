import logging
import uuid

from google.adk import Runner
from google.adk.agents import SequentialAgent, LoopAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.sessions import InMemorySessionService

from .sub_agents.debugging_agent import debugging_agent
from .sub_agents.code_extraction_agent.agent import code_extraction_agent
from .sub_agents.summary_agent import summary_agent
from .sub_agents.tap_creation_agent.agent import tap_creation_agent
from .sub_agents.validation_agent import validation_agent

from .tools import _save_uploaded_image_to_state, _save_tap_artifact_to_state

logger = logging.getLogger(__name__)

session_service_stateful = InMemorySessionService()
artifact_service = InMemoryArtifactService()

APP_NAME = "Speccy AppMod Agent"
USER_ID = "anonymous"
SESSION_ID = str(uuid.uuid4())
stateful_session = session_service_stateful.create_session(
    app_name=APP_NAME,
    user_id=USER_ID,
    session_id=SESSION_ID,
)

code_refinement_loop = LoopAgent(
    name="CodeRefinementLoop",
    max_iterations=3,
    sub_agents=[
        validation_agent,
        debugging_agent,
    ],
    description="Iteratively validated and debugs any error in the code until the code is valid.",
)

image_to_tap_agent = SequentialAgent(
    name="TapCreationPipeline",
    sub_agents=[
        code_extraction_agent,
        code_refinement_loop,
        tap_creation_agent,
    ],
    before_agent_callback=_save_uploaded_image_to_state,
    after_agent_callback=_save_tap_artifact_to_state,
)

root_agent = SequentialAgent(
    name="RootAgent",
    sub_agents=[
        image_to_tap_agent,
        summary_agent
    ],
)

logger.info(f"root_agent '{root_agent.name}' initialized")

runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service_stateful,
    artifact_service=artifact_service,
)
