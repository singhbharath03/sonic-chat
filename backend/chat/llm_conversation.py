import os
from typing import List
from groq import AsyncGroq

from chat.typing import Message_
from chaindata.active_chains import get_active_chains
from chaindata.constants import IntChainId

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
        "content": "Hello! I'm here to help you get started on Sonic Chain. Let's get you set up. Please fund your wallet with natives on Solana or Sonic chain.",
    },
]


async def process_chat(messages: List[Message_]) -> List[Message_]:
    chat_completion = await get_completion(messages)
    response = chat_completion.choices[0].message

    # TODO: Handle tool calls

    # Handle tool calls if present
    if response.tool_calls:
        # Add assistant's response with tool calls to messages
        messages.append(
            {
                "role": "assistant",
                "content": response.content,
                "tool_calls": response.tool_calls,
            }
        )

        tools_responses = []
        for tool_call in response.tool_calls:
            function_name = tool_call.function.name

            # Call the appropriate function
            if function_name == "is_user_wallet_funded":
                result = await is_user_wallet_funded(wallet_address)
            elif function_name == "bridge_assets":
                result = (
                    "Assets bridged successfully"  # Implement actual bridging logic
                )

            # Add the function response to messages
            tools_responses.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": str(result),
                }
            )

        messages.extend(tools_responses)
        # Get a new response from the assistant with the tool results
        chat_completion = await get_completion(messages)
        response = chat_completion.choices[0].message

    messages.append({"role": "assistant", "content": response.content})

    return messages


async def get_completion(messages: List[dict]) -> str:
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

    return await client.chat.completions.create(
        messages=messages,
        model=MODEL,
        tools=tools,
        tool_choice="auto",
    )


async def is_user_wallet_funded(wallet_address: str) -> List[str]:
    active_chains = await get_active_chains(wallet_address)
    return [IntChainId.get_str(chain_id) for chain_id in active_chains]
