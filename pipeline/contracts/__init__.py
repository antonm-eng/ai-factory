import json
from pathlib import Path

CONTRACTS_DIR = Path(__file__).parent


def load_contract(name: str) -> dict:
    return json.loads((CONTRACTS_DIR / f"{name}.json").read_text())
