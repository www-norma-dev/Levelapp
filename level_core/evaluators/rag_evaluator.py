"""
RAG-specific evaluator for retrieval quality assessment.
Refactored to use GenerationService for expected answers and EvaluationService for judge.
"""
import os
from typing import List, Dict, Optional
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from nltk.translate.meteor_score import meteor_score

from level_core.entities.metric import RAGMetrics, LLMComparison
from level_core.simluators.event_collector import log_rag_event
from level_core.generators.service import GenerationService
from level_core.evaluators.service import EvaluationService


class RAGEvaluator:
    """
    Evaluator for RAG retrieval quality using NLP metrics and LLM-as-judge.
    """
    
    def __init__(self, generation_service: GenerationService | None = None, evaluation_service: EvaluationService | None = None, expected_model: Optional[str] = None, judge_provider: Optional[str] = None):
        """Initialize RAG evaluator with services.

        Args:
            generation_service: Service used to generate expected answers.
            evaluation_service: Service used to perform LLM-as-judge.
            expected_model: Model to use for expected answers (when generation provider is OpenAI).
            judge_provider: Provider key for the judge (e.g., 'openai' or 'ionos').
        """
        self._gen = generation_service
        self._eval = evaluation_service
        self.expected_model = expected_model or os.getenv("LEVELAPP_EXPECTED_MODEL", "gpt-4o-mini")
        self.judge_provider = (judge_provider or os.getenv("LEVELAPP_JUDGE_PROVIDER", "openai")).lower()

    def _ensure_gen(self) -> None:
        if self._gen is None:
            raise ValueError("GenerationService not set for RAGEvaluator")
    
    def _ensure_eval(self) -> None:
        if self._eval is None:
            raise ValueError("EvaluationService not set for RAGEvaluator")
        
    async def generate_expected_answer(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate expected answer using GPT-4 from selected chunks.
        
        Args:
            messages: List of messages with system context and user prompt
            
        Returns:
            Generated expected answer
        """
        log_rag_event("INFO", "Generating expected answer")
        self._ensure_gen()
        # Log a safe prompt preview
        try:
            preview = messages[-1]["content"][:400] if messages else ""
            log_rag_event("INFO", f"EXPECTED_ANSWER_CALL model={self.expected_model}, preview={preview}...")
        except Exception:
            pass
        text = await self._gen.generate(provider="openai", messages=messages, model=self.expected_model)
        log_rag_event("INFO", f"EXPECTED_ANSWER_RESPONSE length={len(text)}")
        return text
    
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
        
        # BERTScore - placeholders for now
        bertscore_precision = 0.0
        bertscore_recall = 0.0
        bertscore_f1 = 0.0

        return RAGMetrics(
            bleu_score=bleu,
            rouge_l_f1=rouge_l_f1,
            meteor_score=meteor,
            bertscore_precision=bertscore_precision,
            bertscore_recall=bertscore_recall,
            bertscore_f1=bertscore_f1,
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
            self._ensure_eval()
            # Delegate to EvaluationService using configured judge_provider
            res = await self._eval.evaluate_response(
                provider=self.judge_provider, output_text=actual, reference_text=expected
            )
            # Map to LLMComparison; thresholded interpretation:
            #  - score >= 4: chatbot answer is strong
            #  - score == 3: tie
            #  - score < 3: expected is better
            score = getattr(res, "match_level", 0)
            if score >= 4:
                better = "chatbot"
            elif score == 3:
                better = "tie"
            else:
                better = "expected"
            # missing_facts are not yet produced by evaluators; return explicit marker
            return LLMComparison(
                better_answer=better,
                justification=res.justification or "",
                missing_facts=["No missing facts extracted by judge"]
                if better != "chatbot" and not getattr(res, "metadata", {}).get("missing_facts")
                else getattr(res, "metadata", {}).get("missing_facts", []),
            )
        except Exception as e:
            log_rag_event("ERROR", f"LLM comparison failed: {e}")
            return LLMComparison(
                better_answer="tie",
                justification=f"LLM comparison error: {str(e)}",
                missing_facts=[],
            )