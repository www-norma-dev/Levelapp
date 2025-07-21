"""
Main demonstration script for Level Upgrade framework.
Shows how to use the refactored classes for chatbot evaluation.
"""

import asyncio
import logging
from typing import List

# Import Level Upgrade framework
from level_upgrade import ScenarioRunner, Config, ChatSimulator, ResultsExporter
from level_upgrade.utils import setup_logging, print_banner, validate_prompts

# Define your custom prompts here
CUSTOM_PROMPTS = [
    "Hello, can you help me with information about IONOS services?",
    "What are the main features of IONOS web hosting?",
    "How much does IONOS cloud hosting cost?",
    "Can you explain the difference between shared and dedicated hosting?",
    "What security features does IONOS provide?",
    "How do I contact IONOS customer support?",
    "Thank you for the information!"
]

# Alternative scenario: AI and Technology Discussion
AI_DISCUSSION_PROMPTS = [
    "What is artificial intelligence?",
    "How does machine learning work?",
    "What are the benefits of AI in healthcare?",
    "What are the potential risks of AI?",
    "How can we ensure AI development is ethical?",
    "What's the future of AI technology?"
]

# Customer Service Scenario
CUSTOMER_SERVICE_PROMPTS = [
    "Hi, I'm having trouble with my account login",
    "I forgot my password, can you help me reset it?",
    "How long does it usually take to reset a password?",
    "Is there a way to enable two-factor authentication?",
    "What should I do if I still can't access my account?",
    "Thank you for your help!"
]


async def demo_custom_scenario():
    """Demonstrate scenario evaluation with custom prompts."""
    print_banner("🚀 LEVEL UPGRADE - CUSTOM PROMPTS DEMO")
    
    # Setup logging
    logger = setup_logging("INFO")
    
    # Create configuration from environment
    config = Config.from_env()
    
    # Create scenario runner
    runner = ScenarioRunner(config)
    
    # Validate your custom prompts
    validate_prompts(CUSTOM_PROMPTS)
    print(f"✅ Validated {len(CUSTOM_PROMPTS)} custom prompts")
    
    # Run scenario with your custom prompts
    results = await runner.run_complete_scenario(
        prompts=CUSTOM_PROMPTS,                    # Your custom prompts
        rag_url="https://www.ionos.com",           # RAG source URL
        evaluator_type="local",                    # Evaluator type
        scenario_name="ionos_customer_inquiry",    # Custom scenario name
        export_results=True                        # Export to JSON
    )
    
    print(f"\n✅ Custom scenario completed successfully!")
    print(f"📊 Summary Stats: {results['summary_stats']}")
    print(f"📁 Exported files: {results['scenario_metadata']['exported_files']}")
    
    return results


async def demo_multiple_scenarios():
    """Demonstrate running multiple different scenarios."""
    print_banner("🔄 MULTIPLE SCENARIOS DEMO")
    
    config = Config.from_env()
    runner = ScenarioRunner(config)
    
    scenarios = [
        {
            "name": "ionos_services",
            "prompts": CUSTOM_PROMPTS,
            "rag_url": "https://www.ionos.com"
        },
        {
            "name": "ai_discussion", 
            "prompts": AI_DISCUSSION_PROMPTS,
            "rag_url": "https://www.ionos.com"  # You can change this URL
        },
        {
            "name": "customer_service",
            "prompts": CUSTOMER_SERVICE_PROMPTS,
            "rag_url": "https://www.ionos.com"
        }
    ]
    
    all_results = []
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n🔍 Running Scenario {i}/{len(scenarios)}: {scenario['name']}")
        
        # Validate prompts
        validate_prompts(scenario['prompts'])
        
        # Run scenario
        results = await runner.run_complete_scenario(
            prompts=scenario['prompts'],
            rag_url=scenario['rag_url'],
            evaluator_type="local",
            scenario_name=scenario['name'],
            export_results=True
        )
        
        all_results.append({
            "scenario_name": scenario['name'],
            "summary_stats": results['summary_stats'],
            "files": results['scenario_metadata']['exported_files']
        })
        
        print(f"✅ {scenario['name']} completed - Average Score: {results['summary_stats']['average_score']}")
    
    # Print summary of all scenarios
    print(f"\n📊 SUMMARY OF ALL SCENARIOS:")
    print("="*50)
    for result in all_results:
        print(f"📋 {result['scenario_name']}:")
        print(f"   Average Score: {result['summary_stats']['average_score']}")
        print(f"   Performance Grade: {result['summary_stats']['performance_grade']}")
        print(f"   Success Rate: {result['summary_stats']['success_rate']}%")
        print(f"   Exported to: {result['files']}")
        print()
    
    return all_results


async def demo_interactive_prompts():
    """Demonstrate getting prompts from user input (optional)."""
    print_banner("💬 INTERACTIVE PROMPTS DEMO")
    
    # For demonstration, we'll use predefined prompts
    # But you could replace this with actual input() calls
    print("Using predefined prompts for demonstration...")
    
    # Example of how you could collect prompts interactively:
    # interactive_prompts = []
    # print("Enter your prompts (type 'done' to finish):")
    # while True:
    #     prompt = input("Prompt: ").strip()
    #     if prompt.lower() == 'done':
    #         break
    #     if prompt:
    #         interactive_prompts.append(prompt)
    
    # For now, using predefined prompts
    interactive_prompts = [
        "What services does IONOS offer?",
        "How reliable is IONOS hosting?",
        "What are the pricing options?"
    ]
    
    config = Config.from_env()
    runner = ScenarioRunner(config)
    
    print(f"Running scenario with {len(interactive_prompts)} prompts...")
    
    results = await runner.run_complete_scenario(
        prompts=interactive_prompts,
        rag_url="https://www.ionos.com",
        evaluator_type="local",
        scenario_name="interactive_demo",
        export_results=True
    )
    
    return results


async def main():
    """Main function to run all demonstrations."""
    print_banner("🎉 LEVEL UPGRADE FRAMEWORK - CUSTOM PROMPTS")
    
    try:
        # Run custom prompts demo
        print("\n" + "="*60)
        await demo_custom_scenario()
        
        # Run multiple scenarios demo
        print("\n" + "="*60)
        await demo_multiple_scenarios()
        
        # Run interactive demo
        print("\n" + "="*60)
        await demo_interactive_prompts()
        
        print("\n" + "="*60)
        print_banner("✅ ALL CUSTOM SCENARIOS COMPLETED!")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        logging.error(f"Demonstration error: {e}", exc_info=True)


if __name__ == "__main__":
    # Run the demonstrations
    asyncio.run(main()) 