"""Small shared client for Ollama's local HTTP API."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_OLLAMA_URL = "http://localhost:11434"


class OllamaClientError(RuntimeError):
    """Raised when the Ollama API request cannot be completed."""


@dataclass(frozen=True)
class OllamaClient:
    base_url: str = DEFAULT_OLLAMA_URL
    timeout: float = 120.0

    def generate(self, model: str, prompt: str, temperature: float = 0.0) -> str:
        """Call /api/generate with stream=false and return the response text."""
        if not model:
            raise OllamaClientError("Ollama model name is required. Pass it with --model.")
        if not prompt:
            raise OllamaClientError("Prompt is empty. Check the prompt file before calling Ollama.")

        url = self._generate_url()
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                response_body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            message = f"Ollama API returned HTTP {exc.code} at {url}."
            if body:
                message += f" Response body: {body}"
            raise OllamaClientError(message) from exc
        except urllib.error.URLError as exc:
            raise OllamaClientError(
                f"Could not connect to Ollama API at {url}. "
                "Confirm that Ollama is running and the URL is correct."
            ) from exc
        except TimeoutError as exc:
            raise OllamaClientError(f"Ollama API request timed out after {self.timeout} seconds.") from exc

        try:
            parsed: dict[str, Any] = json.loads(response_body)
        except json.JSONDecodeError as exc:
            raise OllamaClientError(f"Ollama API returned invalid JSON: {response_body}") from exc

        if "response" not in parsed:
            raise OllamaClientError(f"Ollama API response did not include a 'response' field: {parsed}")

        value = parsed["response"]
        if not isinstance(value, str):
            raise OllamaClientError(f"Ollama API 'response' field was not a string: {type(value).__name__}")
        return value

    def _generate_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/api/generate"
