import requests
import urllib.parse
from io import BytesIO

class MurfAITTSEngine:

      # Add api_key to the constructor
    def __init__(self, style: str, model: str, url: str, api_key: str):
        self._style = style # Note: The paid API may not use 'style' in the same way. The curl example doesn't show it.
        self._model = model # This will now be the voiceId, e.g., 'en-US-terrell'
        self._url = url # This should be 'https://api.murf.ai/v1/speech/generate'
        self._api_key = api_key # Store the API key

    def get_tts(self, text: str):
        """ Makes request to the paid MurfAI TTS API to convert text into audio"""
        
        # 1. Define the headers for authentication and content type
        headers = {
            "api-key": self._api_key,
            "Content-Type": "application/json"
        }

        # 2. Define the payload (the data body) as a Python dictionary
        # The paid API uses 'voiceId', which corresponds to your 'model'
        payload = {
            "text": text,
            "voiceId": self._model
            # The 'style' parameter might be part of a different field or not supported by this endpoint.
            # You'll need to check the Murf.ai API documentation for how to specify style/tone.
            # For now, we will omit it as per the curl example.
        }

        # 3. Make the POST request
        # We use the 'json' parameter of requests.post, which automatically converts the dict to JSON
        resp = requests.post(self._url, headers=headers, json=payload)
        
        # This part remains the same
        resp.raise_for_status()
        return resp.content

    @staticmethod
    def get_supported_langs() -> list:
        """Returns list of supported languages."""
        # You should update this based on the paid API's capabilities
        return ["en"]