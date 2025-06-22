import logging
import os
import sys
import uuid
import asyncio

import google

from google.cloud import logging as cloud_logging

from google.adk import Runner
from google.adk.agents import SequentialAgent, LoopAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.sessions import InMemorySessionService

from .sub_agents.debugging_agent import debugging_agent
from .sub_agents.code_extraction_agent.agent import code_extraction_agent
from .sub_agents.summary_agent import summary_agent
from .sub_agents.tap_creation_agent.agent import tap_creation_agent
from .sub_agents.validation_agent import validation_agent

from .tools import _save_uploaded_image_to_state, _upload_to_gcs_and_get_url

IS_CLOUD_RUN_ENV = os.environ.get("K_SERVICE") is not None

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

if IS_CLOUD_RUN_ENV:
    print("Cloud Run environment detected. Using structured logging.")
    cloud_logging_client = cloud_logging.Client()
    cloud_logging_client.setup_logging(log_level=root_logger.level)
    adk_logger = logging.getLogger("google.adk")
    adk_logger.setLevel(logging.WARNING)
else:
    print("Local environment detected. Using human-readable logging.")
    console_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    root_logger.setLevel(logging.DEBUG)


logger = logging.getLogger(__name__)

_, project_id = google.auth.default()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")

session_service_stateful = InMemorySessionService()
artifact_service = InMemoryArtifactService()

APP_NAME = "retro-righter"
USER_ID = "anonymous"

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
    after_agent_callback=_upload_to_gcs_and_get_url,
)

root_agent = SequentialAgent(
    name="RootAgent",
    sub_agents=[image_to_tap_agent, summary_agent],
)


async def main():
    SESSION_ID = str(uuid.uuid4())
    logger.info(
        f"Initializing session with ID: {SESSION_ID} for app: {APP_NAME} and user: {USER_ID}"
    )
    stateful_session = await session_service_stateful.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )
    logger.info(f"Stateful session created successfully: {stateful_session}")

    logger.info(f"root_agent '{root_agent.name}' initialized")

    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service_stateful,
        artifact_service=artifact_service,
    )


if __name__ == "__main__":
    logger.info("Starting Retro Righter application...")
    asyncio.run(main())
