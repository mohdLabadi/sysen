import os
from pathlib import Path

from dotenv import load_dotenv


def load_env_from_dotenv() -> None:
    """Load environment variables from a local .env file if it exists."""
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        # Fallback to default behavior: do nothing if .env is missing
        pass

