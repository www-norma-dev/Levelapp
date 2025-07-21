"""
ResultsExporter class for exporting evaluation results to various formats.
Handles JSON export with comprehensive scenario information.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from ..config import Config

logger = logging.getLogger(__name__)

class ResultsExporter:
    """Handles exporting evaluation results to various formats."""
    
    def __init__(self, config: Config):
        """
        Initialize ResultsExporter with configuration.
        
        Args:
            config: Configuration object with output settings
        """
        self.config = config
        self.logger = logger
    
    def export_scenario_to_json(
        self, 
        evaluation_results: Dict[str, Any], 
        rag_url: str = None,
        output_file: str = None
    ) -> Dict[str, Any]:
        """
        Export evaluation results to a structured JSON format with all scenario interactions.
        
        Args:
            evaluation_results: Results from evaluate_chatbot_conversation
            rag_url: URL where the chatbot gets information from
            output_file: Optional file path to save the JSON (if None, returns dict only)
            
        Returns:
            Structured JSON with all interactions and metadata
        """
        # Extract basic info
        detailed_results = evaluation_results["detailed_results"]
        summary = evaluation_results["summary"]
        metadata = evaluation_results["evaluation_metadata"]
        
        # Create scenario structure
        scenario_json = {
            "scenario_metadata": {
                "scenario_id": f"scenario_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "timestamp": datetime.now().isoformat(),
                "rag_source_url": rag_url or "Unknown",
                "total_interactions": summary["total_turns"],
                "average_score": summary["average_score"],
                "success_rate": summary["success_rate"],
                "evaluator_type": metadata["evaluator_type"],
                "model_used": metadata["model_used"]
            },
            
            "scenario_summary": {
                "score_distribution": {
                    "excellent_responses": summary["excellent_responses"],
                    "good_responses": summary["good_responses"], 
                    "fair_responses": summary["fair_responses"],
                    "poor_responses": summary["poor_responses"]
                },
                "overall_performance": {
                    "total_score": summary["total_turns"] * summary["average_score"] if summary["total_turns"] > 0 else 0,
                    "max_possible_score": summary["total_turns"] * 3,
                    "success_rate_percentage": summary["success_rate"]
                }
            },
            
            "interactions": []
        }
        
        # Add each interaction with all requested fields
        for result in detailed_results:
            interaction = {
                "interaction_id": f"interaction_{result['turn']}",
                "turn_number": result["turn"],
                
                # Core data fields
                "rag_source_url": rag_url or "Unknown",
                "user_prompt": result["user_prompt"],
                "chatbot_reply": result["bot_reply"],
                "reference": result["user_prompt"],  # Using user prompt as reference
                "evaluation_score": result["evaluation_score"],
                "judgement": result["justification"],
                
                # Additional metadata
                "status": result["status"],
                "metadata": result.get("metadata", {}),
                "evaluation_timestamp": datetime.now().isoformat()
            }
            
            scenario_json["interactions"].append(interaction)
        
        # Save to file if specified
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(scenario_json, f, indent=2, ensure_ascii=False)
                self.logger.info(f"Scenario results saved to: {output_file}")
                print(f"\n💾 Scenario results saved to: {output_file}")
            except Exception as e:
                self.logger.error(f"Error saving to file: {e}")
                print(f"\n❌ Error saving to file: {e}")
        
        return scenario_json
    
    def save_scenario_results(
        self,
        evaluation_results: Dict[str, Any],
        rag_url: str = None,
        scenario_name: str = None
    ) -> str:
        """
        Save scenario results with automatic file naming and directory creation.
        
        Args:
            evaluation_results: Results from evaluate_chatbot_conversation
            rag_url: URL where the chatbot gets information from
            scenario_name: Optional scenario name (auto-generated if None)
            
        Returns:
            Path to the saved file
        """
        # Create results directory if it doesn't exist
        output_dir = self.config.results_output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if not scenario_name:
            scenario_name = f"chatbot_evaluation_{timestamp}"
        
        filename = f"{scenario_name}.json"
        filepath = os.path.join(output_dir, filename)
        
        # Export and save
        scenario_json = self.export_scenario_to_json(
            evaluation_results, 
            rag_url=rag_url,
            output_file=filepath
        )
        
        return filepath
    
    def print_json_preview(self, scenario_json: Dict[str, Any]):
        """
        Print a preview of the JSON structure.
        
        Args:
            scenario_json: The scenario JSON data
        """
        metadata = scenario_json['scenario_metadata']
        
        print(f"\n📋 JSON Structure Preview:")
        print(f"   - Scenario ID: {metadata['scenario_id']}")
        print(f"   - Total Interactions: {metadata['total_interactions']}")
        print(f"   - Average Score: {metadata['average_score']}")
        print(f"   - Success Rate: {metadata['success_rate']}%")
        print(f"   - Model Used: {metadata['model_used']}")
        print(f"   - RAG Source: {metadata['rag_source_url']}")
    
    def export_to_csv(self, evaluation_results: Dict[str, Any], output_file: str = None) -> str:
        """
        Export evaluation results to CSV format.
        
        Args:
            evaluation_results: Results from evaluate_chatbot_conversation
            output_file: Optional file path (auto-generated if None)
            
        Returns:
            Path to the saved CSV file
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required for CSV export. Install with: pip install pandas")
        
        detailed_results = evaluation_results["detailed_results"]
        
        # Prepare data for CSV
        csv_data = []
        for result in detailed_results:
            csv_data.append({
                "turn_number": result["turn"],
                "user_prompt": result["user_prompt"],
                "chatbot_reply": result["bot_reply"],
                "evaluation_score": result["evaluation_score"],
                "judgement": result["justification"],
                "status": result["status"]
            })
        
        df = pd.DataFrame(csv_data)
        
        # Generate filename if not provided
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(self.config.results_output_dir, f"evaluation_results_{timestamp}.csv")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Save to CSV
        df.to_csv(output_file, index=False, encoding='utf-8')
        
        self.logger.info(f"Results exported to CSV: {output_file}")
        print(f"\n📊 Results exported to CSV: {output_file}")
        
        return output_file
    
    def get_summary_stats(self, evaluation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract summary statistics from evaluation results.
        
        Args:
            evaluation_results: Results from evaluate_chatbot_conversation
            
        Returns:
            Summary statistics
        """
        summary = evaluation_results["summary"]
        
        return {
            "total_interactions": summary["total_turns"],
            "average_score": summary["average_score"],
            "success_rate": summary["success_rate"],
            "score_distribution": {
                "excellent": summary["excellent_responses"],
                "good": summary["good_responses"],
                "fair": summary["fair_responses"],
                "poor": summary["poor_responses"]
            },
            "performance_grade": self._calculate_performance_grade(summary["average_score"])
        }
    
    def _calculate_performance_grade(self, avg_score: float) -> str:
        """Calculate a letter grade based on average score."""
        if avg_score >= 2.7:
            return "A"
        elif avg_score >= 2.3:
            return "B"
        elif avg_score >= 1.7:
            return "C"
        elif avg_score >= 1.0:
            return "D"
        else:
            return "F" 