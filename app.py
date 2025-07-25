import asyncio
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from level_core.simluators.service import ConversationSimulator
from level_core.evaluators.service import EvaluationService
from level_core.evaluators.schemas import EvaluationConfig
from level_core.simluators.schemas import ConversationBatch, BasicConversation

# Logger setup
logger = logging.getLogger("run-batch-test")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# Flask app
app = Flask(__name__)
CORS(app)

@app.route("/run_batch_test", methods=["POST"])
def run_batch_test():
    try:
        data = request.get_json(force=True)

        # Extract model_id and api_key from body
        model_id = data.get("model_id")
        api_key = data.get("api_key")
        test_batch_data = data.get("test_batch")

        if not model_id or not api_key or not test_batch_data:
            return jsonify({"error": "Missing model_id, api_key, or test_batch in body"}), 400

        # Setup evaluation config
        evaluation_service = EvaluationService(logger=logger)
        ionos_config = EvaluationConfig(
            api_url="https://inference.api.us-east-1.ionos.com",
            api_key=api_key,
            model_id=model_id
        )
        evaluation_service.set_config(provider="ionos", config=ionos_config)

        # Parse batch test
        batch = ConversationBatch.model_validate(test_batch_data)

        # Setup and run simulator
        simulator = ConversationSimulator(
            batch=batch,
            evaluation_service=evaluation_service
        )
        simulator.setup_simulator(
            endpoint="https://inference.api.us-east-1.ionos.com",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "x-model-id": model_id
            }
        )

        results = asyncio.run(
            simulator.run_batch_test(
                name="Batch Test",
                test_load={},
                attempts=1
            )
        )

        return jsonify(results), 200

    except Exception as e:
        logger.exception("Failed to run batch test")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
