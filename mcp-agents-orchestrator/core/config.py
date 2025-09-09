import os
from dataclasses import dataclass


@dataclass
class AIConfig:
    agent_request_timeout: float = float(os.getenv("AGENT_TIMEOUT_SECS", "120"))


@dataclass
class Config:
    ai: AIConfig = AIConfig()


_CFG = Config()


def get_config() -> Config:
    return _CFG

