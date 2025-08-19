import asyncio
import json
import os
from typing import Dict, Any
from logging import Logger

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict
from dotenv import load_dotenv
from contextlib import asynccontextmanager

from level_core.simluators.schemas import BasicConversation, ConversationBatch
from level_core.simluators.service import ConversationSimulator
from level_core.evaluators.service import EvaluationService
from level_core.evaluators.schemas import EvaluationConfig

# Load environment variables
load_dotenv()

# Global services
evaluation_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize evaluation service on startup"""
    global evaluation_service
    
    try:
        # Initialize evaluation service
        evaluation_service = EvaluationService(logger=Logger("EvaluationService"))
        
        # Set up default configurations if environment variables are available
            
        print("✅ LevelApp API started successfully")
        
    except Exception as e:
        print(f"❌ Error during startup: {e}")
    
    yield
    print("🔄 LevelApp API shutting down...")

# Initialize FastAPI app
app = FastAPI(
    title="LevelApp API",
    description="Minimal API for conversation evaluation",
    version="1.0.0",
    lifespan=lifespan
)
from fastapi.middleware.cors import CORSMiddleware

origins = os.getenv("ALLOWED_ORIGINS", "").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Main evaluation request schema
class MainEvaluationRequest(BaseModel):
    """Main evaluation request that mimics main.py behavior"""
    model_config = ConfigDict(protected_namespaces=())
    
    test_batch: Dict[str, Any] = Field(description="The test batch data from batch_test.json format")
    endpoint: str = Field(default="http://localhost:8000", description="LLM endpoint to test against")
    model_id: str = Field(default="meta-llama/Llama-3.3-70B-Instruct", description="Model ID for headers")
    attempts: int = Field(default=1, description="Number of test attempts")
    test_name: str = Field(default="api_test", description="Name for the test run")


@app.post("/evaluate", tags=["Main"])
async def main_evaluate(request: MainEvaluationRequest):
    """
    End point to evaluate a conversation batch against an LLM endpoint.
    """
    try:
        # Check if evaluation service is initialized
        if evaluation_service is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Evaluation service not initialized. Server may need restart."
            )
        
        # Validate and create BasicConversation from test_batch
        try:
            batch_test = BasicConversation.model_validate(request.test_batch)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid test_batch format: {str(e)}"
            )
        
        # Create conversations batch
        conversations_batch = ConversationBatch(conversations=[batch_test])
        
        # Set up simulator (mimicking main.py)
        simulator = ConversationSimulator(conversations_batch, evaluation_service)
        
        # Setup simulator with endpoint and headers
        headers = {
            "Content-Type": "application/json",
            "x-model-id": request.model_id
        }
        
        simulator.setup_simulator(
            endpoint=request.endpoint,
            headers=headers
        )
        
        # Run the batch test (this is the main work)
        results = await simulator.run_batch_test(
            name=request.test_name,
            test_load={}, 
            attempts=request.attempts
        )
        
        # Convert results to JSON-serializable format
        def convert_uuid_to_str(obj):
            """Recursively convert UUID objects to strings for JSON serialization"""
            import uuid
            if isinstance(obj, uuid.UUID):
                return str(obj)
            elif isinstance(obj, dict):
                return {key: convert_uuid_to_str(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_uuid_to_str(item) for item in obj]
            elif hasattr(obj, '__dict__'):
                return convert_uuid_to_str(obj.__dict__)
            else:
                return obj
        
        from fastapi.encoders import jsonable_encoder
        serializable_results = jsonable_encoder(results)


        from level_core.datastore.registry import get_datastore
        from config.loader import get_database_config
        import uuid

        db_config = get_database_config("config.yaml")
        firestore_service = get_datastore(backend="firestore", config=db_config)
        firestore_service.save_batch_test_results(
            user_id="test-user",
            project_id=request.test_name,
            batch_id=f"batch-{uuid.uuid4()}",
            data=serializable_results
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Evaluation completed successfully",
                "test_name": request.test_name,
                "endpoint": request.endpoint,
                "model_id": request.model_id,
                "attempts": request.attempts,
                "results": serializable_results
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    
    # Run the server
    uvicorn.run(
        "app:app", 
        host="0.0.0.0", 
        port=8080, 
        reload=True,
        log_level="info"
    )