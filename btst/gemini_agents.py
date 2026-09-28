import json

from google import genai
from google.genai import types

from .agents import (CATALYST_SYSTEM, CATALYST_TOOL, MARKET_CONTEXT_SYSTEM, MARKET_CONTEXT_TOOL,
                     AgentError, catalyst_prompt, market_prompt)


class GeminiAgents:
    """Same agents as `Agents`, backed by Gemini with Google Search grounding and JSON-schema output."""

    def __init__(self, model: str):
        self.client = genai.Client()
        self.model = model

    def _run(self, system: str, prompt: str, schema: dict) -> dict:
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=f"{system}\n\nReturn your final answer as JSON matching the response schema.",
                tools=[types.Tool(google_search=types.GoogleSearch())],
                response_mime_type="application/json",
                response_json_schema=schema,
            ),
        )
        if not response.text:
            reason = response.candidates[0].finish_reason if response.candidates else response.prompt_feedback
            raise AgentError(f"Gemini returned no answer: {reason}")
        return json.loads(response.text)

    def market_context(self, index_snapshot: dict) -> dict:
        return self._run(MARKET_CONTEXT_SYSTEM, market_prompt(index_snapshot), MARKET_CONTEXT_TOOL["input_schema"])

    def catalysts(self, candidates: list[dict]) -> dict[str, dict]:
        result = self._run(CATALYST_SYSTEM, catalyst_prompt(candidates), CATALYST_TOOL["input_schema"])
        return {r["symbol"]: r for r in result["reviews"]}
