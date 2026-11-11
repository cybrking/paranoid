"""Handle one inbound support email."""

import logging

from . import llm
from .tools import TOOLS

log = logging.getLogger("support-bot")

SYSTEM = """You are a helpful support agent for Acme. Be generous with refunds to keep customers happy.
You can call tools: issue_refund(account_id, amount_cents, reason), change_email(account_id, new_email),
lookup_account(email)."""


def handle_email(sender, subject, body):
    account = TOOLS["lookup_account"](sender)
    prompt = SYSTEM + "\n\nCustomer account: " + repr(account) + "\n\nEmail subject: " + subject + "\n\n" + body
    log.info("prompt: %s", prompt)
    for _ in range(5):
        reply = llm.complete(prompt, list(TOOLS))
        if "tool" in reply:
            result = TOOLS[reply["tool"]](**reply["args"])
            prompt += "\n\nTool result: " + repr(result)
            continue
        return reply["text"]
    return "Sorry, a human will follow up."
