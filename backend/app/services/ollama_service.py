from typing import Any

import httpx

from app.core.response_sanitizer import sanitize_model_response


class OllamaService:
    """
    Handles communication between AURA and the local Ollama server.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        timeout: float = 180.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def health_check(self) -> bool:
        try:
            response = httpx.get(
                f"{self.base_url}/api/tags",
                timeout=self.timeout,
            )
            return response.status_code == 200

        except httpx.HTTPError:
            return False

    def list_models(self) -> list[dict[str, Any]]:
        response = httpx.get(
            f"{self.base_url}/api/tags",
            timeout=self.timeout,
        )

        response.raise_for_status()

        data = response.json()

        models = []

        for model in data.get("models", []):
            models.append(
                {
                    "name": model.get("name"),
                    "model": model.get("model"),
                    "size": model.get("size"),
                    "modified_at": model.get("modified_at"),
                    "details": model.get("details", {}),
                }
            )

        return models

    def generate(
        self,
        model: str,
        prompt: str,
        system_prompt: str | None = None,
        think: bool = False,
    ) -> dict[str, Any]:

        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "think": think,
        }

        if system_prompt:
            payload["system"] = system_prompt

        response = httpx.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=self.timeout,
        )

        response.raise_for_status()

        data = response.json()

        raw_response = data.get("response", "")

        clean_response = sanitize_model_response(
            raw_response
        )

        return {
            "model": data.get("model", model),
            "response": clean_response,
            "thinking": data.get("thinking"),
            "done": data.get("done", False),
            "total_duration": data.get("total_duration"),
            "load_duration": data.get("load_duration"),
            "prompt_eval_count": data.get("prompt_eval_count"),
            "eval_count": data.get("eval_count"),
            "eval_duration": data.get("eval_duration"),
        }
