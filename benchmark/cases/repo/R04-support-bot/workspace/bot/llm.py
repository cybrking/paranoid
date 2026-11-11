"""Client for our model provider. Returns either text or a tool call."""


def complete(prompt, tools):
    """Send prompt to the model with the tool list. Returns {"text": str} or {"tool": name, "args": dict}."""
    raise NotImplementedError("wired up in production")
