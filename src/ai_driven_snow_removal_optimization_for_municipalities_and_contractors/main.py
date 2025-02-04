#!/usr/bin/env python
import sys
import os
import requests
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)
from ai_driven_snow_removal_optimization_for_municipalities_and_contractors.crew import AiDrivenSnowRemovalOptimizationForMunicipalitiesAndContractorsCrew

def check_lmstudio_server(url: str) -> bool:
    """
    Check if the LMStudio server is running and accessible.
    
    Args:
        url: The base URL of the LMStudio server
    
    Returns:
        bool: True if server is running, False otherwise
    """
    try:
        # Try to connect to the LMStudio server's health endpoint
        response = requests.get(f"{url}/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def validate_lmstudio_connection():
    """
    Validate that the LMStudio server is running before starting the crew.
    Raises RuntimeError if server is not accessible.
    """
    lmstudio_url = "http://10.0.0.175:1234/v1"
    if not check_lmstudio_server(lmstudio_url):
        raise RuntimeError(
            "LMStudio server is not running or not accessible at "
            f"{lmstudio_url}. Please start the LMStudio server before "
            "running the crew."
        )

# This main file is intended to be a way for your to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    print("Starting OLAF agents execution...")
    # Validate LMStudio connection before starting
    validate_lmstudio_connection()
    
    inputs = {
        'region': 'Montreal'
    }
    AiDrivenSnowRemovalOptimizationForMunicipalitiesAndContractorsCrew().crew().kickoff(inputs=inputs)


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        'region': 'Montreal'
    }
    try:
        AiDrivenSnowRemovalOptimizationForMunicipalitiesAndContractorsCrew().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        AiDrivenSnowRemovalOptimizationForMunicipalitiesAndContractorsCrew().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        'region': 'Montreal'
    }
    try:
        AiDrivenSnowRemovalOptimizationForMunicipalitiesAndContractorsCrew().crew().test(n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: main.py <command> [<args>]")
        sys.exit(1)

    command = sys.argv[1]
    if command == "run":
        run()
    elif command == "train":
        train()
    elif command == "replay":
        replay()
    elif command == "test":
        test()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
