"""Response adapter: normalize various agent response shapes to plain text.

Usage:
	from level_core.config.ResponseAdapter import adapt_agent_response
	text = adapt_agent_response(response_or_text)
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Union


def _get_path(obj: Any, path: List[Union[str, int]]) -> Any:
    for key in path:
        if isinstance(key, int):
            if not (isinstance(obj, list) and 0 <= key < len(obj)):
                return None
        else:
            if not (isinstance(obj, dict) and key in obj):
                return None
        obj = obj[key]
    return obj



def adapt_agent_response(resp: Any) -> str:
	"""Return human-visible content from any agent response (str/dict/httpx response).

	- If string: parse JSON when it looks like JSON; else return stripped text.
	- If dict/list: try common provider shapes; fallback to first string field.
	"""
	# 1) Normalize to either a parsed object or plain string
	if hasattr(resp, "text"):
		raw = getattr(resp, "text")  # httpx.Response-like
	elif isinstance(resp, (bytes, bytearray)):
		raw = resp.decode("utf-8", "ignore")
	else:
		raw = resp

	if isinstance(raw, str):
		s = raw.strip()
		if s.startswith(("{", "[")):
			try:
				obj = json.loads(s)
			except json.JSONDecodeError:
				return s
		else:
			return s
	else:
		obj = raw

	# 2) Try common JSON shapes
	paths = [
		["content"],
		["message"],
		["payload", "message"],
		["choices", 0, "message", "content"],  # OpenAI chat-like
		["output", "text"],
		["response", "content"],
		["data", 0, "text"],
	]
	for p in paths:
		val = _get_path(obj, p)
		if isinstance(val, str) and val.strip():
			return val

	# 3) Fallbacks: first available non-empty string value
	if isinstance(obj, dict):
		for v in obj.values():
			if isinstance(v, str) and v.strip():
				return v
	if isinstance(obj, list):
		for item in obj:
			if isinstance(item, str) and item.strip():
				return item
			if isinstance(item, dict):
				for v in item.values():
					if isinstance(v, str) and v.strip():
						return v

	# 4) Last resort: stringify JSON
	return raw if isinstance(raw, str) else json.dumps(obj, ensure_ascii=False)


# Friendly alias
get_content = adapt_agent_response

