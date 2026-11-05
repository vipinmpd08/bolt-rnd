"""Pick the AI model from .env. Returns None when there is no key, so Bolt runs offline."""
import logging

from . import config

log = logging.getLogger("llm")


def make_llm():
    if config.LLM_PROVIDER == "groq" and config.GROQ_API_KEY:
        from langchain_openai import ChatOpenAI

        log.info("Brain: Groq (%s)", config.GROQ_MODEL)
        return ChatOpenAI(
            model=config.GROQ_MODEL, api_key=config.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1", temperature=0.8, timeout=30, max_retries=1,
            max_tokens=200,  # free tiers count this against a tokens-per-minute limit
        )
    if config.LLM_PROVIDER == "grok" and config.XAI_API_KEY:
        from langchain_openai import ChatOpenAI

        log.info("Brain: Grok (%s)", config.XAI_MODEL)
        return ChatOpenAI(
            model=config.XAI_MODEL, api_key=config.XAI_API_KEY,
            base_url="https://api.x.ai/v1", temperature=0.8, timeout=30, max_retries=1,
            max_tokens=200,  # free tiers count this against a tokens-per-minute limit
        )
    if config.LLM_PROVIDER == "claude" and config.ANTHROPIC_API_KEY:
        from langchain_anthropic import ChatAnthropic

        log.info("Brain: Claude (%s)", config.CLAUDE_MODEL)
        return ChatAnthropic(
            model=config.CLAUDE_MODEL, api_key=config.ANTHROPIC_API_KEY,
            temperature=0.8, timeout=30, max_retries=1, max_tokens=300,
        )
    log.warning("No API key for %r, Bolt runs offline with simple answers", config.LLM_PROVIDER)
    return None
