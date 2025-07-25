import asyncio
import logging
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from level_core.simluators.service import ConversationSimulator
from level_core.evaluators.service import EvaluationService
from level_core.evaluators.schemas import EvaluationConfig
from level_core.simluators.schemas import BasicConversation, ConversationBatch

# Load environment variables
load_dotenv()

# Logger setup
logger = logging.getLogger("run-batch-test")
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(stream_handler)

# Initialize Flask
app = Flask(__name__)
CORS(app)

@app.route("/run_batch_test", methods=["POST"])
def run_batch_test():
    try:
        # Parse request
        request_data = request.get_json(force=True, silent=True)
        if not request_data:
            logger.error("Missing or invalid JSON payload.")
            return jsonify({"error": "Missing or invalid JSON payload"}), 400

        # Extract model_id from body
        model_id = request_data.get("model_id")
        if not model_id:
            logger.error("Missing 'model_id' in payload.")
            return jsonify({"error": "Missing 'model_id' in payload"}), 400

        # Load credentials from env
        api_key = os.getenv("IONOS_API_KEY")
        base_url = os.getenv("IONOS_ENDPOINT")

        if not api_key or not base_url:
            logger.error("Missing IONOS_API_KEY or IONOS_ENDPOINT in .env")
            return jsonify({"error": "Server misconfigured. API key or endpoint missing."}), 500

        # Extract test batch
        batch_test_data = request_data.get("test_batch")
        if not batch_test_data:
            logger.error("Missing 'test_batch' in payload.")
            return jsonify({"error": "Missing 'test_batch' in payload"}), 400

        logger.info(f"Running batch test for model: {model_id}")
        logger.info(f"Description: {batch_test_data.get('description', '')}")

        # Prepare evaluation service
        evaluation_service = EvaluationService(logger=logger)
        ionos_config = EvaluationConfig(
            api_url=base_url,
            api_key=api_key,
            model_id=model_id
        )
        evaluation_service.set_config(provider="ionos", config=ionos_config)

        # Build conversation objects
        batch_test = BasicConversation.model_validate(batch_test_data)
        conversation_batch = ConversationBatch(conversations=[batch_test])

        simulator = ConversationSimulator(conversation_batch, evaluation_service)
        simulator.setup_simulator(
            endpoint=base_url,
            headers={
                "Content-Type": "application/json",
                "x-model-id": model_id
            }
        )

        results = asyncio.run(simulator.run_batch_test(
            name=batch_test_data.get("description", "Unnamed Batch"),
            test_load={},
            attempts=1
        ))

        return jsonify(results), 200

    except Exception as e:
        logger.exception("Exception in /run_batch_test")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
