"""
OpenRouter LLM Tool — OpenAI-compatible API wrapper
Supports streaming, retry, and structured JSON output.
"""
import json
import time
from typing import Optional
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from rich.console import Console

from config.settings import settings

console = Console()


class LLMTool:
    """Wrapper around OpenRouter's OpenAI-compatible API."""

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
        )
        self.model = settings.OPENROUTER_MODEL
        self.default_headers = {
            "HTTP-Referer": "https://crowdwisdomtrading.com",
            "X-Title": "CrowdWisdom Video Ad Agent",
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
    )
    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        model: Optional[str] = None,
    ) -> str:
        """Send a completion request and return the response text."""
        response = self.client.chat.completions.create(
            model=model or self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            extra_headers=self.default_headers,
        )
        return response.choices[0].message.content or ""

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        model: Optional[str] = None,
    ) -> dict:
        """Request structured JSON output from the LLM."""
        json_prompt = (
            user_prompt
            + "\n\nIMPORTANT: Respond ONLY with valid JSON. No markdown, no explanation, just the JSON object."
        )
        raw = self.complete(
            system_prompt=system_prompt,
            user_prompt=json_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
        )
        # Strip markdown code fences if present
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        if raw.endswith("```"):
            raw = raw[: raw.rfind("```")]
        return json.loads(raw.strip())


# Singleton
llm = LLMTool()
