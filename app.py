import asyncio
from level_core.simluators.service import ConversationSimulator
from level_core.datastore.firestore.schemas import ScenarioBatch

# Optionally: from level_core.simluators.schemas import Interaction, BasicConversation

def dummy_evaluation_fn(*args, **kwargs):
    # Replace with real evaluation logic as needed
    return {}

def dummy_persistence_fn(results):
    # Replace with real persistence logic as needed
    print("Persisted results:", results)

def create_dummy_batch():
    # Replace with real scenario loading logic
    return ScenarioBatch(
        metadata={"batch_name": "test_batch"},
        content={"prompt": "What is the capital of France?"},
    )

async def main():
    batch = create_dummy_batch()
    simulator = ConversationSimulator(
        batch=batch,
        evaluation_fn=dummy_evaluation_fn,
        persistence_fn=dummy_persistence_fn
    )
    simulator.setup_simulator(
        endpoint="http://localhost:8000/",
        headers={"Content-Type": "application/json"}
    )
    result = await simulator.run_batch_test(
        name="test_batch",
        test_load={},
        attempts=1
    )
    print("Simulation result:", result)

if __name__ == "__main__":
    asyncio.run(main())
