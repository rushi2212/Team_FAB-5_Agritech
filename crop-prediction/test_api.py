import json
import os
import sys
import time
from typing import Any, Dict

import requests


def _print_header(title: str):
    print("=" * 60)
    print(title)
    print("=" * 60)


def _pretty(data: Dict[str, Any]):
    print(json.dumps(data, indent=2, ensure_ascii=False))


def main():
    base_url = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
    url = f"{base_url.rstrip('/')}/recommend-crops"

    payload = {
        "city": os.getenv("TEST_CITY", "Ludhiana"),
        "soil_type": os.getenv("TEST_SOIL", "Alluvial Soil"),
    }

    _print_header("Testing /recommend-crops")
    print(f"URL: {url}")
    print(f"Payload: {payload}")

    attempts = 3
    last_error = None

    for i in range(1, attempts + 1):
        try:
            start = time.time()
            response = requests.post(url, json=payload, timeout=30)
            elapsed_ms = int((time.time() - start) * 1000)
            print(
                f"Attempt {i}: HTTP {response.status_code} ({elapsed_ms} ms)")

            response.raise_for_status()
            data = response.json()
            _pretty(data)
            return 0
        except requests.RequestException as exc:
            last_error = exc
            print(f"Attempt {i} failed: {exc}")
            time.sleep(1)

    print("All attempts failed. Ensure the API server is running: python -m uvicorn main:app --reload")
    if last_error:
        print(f"Last error: {last_error}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
