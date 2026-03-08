"""
agent/minimax_brain.py
MiniMax M2 API integration — the AI brain of the agent
"""
import requests
import json
from config import MINIMAX_API_KEY, MINIMAX_GROUP_ID

API_URL = "https://api.minimax.chat/v1/text/chatcompletion_v2"

SYSTEM_PROMPT = """
You are an expert Indian stock market scalping agent trading NSE/BSE stocks.
You specialise in momentum strategies: EMA crossover, VWAP, RSI, Bollinger Bands.
Portfolio: Rs 10,000. Max risk per trade: Rs 200 (2%). Daily stop loss: Rs 500.
After Rs 500 daily profit, only accept signal scores of 9 or higher.
After Rs 800 daily profit, stop all new trades.
Always respond in valid JSON format only. No extra text, no markdown, no explanation.
"""


def ask_minimax(prompt: str, web_search: bool = False) -> str:
    """
    Send a prompt to MiniMax M2 and return the response text.
    Set web_search=True for pre-market analysis that needs live web data.
    """
    tools = []
    if web_search:
        tools = [{"type": "web_search_20250305", "name": "web_search"}]

    payload = {
        "model": "MiniMax-M1",
        "group_id": MINIMAX_GROUP_ID,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt}
        ],
        "tools": tools,
        "max_tokens": 2048,
        "temperature": 0.1   # Low temperature = consistent, predictable outputs
    }

    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        res = requests.post(API_URL, json=payload, headers=headers, timeout=30)
        res.raise_for_status()
        data = res.json()

        # Extract text from all content blocks (handles tool use responses)
        content_blocks = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if isinstance(content_blocks, list):
            text = " ".join(
                block.get("text", "") for block in content_blocks
                if block.get("type") == "text"
            )
        else:
            text = content_blocks

        return text.strip()

    except requests.exceptions.Timeout:
        print("MiniMax API timeout — using fallback")
        return "{}"
    except Exception as e:
        print(f"MiniMax API error: {e}")
        return "{}"


def parse_json_response(raw: str) -> dict:
    """Safely parse JSON from MiniMax response, stripping markdown if present."""
    try:
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        return json.loads(clean.strip())
    except Exception:
        return {}
