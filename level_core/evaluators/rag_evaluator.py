"""
RAG-specific evaluator for retrieval quality assessment.
"""
import asyncio
import os
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from nltk.translate.meteor_score import meteor_score
from typing import List, Dict, Any
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment variables from .env file
load_dotenv()

from level_core.simluators.rag_schemas import RAGMetrics, LLMComparison
from level_core.simluators.event_collector import log_rag_event

class RAGEvaluator:
    """
    Evaluator for RAG retrieval quality using NLP metrics and LLM-as-judge.
    """
    
    def __init__(self):
        """Initialize RAG evaluator with OpenAI configuration."""
        self._client: AsyncOpenAI | None = None  # Lazy init
        # Allow overriding model via env
        self.expected_model = os.getenv("LEVELAPP_EXPECTED_MODEL", "gpt-4o-mini")

    def _get_openai_client(self) -> AsyncOpenAI:
        """Lazy load OpenAI client with current API key."""
        if self._client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                log_rag_event("ERROR", "OPENAI_API_KEY not found in environment variables")
                raise ValueError("OPENAI_API_KEY not found in environment variables")
            # AsyncOpenAI reads api_key from env implicitly, but pass explicitly for clarity
            self._client = AsyncOpenAI(api_key=api_key)
        return self._client
        
    async def generate_expected_answer(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate expected answer using GPT-4 from selected chunks.
        
        Args:
            messages: List of messages with system context and user prompt
            
        Returns:
            Generated expected answer
        """
        log_rag_event("INFO", "Generating expected answer with OpenAI")
        
        try:
            client = self._get_openai_client()
            # Log a safe prompt preview
            try:
                preview = messages[-1]["content"][:400] if messages else ""
                log_rag_event("INFO", f"EXPECTED_ANSWER_CALL model={self.expected_model}, preview={preview}...")
            except Exception:
                pass

            response = await client.chat.completions.create(
                model=self.expected_model,
                messages=messages,
                temperature=0.0,
                max_tokens=512,
            )
            text = (response.choices[0].message.content or "").strip()
            finish = getattr(response.choices[0], "finish_reason", "unknown")
            log_rag_event("INFO", f"EXPECTED_ANSWER_RESPONSE finish_reason={finish}, length={len(text)}")
            return text
        except Exception as e:
            log_rag_event("ERROR", f"Failed to generate expected answer: {e}")
            raise
    
    async def compute_metrics(self, expected: str, actual: str) -> RAGMetrics:
        """
        Compute NLP metrics between expected and actual answers.
        
        Args:
            expected: Expected answer
            actual: Actual chatbot answer
            
        Returns:
            RAGMetrics with all computed scores
        """
        log_rag_event("INFO", "Computing NLP metrics")
        
        # BLEU Score
        smooth = SmoothingFunction().method1
        bleu = sentence_bleu(
            [expected.split()],
            actual.split(),
            smoothing_function=smooth
        )
        
        # ROUGE-L F1
        rouge_l_f1 = self._compute_rouge_l(expected, actual)
        
        # METEOR Score
        try:
            meteor = meteor_score(
                [expected.split()],
                actual.split()
            )
        except Exception:
            # Fallback to token overlap
            ref_tokens = set(expected.split())
            cand_tokens = set(actual.split())
            overlap = len(ref_tokens & cand_tokens)
            meteor = 2 * overlap / (len(ref_tokens) + len(cand_tokens)) if (ref_tokens and cand_tokens) else 0.0
        
        # BERTScore - always set to 0.0 for now
        bertscore_precision = 0.0
        bertscore_recall = 0.0
        bertscore_f1 = 0.0
        
        return RAGMetrics(
            bleu_score=bleu,
            rouge_l_f1=rouge_l_f1,
            meteor_score=meteor
            # bertscore_precision=bertscore_precision,
            # bertscore_recall=bertscore_recall,
            # bertscore_f1=bertscore_f1
        )
    
    def _compute_rouge_l(self, reference: str, hypothesis: str) -> float:
        """
        Compute ROUGE-L F1 score (word-level LCS).
        
        Args:
            reference: Reference text
            hypothesis: Hypothesis text
            
        Returns:
            ROUGE-L F1 score
        """
        ref_w = reference.split()
        hyp_w = hypothesis.split()
        m, n = len(ref_w), len(hyp_w)
        
        # DP table for LCS
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(m):
            for j in range(n):
                if ref_w[i] == hyp_w[j]:
                    dp[i + 1][j + 1] = dp[i][j] + 1
                else:
                    dp[i + 1][j + 1] = max(dp[i][j + 1], dp[i + 1][j])
        
        lcs_len = dp[m][n]
        
        # Precision, Recall, F1
        prec = lcs_len / n if n > 0 else 0.0
        rec = lcs_len / m if m > 0 else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        
        return f1
    
    async def compare_answers(
        self, 
        prompt: str, 
        expected: str, 
        actual: str
    ) -> LLMComparison:
        """
        Use LLM-as-judge to compare expected vs actual answers.
        
        Args:
            prompt: Original user question
            expected: Expected answer
            actual: Actual chatbot answer
            
        Returns:
            LLMComparison with judgment and missing facts
        """
        log_rag_event("INFO", "Performing LLM-as-judge comparison")
        
        judge_system = "You are an expert evaluator of answer relevance and completeness."
        judge_user = f"""
Query:
"{prompt}"

Expected Answer (human-curated):
"{expected}"

Chatbot Answer:
"{actual}"

Compare the two answers and decide which one better addresses the Query in terms of:
  1. Factual relevance,
  2. Completeness of information,
  3. Faithfulness to the source context.

Do NOT output any numeric score. Instead, return a JSON object with these fields:
  - "better_answer": one of ["expected", "chatbot", "tie"]
  - "justification": a concise explanation that includes bullet-point lines of any factual statements from the Expected Answer that are missing or incorrect in the Chatbot Answer
  - "missing_facts": a list of the exact factual statements present in the Expected Answer that are missing from the Chatbot Answer

Format example:
{{
  "better_answer": "expected",
  "justification": "- Fact A is missing\\n- Fact B is incorrect\\nOverall explanation...",
  "missing_facts": ["Fact A", "Fact B"]
}}

Respond with only the JSON object.
"""
        
        try:
            client = self._get_openai_client()
            response = await client.chat.completions.create(
                model=self.expected_model,
                messages=[
                    {"role": "system", "content": judge_system},
                    {"role": "user", "content": judge_user}
                ],
                temperature=0.0,
                max_tokens=512,
            )
            
            raw_response = response.choices[0].message.content.strip()
            
            # Parse JSON response
            import json
            try:
                verdict = json.loads(raw_response)
                return LLMComparison(
                    better_answer=verdict.get("better_answer", "tie"),
                    justification=verdict.get("justification", ""),
                    missing_facts=verdict.get("missing_facts", [])
                )
            except json.JSONDecodeError:
                log_rag_event("ERROR", f"Invalid JSON from LLM: {raw_response}")
                return LLMComparison(
                    better_answer="tie",
                    justification=f"LLM comparison failed. Raw response: {raw_response}",
                    missing_facts=[]
                )
                
        except Exception as e:
            log_rag_event("ERROR", f"LLM comparison failed: {e}")
            return LLMComparison(
                better_answer="tie",
                justification=f"LLM comparison error: {str(e)}",
                missing_facts=[]
            )