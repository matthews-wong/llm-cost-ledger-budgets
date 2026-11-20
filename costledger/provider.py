"""Provider seam: every model call goes through ``Provider.complete``."""

import math
from dataclasses import dataclass
from typing import Protocol

CHARS_PER_TOKEN = 4


@dataclass(frozen=True)
class Request:
    model: str
    prompt: str
    max_tokens: int = 256


@dataclass(frozen=True)
class Usage:
    input_tokens: int
    output_tokens: int


@dataclass(frozen=True)
class Response:
    text: str
    model: str
    usage: Usage


class Provider(Protocol):
    def complete(self, request: Request) -> Response: ...


def estimate_tokens(text: str) -> int:
    """Cheap character-based estimate; good enough to size a reservation."""
    return math.ceil(len(text) / CHARS_PER_TOKEN)


class FakeProvider:
    """Deterministic provider: the reply and usage are a function of the request."""

    def __init__(self, reply_tokens: int = 40) -> None:
        self.reply_tokens = reply_tokens
        self.calls = 0

    def complete(self, request: Request) -> Response:
        self.calls += 1
        output_tokens = min(self.reply_tokens, request.max_tokens)
        text = "x" * (output_tokens * CHARS_PER_TOKEN)
        usage = Usage(estimate_tokens(request.prompt), output_tokens)
        return Response(text=text, model=request.model, usage=usage)
