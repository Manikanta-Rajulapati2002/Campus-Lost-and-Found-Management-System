import json
import requests
from datetime import date


OLLAMA_API_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL_NAME = "llama3"  # or any model you pulled


def parse_nl_query_to_filters(nl_query: str) -> dict:
    """
    Call Ollama to convert natural language into structured filters.
    The LLM MUST return JSON only.
    """
    system_prompt = """
You are a strict JSON API that converts natural language lost & found queries
into structured search filters for a campus Lost & Found system.

You MUST respond with ONLY valid JSON. No explanations, no extra text.

JSON format:
{
  "keyword": string or null,
  "category": string or null,
  "color": string or null,
  "location": string or null,
  "item_type": "lost" or "found" or null,
  "start_date": "YYYY-MM-DD" or null,
  "end_date": "YYYY-MM-DD" or null
}

Rules:
- If the user mentions "lost", item_type = "lost".
- If the user mentions "found" or "turned in", item_type = "found".
- If not clear, item_type = null.
- If time expressions like "yesterday", "last week", "today" etc. appear,
  convert them into an approximate date or date range.
- If you are unsure about dates, set start_date and end_date to null.
- If any field is not specified, use null for that field.
"""

    payload = {
        "model": OLLAMA_MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": nl_query},
        ],
        "stream": False,
    }

    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        content = data["message"]["content"]

        # content should be JSON text
        filters = json.loads(content)

        # Basic sanity check: ensure all keys exist
        expected_keys = [
            "keyword",
            "category",
            "color",
            "location",
            "item_type",
            "start_date",
            "end_date",
        ]
        for key in expected_keys:
            filters.setdefault(key, None)

        return filters

    except Exception as e:
        # In case of any error, return "no filters" so we don't break the app
        print("Error calling Ollama:", e)
        return {
            "keyword": None,
            "category": None,
            "color": None,
            "location": None,
            "item_type": None,
            "start_date": None,
            "end_date": None,
        }
