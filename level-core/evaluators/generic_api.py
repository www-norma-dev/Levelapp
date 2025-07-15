import httpx
from typing import Dict, Any
from evaluators.base import BaseEvaluator
from evaluators.schemas import EvaluationConfig

def get_by_path(obj: dict, path: str):
    """Accès dans un dict par chemin JSON style 'a.b.0.c'."""
    for part in path.split("."):
        if part.isdigit():
            obj = obj[int(part)]
        else:
            obj = obj.get(part)
    return obj

class GenericAPIEvaluator(BaseEvaluator):
    def __init__(self, config, logger):
        super().__init__(config)
        self.logger = logger
    """
    Generic evaluator that supports any provider via API + headers + config.
    """

    def build_prompt(self, generated: str, expected: str) -> str:
        return f"""
        Evaluate how well the generated text matches the expected reference.

        Expected:
        \"\"\"{expected}\"\"\"

        Generated:
        \"\"\"{generated}\"\"\"

        Respond with a JSON:
        {{
            "match_level": 0 to 3,
            "justification": "..."
        }}
        """

    async def call_llm(self, prompt: str) -> Dict[str, Any]:
        try:
            payload = {
                "model": self.config.model_id,
                "messages": [
                    {"role": "system", "content": "You are a helpful evaluation assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": self.config.llm_config.get("temperature", 0),
                "max_tokens": self.config.llm_config.get("max_tokens", 256)
            }

            headers = self.config.extra.get("headers", {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            })

            async with httpx.AsyncClient(timeout=60) as client:
                res = await client.post(
                    self.config.api_url,
                    headers=headers,
                    json=payload
                )
                res.raise_for_status()
                content = get_by_path(res.json(), self.config.extra.get("output_path", "choices.0.message.content"))
                
                from evaluators.base import BaseEvaluator
                parsed = BaseEvaluator._parse_json_output(content)
                return parsed

        except Exception as e:
            return {"error": str(e)}
