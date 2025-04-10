"""
LLM Client module for interacting with Ollama.
Provides a client for making completions with locally hosted LLMs.
"""

import json
import logging
import requests
import time
from typing import Dict, List, Any, Optional, Union

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Client for interacting with Ollama's API to get completions from local LLMs.
    """
    
    def __init__(self, model_name="llama2", base_url="http://localhost:11434"):
        """
        Initialize the Ollama client.
        
        Args:
            model_name: Name of the Ollama model to use (default: llama2)
            base_url: Base URL for Ollama API (default: http://localhost:11434)
        """
        self.model_name = model_name
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api/generate"
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        
        # Default parameters
        self.default_params = {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 2048
        }
    
    def complete(self, prompt: str, **kwargs) -> str:
        """
        Generate text completion using Ollama.
        
        Args:
            prompt: The text prompt for completion
            **kwargs: Additional parameters to pass to Ollama API
                      (temperature, top_p, max_tokens, etc.)
            
        Returns:
            Generated text as string
        """
        # Prepare request payload
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            **self.default_params,
            **kwargs
        }
        
        logger.info(f"Generating completion with {self.model_name}")
        
        # Try to get completion with retries
        retries = 0
        while retries < self.max_retries:
            try:
                response = requests.post(self.api_url, json=payload)
                response.raise_for_status()
                
                # Parse response
                result = response.json()
                
                # Extract generated text
                generated_text = result.get("response", "")
                if not generated_text:
                    logger.warning("Empty response from Ollama")
                
                return generated_text
                
            except requests.exceptions.RequestException as e:
                retries += 1
                logger.warning(f"Error calling Ollama API (attempt {retries}/{self.max_retries}): {e}")
                if retries < self.max_retries:
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"Failed to get completion after {self.max_retries} attempts")
                    return "Error: Failed to get response from language model."
    
    def complete_with_json(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate text completion and parse as JSON.
        
        Args:
            prompt: The text prompt for completion
            **kwargs: Additional parameters to pass to Ollama API
            
        Returns:
            Parsed JSON response or empty dict if parsing fails
        """
        # Add instruction to format as JSON
        json_prompt = f"{prompt}\n\nPlease provide your response in valid JSON format only."
        
        # Get completion
        response_text = self.complete(json_prompt, **kwargs)
        
        # Try to extract and parse JSON
        try:
            # Look for JSON within the response (in case there's extra text)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                return json.loads(json_text)
            else:
                # If no braces found, try to parse the whole response
                return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            logger.debug(f"Raw response: {response_text}")
            return {}


# For testing purposes
if __name__ == "__main__":
    # Create client
    client = OllamaClient(model_name="llama2")
    
    # Test basic completion
    test_prompt = "What are the key skills needed for a data scientist?"
    
    print(f"Testing completion with prompt: '{test_prompt}'")
    response = client.complete(test_prompt)
    print(f"\nResponse:\n{response}")
    
    # Test JSON completion
    json_prompt = """
    Extract skills from this job description:
    
    Job: Data Scientist
    Description: We are looking for a data scientist with 5+ years of experience in Python, machine learning, and data visualization. Knowledge of SQL and cloud platforms like AWS is required.
    
    Return a JSON object with these keys:
    - required_skills: array of required skills
    - years_experience: number of years required
    """
    
    print(f"\nTesting JSON completion...")
    json_response = client.complete_with_json(json_prompt)
    print(f"\nJSON Response:\n{json.dumps(json_response, indent=2)}") 