
import logging
from uuid import uuid4
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from models import client,model
from tools import (
    calculate_right_refund,
    get_today_date,
    issue_refund_ticket,
    get_user_purchase_history,
)
from prompts import agent_system_prompt
from objects import Answer

# Load environment variables BEFORE importing the model.
load_dotenv()

# --------------------------------------------------
# LOGGING CONFIGURATION
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# --------------------------------------------------
# CHECKPOINTER
# --------------------------------------------------

# Keeps conversation history for each thread during
# the lifetime of this application.
checkpointer = InMemorySaver()


# --------------------------------------------------
# TOOL REGISTRATION
# --------------------------------------------------

refund_tools = [
    get_user_purchase_history,
    get_today_date,
    calculate_right_refund,
    issue_refund_ticket,
]


# --------------------------------------------------
# CREATE REFUND AGENT
# --------------------------------------------------

agent = create_agent(
    model=model,
    system_prompt=agent_system_prompt,
    tools=refund_tools,
    response_format=Answer,
    checkpointer=checkpointer,
)


# --------------------------------------------------
# CONVERSATION FUNCTION
# --------------------------------------------------

def run_conversation(
    initial_message: str = "I would like to request a refund",
    max_turns: int = 15,
):
    """
    Start and manage a refund conversation.

    Args:
        initial_message: Initial customer message.
        max_turns: Maximum number of customer interaction turns.
    """

    # Generate a unique ID for this conversation.
    thread_id = str(uuid4())

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    logger.info("Starting refund conversation: %s", thread_id)

    print("\nCustomer:", initial_message)

    user_message = initial_message
    turn = 0

    try:
        while turn < max_turns:

            turn += 1

            # Send the latest user message.
            response = agent.invoke(
                {
                    "messages": [
                        HumanMessage(content=user_message)
                    ]
                },
                config=config,
            )

            # Retrieve structured response.
            structured_response = response.get("structured_response")

            if structured_response is None:
                logger.error("Agent did not return structured output.")
                print("Agent error: Unable to generate a valid response.")
                break

            # Display agent response.
            print("\nRefund Agent:", structured_response.answer)

            # Check whether the conversation should continue.
            if not structured_response.conversation:
                logger.info("Conversation completed.")
                break

            # Get the next customer response.
            user_message = input("\nCustomer: ").strip()

            if not user_message:
                print("Please enter a valid response.")
                user_message = input("\nCustomer: ").strip()

            if not user_message:
                print("No response received. Ending conversation.")
                break

        else:
            logger.warning("Maximum conversation turns reached.")
            print("\nMaximum conversation turns reached.")

    except KeyboardInterrupt:
        logger.info("Conversation interrupted by customer.")
        print("\nConversation interrupted.")

    except Exception:
        logger.exception("An error occurred during the conversation.")
        print(
            "\nSorry, an unexpected error occurred. "
            "Please try again later."
        )

    finally:
        logger.info("Conversation ended: %s", thread_id)
        print("\nRefund conversation ended.")


if __name__ == "__main__":
    run_conversation()
