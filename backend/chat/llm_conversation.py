import os
import logging
from typing import List, Any
from groq import AsyncGroq

from tools.dictionary import get_from_dict
from chat.models import Conversation
from chaindata.evm.token_metadata import get_token_metadata
from chaindata.odos import build_swap_transaction
from chaindata.evm.token_lists import get_token_addresses_from_symbols
from tools.typing import UserDetails
from chaindata.active_chains import get_active_chains
from chaindata.constants import IntChainId

logger = logging.getLogger(__name__)

client = AsyncGroq(
    api_key=os.environ.get("GROQ_API_KEY"),
)


MODEL = "deepseek-r1-distill-llama-70b"
SYSTEM_PROMPT = """
You are a helpful AI assistant whose goal is to help onboard users to Sonic chain.

Some details about the chain:
- It is the defi powerhouse with yields upto 40% on stables.
- There is an airdrop worth $200M Sonic in 6 months, good time to farm!

Steps to onboard a user:
1. Ask user to fund their wallet with natives on Solana or Sonic chain.
2. verify that the user has funded their wallet. 
3. Let the user know the chains they have funded.
4. If any chain other than Sonic was funded, bridge those assets to Sonic chain. 
"""

NEW_THREAD_START_MESSAGES = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT,
    },
    {
        "role": "assistant",
        "content": "Hello! I'm here to help you get started on Sonic Chain. Let's get you set up. Please fund your wallet with natives on Base or Sonic chain.",
    },
]


async def complete_conversation(
    conversation: Conversation,
    user_details: UserDetails,
) -> None:
    await get_completion(conversation)

    # Handle tool calls if present
    while conversation.messages[-1].get("tool_calls"):
        tools_responses = []
        for tool_call in conversation.messages[-1].get("tool_calls"):
            print("tool call", tool_call)
            try:
                function_name = get_from_dict(tool_call, ["function", "name"])
                fn_args = get_from_dict(tool_call, ["function", "arguments"])
                # Call the appropriate function
                if function_name == "is_user_wallet_funded":
                    result = await is_user_wallet_funded(user_details)
                elif function_name == "bridge_assets":
                    result = (
                        "Assets bridged successfully"  # Implement actual bridging logic
                    )
                else:
                    result = f"Error: Unknown function '{function_name}'"

                # Add the function response to messages
                tools_responses.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": function_name,
                        "content": str(result),
                    }
                )
            except Exception as e:
                # Add error response for failed tool calls
                logger.error(f"Error executing {str(e)}")
                tools_responses.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": function_name,
                        "content": f"Error executing {function_name}: {str(e)}",
                    }
                )

        conversation.messages.extend(tools_responses)
        await conversation.asave()

        # Get a new response from the assistant with the tool results
        await get_completion(conversation)

    return


async def get_completion(conversation: Conversation) -> None:
    tools = [
        {
            "type": "function",
            "function": {
                "name": "is_user_wallet_funded",
                "description": "Check if the user has funded their wallet.",
                "parameters": {},
                "returns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of funded chains",
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "bridge_assets",
                "description": "Bridge assets from any chain to Sonic chain.",
                "parameters": {},
                "returns": "string",
            },
        },
    ]

    # Clean up any messages that might have a 'reasoning' field as they are not supported by groq API
    messages = [
        {k: v for k, v in message.items() if k != "reasoning"}
        for message in conversation.messages
    ]

    chat_completion_obj = await client.chat.completions.create(
        messages=messages,
        model=MODEL,
        tools=tools,
        tool_choice="auto",
    )

    conversation.messages.append(chat_completion_obj.choices[0].message.to_dict())
    await conversation.asave()


async def is_user_wallet_funded(user_details: UserDetails) -> List[str]:
    active_chains = await get_active_chains(user_details.evm_wallet_address)
    return [IntChainId.get_str(chain_id) for chain_id in active_chains]
