# Level Upgrade Framework 🚀

**Advanced Chatbot Evaluation Framework with LLM-as-Judge Methodology**

A comprehensive, class-based framework for evaluating chatbot responses using local and cloud-based language models. Refactored from monolithic code into clean, maintainable classes with separation of concerns.

## 📁 Project Structure

```
level_upgrade/
├── __init__.py                 # Main package exports
├── config.py                   # Configuration management
├── chat_simulator.py           # Chat simulation class
├── scenario_runner.py          # Main orchestration class
├── utils.py                    # Utility functions
├── evaluators/
│   ├── __init__.py
│   └── local_evaluator.py      # Local LLM evaluator
└── exporters/
    ├── __init__.py
    └── results_exporter.py     # Results export functionality

main_refactored.py              # Demonstration script
README_level_upgrade.md         # This file
```

## 🎯 Key Features

### **Class-Based Architecture**
- **ScenarioRunner**: Main orchestration class
- **ChatSimulator**: Handles conversation simulation  
- **LocalEvaluator**: LLM-based response evaluation
- **ResultsExporter**: JSON/CSV export functionality
- **Config**: Environment-based configuration management

### **Evaluation Capabilities**
- **LLM-as-Judge**: Uses language models to evaluate response quality
- **Multiple Evaluators**: Local, OpenAI, and IONOS support
- **Comprehensive Scoring**: 0-3 scale with detailed justifications
- **Batch Processing**: Evaluate entire conversations

### **Export Features**
- **JSON Export**: Structured scenario data with all interactions
- **CSV Export**: Tabular format for analysis
- **Automatic File Management**: Timestamped, organized output

## 🚀 Quick Start

### 1. **Installation**

```bash
# Install dependencies
pip install python-dotenv pandas

# Ensure level_core is available
# (Your existing level_core package)
```

### 2. **Environment Setup**

Create a `.env` file:

```env
# API Configuration
API_BASE_URL=http://127.0.0.1:8000
MODEL_ID=meta-llama/Llama-3.3-70B-Instruct

# Evaluator Configuration (optional - defaults to main API)
EVALUATOR_API_URL=http://127.0.0.1:8000
EVALUATOR_MODEL_ID=meta-llama/Llama-3.3-70B-Instruct

# Results Configuration
RESULTS_OUTPUT_DIR=results

# OpenAI Configuration (optional)
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL_ID=gpt-4o-mini
```

### 3. **Basic Usage**

```python
import asyncio
from level_upgrade import ScenarioRunner, Config

async def main():
    # Create configuration
    config = Config.from_env()
    
    # Create scenario runner
    runner = ScenarioRunner(config)
    
    # Run complete evaluation scenario
    results = await runner.run_complete_scenario(
        prompts=[
            "Hello, how are you?",
            "What's the weather like?", 
            "Tell me a joke"
        ],
        rag_url="https://www.ionos.com",
        evaluator_type="local",
        scenario_name="my_test_scenario"
    )
    
    print(f"Average Score: {results['summary_stats']['average_score']}")
    print(f"Files: {results['scenario_metadata']['exported_files']}")

asyncio.run(main())
```

### 4. **Run Demonstrations**

```bash
python main_refactored.py
```

## 🔧 Core Classes

### **ScenarioRunner**

Main orchestration class that ties everything together.

```python
from level_upgrade import ScenarioRunner, Config

# Initialize
config = Config.from_env()
runner = ScenarioRunner(config)

# Run complete scenario
results = await runner.run_complete_scenario(
    prompts=["Hello!", "How are you?"],
    rag_url="https://example.com",
    evaluator_type="local",
    scenario_name="test_run"
)

# Run example scenario
results = await runner.run_example_scenario()
```

### **ChatSimulator**

Handles conversation simulation with language models.

```python
from level_upgrade import ChatSimulator, Config

# Initialize
config = Config.from_env()
simulator = ChatSimulator(config)

# Initialize RAG
await simulator.init_rag("https://example.com")

# Single prompt
response = await simulator.simulate_single_prompt("Hello!")

# Multiple prompts
prompts = ["Hi!", "How are you?", "Goodbye!"]
replies = await simulator.simulate_conversation(prompts)
```

### **LocalEvaluator** 

Evaluates responses using local LLM with structured prompts.

```python
from level_upgrade.evaluators import LocalEvaluator
from level_upgrade import Config

# Create from config
config = Config.from_env()
evaluator = LocalEvaluator.from_level_config(config)

# Evaluate response
result = await evaluator.evaluate(
    generated_text="Hello! How can I help you?",
    expected_text="Hello, how are you?"
)

print(f"Score: {result.match_level}/3")
print(f"Justification: {result.justification}")
```

### **ResultsExporter**

Exports evaluation results to various formats.

```python
from level_upgrade import ResultsExporter, Config

# Initialize
config = Config.from_env()
exporter = ResultsExporter(config)

# Export to JSON
json_file = exporter.save_scenario_results(
    evaluation_results,
    rag_url="https://example.com",
    scenario_name="my_scenario"
)

# Export to CSV
csv_file = exporter.export_to_csv(evaluation_results)

# Get summary stats
stats = exporter.get_summary_stats(evaluation_results)
```

### **Config**

Environment-based configuration management.

```python
from level_upgrade import Config

# From environment variables
config = Config.from_env()

# From dictionary
config = Config.from_dict({
    "api_base_url": "http://localhost:8000",
    "model_id": "llama-3"
})

# Print configuration
config.print_config()

# Validate configuration
config.validate()
```

## 📊 JSON Output Format

The framework exports comprehensive JSON results:

```json
{
  "scenario_metadata": {
    "scenario_id": "scenario_20241215_143022",
    "timestamp": "2024-12-15T14:30:22.123456",
    "rag_source_url": "https://www.ionos.com",
    "total_interactions": 3,
    "average_score": 2.3,
    "success_rate": 100.0,
    "evaluator_type": "local",
    "model_used": "meta-llama/Llama-3.3-70B-Instruct"
  },
  "interactions": [
    {
      "interaction_id": "interaction_1",
      "turn_number": 1,
      "rag_source_url": "https://www.ionos.com",
      "user_prompt": "Hello, how are you?",
      "chatbot_reply": "Hello! I'm doing well, thank you for asking...",
      "reference": "Hello, how are you?",
      "evaluation_score": 3,
      "judgement": "Excellent response with appropriate greeting...",
      "status": "success",
      "evaluation_timestamp": "2024-12-15T14:30:22.123456"
    }
  ]
}
```

## 🎯 Evaluation Criteria

The LLM-as-Judge evaluates responses on:

- **Relevance**: How well does the response address the user's prompt?
- **Helpfulness**: Is the response useful and informative?
- **Clarity**: Is the response clear and easy to understand?
- **Appropriateness**: Is the tone and style appropriate?
- **Accuracy**: Is the information provided correct?

**Scoring Scale:**
- **3 - Excellent**: Highly relevant, helpful, clear, appropriate, and accurate
- **2 - Good**: Mostly relevant and helpful with minor issues
- **1 - Fair**: Addresses prompt but has notable deficiencies  
- **0 - Poor**: Irrelevant, unhelpful, unclear, or inappropriate

## 🔄 Migration from Original Code

The refactored framework maintains full compatibility while providing better structure:

### **Before (main.py):**
```python
# Monolithic functions
prompts = ["Hello!", "How are you?"]
replies = await chat_simulation(prompts)
results = await evaluate_chatbot_conversation(prompts, replies)
export_scenario_results_to_json(results, "https://example.com")
```

### **After (Level Upgrade):**
```python
# Class-based approach
runner = ScenarioRunner(Config.from_env())
results = await runner.run_complete_scenario(
    prompts=["Hello!", "How are you?"],
    rag_url="https://example.com"
)
```

## 🛠️ Advanced Usage

### **Custom Configuration**
```python
# Custom config
config = Config(
    api_base_url="http://custom-api:8080",
    model_id="custom-model",
    llm_config={"temperature": 0.2, "max_tokens": 300}
)
```

### **Multiple Evaluator Types**
```python
# Test with different evaluators
for evaluator_type in ["local", "openai"]:
    results = await runner.run_complete_scenario(
        prompts=test_prompts,
        evaluator_type=evaluator_type,
        scenario_name=f"test_{evaluator_type}"
    )
```

### **Component Testing**
```python
# Test individual components
simulator = ChatSimulator(config)
evaluator = LocalEvaluator.from_level_config(config)
exporter = ResultsExporter(config)

# Use components independently
replies = await simulator.simulate_conversation(prompts)
eval_result = await evaluator.evaluate(reply, prompt)
exporter.save_scenario_results(results)
```

## 🎉 Benefits of Refactoring

1. **Maintainability**: Clear separation of concerns
2. **Reusability**: Components can be used independently  
3. **Testability**: Each class can be unit tested
4. **Extensibility**: Easy to add new evaluators/exporters
5. **Configuration**: Centralized, environment-based config
6. **Documentation**: Self-documenting class structure
7. **Error Handling**: Consistent error handling patterns

## 🔍 Testing

Run the demonstration script to test all functionality:

```bash
python main_refactored.py
```

This will demonstrate:
- Basic scenario evaluation
- Custom prompt scenarios  
- Individual component usage
- Multiple evaluator types

## 📚 Dependencies

- `level_core`: Your existing evaluation framework
- `python-dotenv`: Environment variable management
- `pandas`: CSV export functionality (optional)
- `asyncio`: Async/await support
- Standard library modules

---

**Level Upgrade Framework** - Transform your chatbot evaluation workflow with clean, maintainable, class-based architecture! 🚀 