import os
import json
import logging
from typing import List, Any
from groq import AsyncGroq

from django.db import transaction
from asgiref.sync import sync_to_async

from chat.stake_sonic_txn import stake_sonic
from chat.silo_lending_txns import lend_tokens, withdraw_all_tokens, withdraw_tokens
from chat.swap_transactions import swap_tokens
from chat.typing import (
    SiloLendingDepositTxnSteps,
    SiloLendingWithdrawTxnSteps,
    SonicStakeTxnSteps,
    SwapTransactionSteps,
    TransactionFlows,
    TransactionStates,
)
from tools.dictionary import get_from_dict
from chat.models import Conversation, TransactionRequests
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

Always use `S` as the symbol for the native token of Sonic chain. Never use `SONIC` or `SONIC_CHAIN` or anything related to the name Sonic.

Some details about the chain:
- It is the defi powerhouse with yields upto 30% on stables.
- There is an airdrop worth 200M Sonic. The first season becomes claimable around June 2025, good time to farm!

Steps to onboard a user:
1. Ask user to fund their wallet with natives on Solana or Sonic chain.
2. verify that the user has funded their wallet. 
3. Let the user know the chains they have funded.
4. If any chain other than Sonic was funded, bridge those assets to Sonic chain. 

Supported actions:
- Swap tokens
- Lend, withdraw tokens
- Stake Sonic native token `S`
"""


async def complete_conversation(
    conversation: Conversation,
    user_details: UserDetails,
) -> bool:
    await get_completion(conversation)

    # Handle tool calls if present
    while conversation.messages[-1].get("tool_calls"):
        tools_responses = []
        for tool_call in conversation.messages[-1].get("tool_calls"):
            try:
                function_name = get_from_dict(tool_call, ["function", "name"])
                fn_args = json.loads(
                    get_from_dict(tool_call, ["function", "arguments"])
                )

                # Call the appropriate function
                if function_name == "is_user_wallet_funded":
                    result = await is_user_wallet_funded(user_details)
                elif function_name == "swap_tokens":
                    result = await swap_tokens(
                        conversation,
                        user_details.evm_wallet_address,
                        fn_args["input_token_symbol"],
                        fn_args["input_token_amount"],
                        fn_args["output_token_symbol"],
                    )

                    return True

                elif function_name == "lend_tokens":
                    result = await lend_tokens(
                        conversation,
                        user_details.evm_wallet_address,
                        fn_args["token_symbol"],
                        fn_args["amount"],
                    )

                    return True
                elif function_name == "withdraw_tokens":
                    result = await withdraw_tokens(
                        conversation,
                        user_details.evm_wallet_address,
                        fn_args["token_symbol"],
                        fn_args["amount"],
                    )

                    return True
                elif function_name == "withdraw_all_tokens":
                    result = await withdraw_all_tokens(
                        conversation,
                        user_details.evm_wallet_address,
                        fn_args["token_symbol"],
                    )
                    return True
                elif function_name == "stake_sonic":
                    result = await stake_sonic(
                        conversation,
                        user_details.evm_wallet_address,
                        fn_args["amount"],
                    )
                    return True

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
                import traceback

                logger.error(f"Error executing tool call: {traceback.format_exc()}")
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

    return False


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
                "name": "lend_tokens",
                "description": "Builds a transaction to lend tokens.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "token_symbol": {"type": "string"},
                        "amount": {"type": "number"},
                    },
                    "required": ["token_symbol", "amount"],
                },
                "returns": {
                    "type": "object",
                    "description": "Lending transaction details",
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "withdraw_tokens",
                "description": "Builds a transaction to withdraw tokens.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "token_symbol": {"type": "string"},
                        "amount": {"type": "number"},
                    },
                    "required": ["token_symbol", "amount"],
                },
                "returns": {
                    "type": "object",
                    "description": "Withdrawal transaction details",
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "withdraw_all_tokens",
                "description": "Builds a transaction to withdraw all tokens.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "token_symbol": {"type": "string"},
                    },
                    "required": ["token_symbol"],
                },
                "returns": {
                    "type": "object",
                    "description": "Withdrawal transaction details",
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "swap_tokens",
                "description": "Builds a transaction to swap tokens.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input_token_symbol": {"type": "string"},
                        "input_token_amount": {"type": "number"},
                        "output_token_symbol": {"type": "string"},
                    },
                    "required": [
                        "input_token_symbol",
                        "input_token_amount",
                        "output_token_symbol",
                    ],
                },
                "returns": {
                    "type": "object",
                    "description": "Swap transaction details",
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "stake_sonic",
                "description": "Builds a transaction to stake Sonic chains native token `S`.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "amount": {"type": "number"},
                    },
                    "required": ["amount"],
                },
                "returns": {
                    "type": "object",
                    "description": "Staking transaction details",
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

    max_retries = 3
    for attempt in range(max_retries):
        chat_completion_obj = await client.chat.completions.create(
            messages=messages,
            model=MODEL,
            tools=tools,
            tool_choice="auto",
        )

        response = chat_completion_obj.choices[0].message.to_dict()

        # Try to fix malformed tool calls in content
        content = response.get("content", "")
        if "<tool_call>" in content:
            try:
                # Extract the JSON between <tool_call> and the end delimiter
                tool_call_start = content.find("<tool_call>") + len("<tool_call>")
                tool_call_end = content.find("<｜tool▁calls▁end｜>")
                if tool_call_end == -1:  # Handle case where end delimiter might vary
                    tool_call_end = content.find("</tool_call>")

                if tool_call_end != -1:
                    tool_call_json = content[tool_call_start:tool_call_end]
                    tool_call_data = json.loads(tool_call_json)

                    # Reformat as proper tool calls
                    response["tool_calls"] = [
                        {
                            "id": tool_call_data.get("id", f"call_{attempt}"),
                            "type": "function",
                            "function": {
                                "name": tool_call_data["name"],
                                "arguments": json.dumps(tool_call_data["arguments"]),
                            },
                        }
                    ]
                    response["content"] = (
                        None  # Clear the content since we've extracted the tool call
                    )
                    logger.info(
                        "Successfully extracted and reformatted tool call from content"
                    )

            except (json.JSONDecodeError, KeyError) as e:
                logger.exception(f"Failed to parse tool call from content: {e}")
                if attempt < max_retries - 1:
                    continue
                else:
                    logger.error("Max retries reached for malformed tool call")

        conversation.messages.append(response)
        await conversation.asave()
        break


async def is_user_wallet_funded(user_details: UserDetails) -> List[str]:
    active_chains = await get_active_chains(user_details.evm_wallet_address)
    return [IntChainId.get_str(chain_id) for chain_id in active_chains]


async def submit_signed_transaction(
    conversation: Conversation, signed_tx_hash: str
) -> bool:
    try:
        transaction_request = await TransactionRequests.objects.aget(
            conversation=conversation, state=TransactionStates.PROCESSING
        )
    except TransactionRequests.DoesNotExist:
        raise ValueError("No pending transaction found for conversation")
    except TransactionRequests.MultipleObjectsReturned:
        raise ValueError("Multiple pending transactions found for conversation")

    transaction_request.transaction_details = None
    content = None
    if transaction_request.flow == TransactionFlows.SWAP:
        from chat.swap_transactions import process_swap_transaction

        if transaction_request.step == SwapTransactionSteps.BUILD_SWAP_TX:
            transaction_request.state = TransactionStates.COMPLETED
            content = f"Swap has been completed and verified on the blockchain. Let the user know the same."
            transaction_request.step += 1
        else:
            await process_swap_transaction(transaction_request)
    elif transaction_request.flow == TransactionFlows.SILO_LENDING_DEPOSIT:
        from chat.silo_lending_txns import process_lend_transaction

        if transaction_request.step == SiloLendingDepositTxnSteps.DEPOSIT:
            transaction_request.state = TransactionStates.COMPLETED
            content = f"Lending transaction has been completed and verified on the blockchain. Let the user know the same."
            transaction_request.step += 1
        else:
            await process_lend_transaction(transaction_request)
    elif transaction_request.flow == TransactionFlows.SILO_LENDING_WITHDRAW:
        from chat.silo_lending_txns import process_withdraw_transaction

        if transaction_request.step == SiloLendingWithdrawTxnSteps.WITHDRAW:
            transaction_request.state = TransactionStates.COMPLETED
            content = f"Withdrawal transaction has been completed and verified on the blockchain. Let the user know the same."
            transaction_request.step += 1
        else:
            await process_withdraw_transaction(transaction_request)
    elif transaction_request.flow == TransactionFlows.STAKE_SONIC:
        from chat.stake_sonic_txn import process_stake_sonic_transaction

        if transaction_request.step == SonicStakeTxnSteps.STAKE:
            transaction_request.state = TransactionStates.COMPLETED
            content = f"Staking transaction has been completed and verified on the blockchain. Let the user know the same."
            transaction_request.step += 1
        else:
            await process_stake_sonic_transaction(transaction_request)
    else:
        raise ValueError("Unexpected transaction flow")

    if transaction_request.state == TransactionStates.COMPLETED:
        assert content is not None, "Content must be set for completed transactions"

        tools_responses = [
            {
                "role": "tool",
                "tool_call_id": conversation.messages[-1]["tool_calls"][0]["id"],
                "name": conversation.messages[-1]["tool_calls"][0]["function"]["name"],
                "content": content,
            }
        ]
        transaction_request.signed_tx_hash = signed_tx_hash
        transaction_request.tool_call_id = conversation.messages[-1]["tool_calls"][0][
            "id"
        ]
        conversation.messages.extend(tools_responses)

    # Wrap the transaction.atomic() block in sync_to_async
    @sync_to_async
    def save_transaction():
        with transaction.atomic():
            conversation.save()
            transaction_request.save()

    await save_transaction()

    if transaction_request.state == TransactionStates.COMPLETED:
        # Continue the conversation
        await get_completion(conversation)
        return False

    return True
