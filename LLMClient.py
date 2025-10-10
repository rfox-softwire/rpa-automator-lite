from dotenv import dotenv_values
import requests
import logging
from pathlib import Path

config = dotenv_values()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.base_url = config["INFERENCE_SERVER_URL"]
        self.model_name = config["MODEL_NAME_OPENAI"]
        # self.model_name = config["MODEL_NAME_GEMMA"]
        # self.model_name = config["MODEL_NAME_GEMMA_LOW"]

    def send_prompt(self, prompt, temperature=0.7):
        payload = {
            "model": self.model_name,
            "messages": [{
                "role": "user",
                "content": prompt
            }],
            "max_tokens": -1,
            "temperature": temperature
        }

        try:
            logger.info(f"Sending request to {self.base_url} with payload: {payload}")
            response = requests.post(f"{self.base_url}/chat/completions", json = payload)
            result = response.json()
            logger.info(f"Successfully received response from LLM")
            return result
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.exception(error_msg)
            raise Exception(error_msg) from e