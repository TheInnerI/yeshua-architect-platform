"""
Yeshua Architect Platform — OpenRouter Live Agent Service

Lets users chat with their AI agents in the browser.
Uses OpenRouter API with model selection.
"""

import logging
import os
import httpx
from typing import Optional

logger = logging.getLogger("yeshua-agent")

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# OpenRouter API key from env
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# Model options — free and paid
MODELS = {
    # Free tier
    "owl-alpha": {"id": "openrouter/owl-alpha", "name": "Owl Alpha (free)", "cost": "free"},
    "llama-3.1-8b": {"id": "meta-llama/llama-3.1-8b-instruct:free", "name": "Llama 3.1 8B (free)", "cost": "free"},
    "mistral-7b": {"id": "mistralai/mistral-7b-instruct:free", "name": "Mistral 7B (free)", "cost": "free"},
    # Paid tiers
    "gpt-4o-mini": {"id": "openai/gpt-4o-mini", "name": "GPT-4o Mini", "cost": "paid"},
    "claude-sonnet-4": {"id": "anthropic/claude-sonnet-4", "name": "Claude Sonnet 4", "cost": "paid"},
    "gpt-4o": {"id": "openai/gpt-4o", "name": "GPT-4o", "cost": "premium"},
}

# Tier-based model access
TIER_MODELS = {
    "free": ["owl-alpha", "llama-3.1-8b", "mistral-7b"],
    "starter": ["owl-alpha", "llama-3.1-8b", "mistral-7b", "gpt-4o-mini"],
    "pro": ["owl-alpha", "llama-3.1-8b", "mistral-7b", "gpt-4o-mini", "claude-sonnet-4"],
    "full": ["owl-alpha", "llama-3.1-8b", "mistral-7b", "gpt-4o-mini", "claude-sonnet-4", "gpt-4o"],
}


class AgentService:
    """Run live agent chats via OpenRouter."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or OPENROUTER_API_KEY

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def get_available_models(self, tier: str = "free") -> list[dict]:
        """Get models available for a user's tier."""
        model_keys = TIER_MODELS.get(tier, TIER_MODELS["free"])
        return [MODELS[k] for k in model_keys if k in MODELS]

    async def chat(
        self,
        agent_prompt: str,
        user_message: str,
        model_key: str = "owl-alpha",
        conversation_history: list[dict] = None,
        max_tokens: int = 1000,
    ) -> dict:
        """
        Send a message to an agent and get a response.

        Args:
            agent_prompt: The agent's system prompt (from .md file)
            user_message: User's message
            model_key: Model key from MODELS dict
            conversation_history: Previous messages

        Returns:
            dict with: response, model, usage
        """
        if not self.is_configured:
            raise ValueError("OpenRouter API key not configured")

        if model_key not in MODELS:
            model_key = "owl-alpha"

        model = MODELS[model_key]

        # Build messages
        messages = [{"role": "system", "content": agent_prompt}]
        if conversation_history:
            messages.extend(conversation_history[-10:])  # Last 10 messages
        messages.append({"role": "user", "content": user_message})

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://architect.innerinetcompany.com",
            "X-Title": "Yeshua Architect Platform",
        }

        payload = {
            "model": model["id"],
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(OPENROUTER_API_URL, headers=headers, json=payload)

            if resp.status_code != 200:
                logger.error("OpenRouter error %s: %s", resp.status_code, resp.text[:500])
                raise Exception(f"OpenRouter returned {resp.status_code}: {resp.text[:200]}")

            data = resp.json()
            text = data["choices"][0]["message"]["content"]

            return {
                "response": text,
                "model": model["name"],
                "usage": data.get("usage", {}),
            }


# Singleton
_agent_service: Optional[AgentService] = None


def get_agent_service(api_key: str = None) -> AgentService:
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService(api_key=api_key)
    return _agent_service
