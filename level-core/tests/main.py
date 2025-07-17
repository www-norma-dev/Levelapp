from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from simulator import simulate_response
from evaluator import evaluate_result

app = FastAPI()

class EvalRequest(BaseModel):
    user_input: str

@app.post("/run-eval/")
async def run_eval(req: EvalRequest):
    try:
        user_input = req.user_input
        
        # Step 1: Simulate response
        bot_response = simulate_response(user_input)
        
        # Step 2: Evaluate response
        evaluation = evaluate_result(user_input, bot_response)
        
        # Step 3: Final result
        return {
            "input": user_input,
            "response": bot_response,
            "evaluation": evaluation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
