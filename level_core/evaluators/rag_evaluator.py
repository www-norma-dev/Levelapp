"""
RAG-specific evaluator for retrieval quality assessment.
Refactored to use GenerationService for expected answers and EvaluationService for judge.
"""
import os
import re
from typing import List, Dict, Optional
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from nltk.translate.meteor_score import meteor_score
from rouge_score import rouge_scorer

# LangChain imports for evaluation
from langchain.evaluation import EvaluatorType, load_evaluator
from langchain_openai import ChatOpenAI
from langchain_core.outputs import LLMResult

from level_core.entities.metric import RAGMetrics, LLMComparison
from level_core.simluators.event_collector import log_rag_event
from level_core.generators.service import GenerationService
from level_core.evaluators.service import EvaluationService

# RAG Evaluation Constants
JUDGE_STRONG_THRESHOLD = 4  # Score threshold for strong agreement
JUDGE_TIE_SCORE = 3         # Score indicating neutral/tie result

# Missing facts extraction keywords and pattern
_MISSING_KEYWORDS = {"missing", "lacks", "absent", "not mentioned", "omits", "excludes"}
_MISSING_PATTERN = re.compile(r'\b(?:missing|lacks|absent|omits|excludes|not mentioned|fails to mention)\b', re.IGNORECASE)


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
    
    def _init_llm(self) -> Optional[ChatOpenAI]:
        """
        Initialize LLM based on judge provider.
        
        Returns:
            ChatOpenAI instance if OpenAI provider, None otherwise
        """
        if self.judge_provider == "openai":
            return ChatOpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                model="gpt-4o-mini",
                temperature=0.1
            )
        return None
        
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
        
        # Tokenize once and reuse (optimization)
        expected_tokens = expected.split()
        actual_tokens = actual.split()
        
        # BLEU Score
        smooth = SmoothingFunction().method1
        bleu = sentence_bleu(
            [expected_tokens],
            actual_tokens,
            smoothing_function=smooth
        )
        
        # ROUGE-L F1 - use rouge_scorer library with original strings
        scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
        scores = scorer.score(expected, actual)
        rouge_l_f1 = scores["rougeL"].fmeasure
        
        # METEOR Score
        try:
            meteor = meteor_score([expected_tokens], actual_tokens)
        except Exception:
            # Fallback to token overlap using pre-tokenized data
            ref_tokens_set = set(expected_tokens)
            cand_tokens_set = set(actual_tokens)
            overlap = len(ref_tokens_set & cand_tokens_set)
            meteor = 2 * overlap / (len(ref_tokens_set) + len(cand_tokens_set)) if (ref_tokens_set and cand_tokens_set) else 0.0
        
        # BERTScore - placeholder for now
        bertscore_f1 = 0.0

        return RAGMetrics(
            bleu_score=bleu,
            rouge_l_f1=rouge_l_f1,
            meteor_score=meteor,
            bertscore_f1=bertscore_f1,
        )
    
    async def compare_answers(
        self, 
        prompt: str, 
        expected: str, 
        actual: str
    ) -> LLMComparison:
        """
        Use LangChain's evaluation chain to compare expected vs actual answers.
        
        Args:
            prompt: Original user question
            expected: Expected answer
            actual: Actual chatbot answer
            
        Returns:
            LLMComparison with judgment and missing facts
        """
        log_rag_event("INFO", "Performing LangChain evaluation comparison")
        
        try:
            # Initialize LLM based on judge provider
            llm = self._init_llm()
            if not llm:
                # Fallback to manual evaluation for non-OpenAI providers
                return await self._fallback_comparison(prompt, expected, actual)
            
            # Create evaluation input
            eval_input = {
                "input": prompt,
                "prediction": actual,
                "reference": expected
            }
            
            # Load and run LangChain evaluators using loop (DRY optimization)
            criteria = ["relevance", "completeness"]
            criteria_results = {}
            
            for criterion in criteria:
                evaluator = load_evaluator(
                    EvaluatorType.CRITERIA,
                    llm=llm,
                    criteria=[criterion]
                )
                result = await evaluator.aevaluate_strings(**eval_input)
                criteria_results[criterion] = result
            
            # Calculate combined score and justification
            scores = [result.get("score", 0) for result in criteria_results.values()]
            avg_score = sum(scores) / len(scores) if scores else 0.0
            
            # Determine better answer based on combined scores
            if avg_score >= 0.8:  # High threshold for chatbot being better
                better = "chatbot"
            elif avg_score >= 0.6:  # Medium threshold for tie
                better = "tie"
            else:
                better = "expected"
            
            # Combine justifications (using .get() for safety)
            justification = "\n".join(
                f"{criterion.capitalize()}: {criteria_results.get(criterion, {}).get('reasoning', 'No reasoning provided')}"
                for criterion in criteria
            )
            
            # Extract missing facts from completeness reasoning
            completeness_reasoning = criteria_results.get("completeness", {}).get("reasoning", "")
            missing_facts = self._extract_missing_facts(completeness_reasoning)
            
            log_rag_event("INFO", f"LangChain evaluation completed: {better} (avg_score: {avg_score:.2f})")
            
            return LLMComparison(
                better_answer=better,
                justification=justification,
                missing_facts=missing_facts,
            )
            
        except Exception as e:
            log_rag_event("ERROR", f"LangChain evaluation failed: {e}")
            # Fallback to manual evaluation
            return await self._fallback_comparison(prompt, expected, actual)
    
    async def _fallback_comparison(
        self, 
        prompt: str, 
        expected: str, 
        actual: str
    ) -> LLMComparison:
        """
        Fallback to manual evaluation when LangChain evaluation fails.
        
        Args:
            prompt: Original user question
            expected: Expected answer
            actual: Actual chatbot answer
            
        Returns:
            LLMComparison with judgment and missing facts
        """
        log_rag_event("INFO", "Using fallback manual evaluation")
        
        try:
            self._ensure_eval()
            # Use existing EvaluationService logic
            res = await self._eval.evaluate_response(
                provider=self.judge_provider, output_text=actual, reference_text=expected
            )
            # Map to LLMComparison using thresholds
            score = getattr(res, "match_level", 0)
            if score >= JUDGE_STRONG_THRESHOLD:
                better = "chatbot"
            elif score == JUDGE_TIE_SCORE:
                better = "tie"
            else:
                better = "expected"
                
            return LLMComparison(
                better_answer=better,
                justification=res.justification or "",
                missing_facts=getattr(res, "metadata", {}).get("missing_facts", []),
            )
        except Exception as e:
            log_rag_event("ERROR", f"Fallback evaluation failed: {e}")
            return LLMComparison(
                better_answer="tie",
                justification=f"Evaluation error: {str(e)}",
                missing_facts=[],
            )
    
    def _extract_missing_facts(self, reasoning: str) -> List[str]:
        """Extract missing facts from evaluation reasoning."""
        if not reasoning:
            return []
        
        return [
            (line.split(':', 1)[1].strip() if ':' in line else line.strip())
            for line in reasoning.splitlines() 
            if line.strip() and _MISSING_PATTERN.search(line)
        ][:5]