"""
Utility functions for Pocket Flow agents
Shared utilities to avoid circular imports
"""
from openai import OpenAI
import os

def call_llm(prompt: str, model: str = "gpt-4.1-nano-2025-04-14", temperature: float = 0.7, max_tokens: int = 2000) -> str:
    """Call OpenAI LLM with the given prompt"""
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content