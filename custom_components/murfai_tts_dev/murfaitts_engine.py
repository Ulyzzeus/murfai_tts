import requests
import json
from io import BytesIO

class MurfAITTSEngine:

    def __init__(self, api_key: str, style: str, model: str, url: str, format_mp3: bool, multi_native_locale: str | None, pronunciation_dictionary: str, sample_rate: int):
        self._api_key = api_key
        self._style = style
        self._model = model
        self._url = url
        self._format = "MP3" if format_mp3 else "WAV"
        self._multi_native_locale = multi_native_locale
        if pronunciation_dictionary:
            self._pronunciation_dictionary = json.loads(pronunciation_dictionary)
        else:
            self._pronunciation_dictionary = None
        self._sample_rate = sample_rate

    def get_tts(self, text: str, language: str | None = None):
        """ Makes request to MurfAI TTS engine to convert text into audio"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "api-key": self._api_key,
        }
        data = {
            "text": text,
            "voiceId": self._model,
            "style": self._style,
            "format": self._format,
            "sampleRate": self._sample_rate,
        }

        # Determine which locale to use for this specific request
        effective_locale = language or self._multi_native_locale

        # *** THIS IS THE FIX ***
        # Only add the parameter if the locale is a non-empty string
        if effective_locale:
            data["multiNativeLocale"] = effective_locale

        if self._pronunciation_dictionary:
            data["pronunciationDictionary"] = self._pronunciation_dictionary


        resp = requests.post(self._url, headers=headers, json=data)
        resp.raise_for_status()

        # The response contains a link to the audio file, so we need to download it
        audio_url = resp.json().get("audioFile")
        if not audio_url:
            raise Exception("No audio file URL in response")

        audio_resp = requests.get(audio_url)
        audio_resp.raise_for_status()
        return audio_resp.content

    @staticmethod
    def get_voices(api_key: str):
        """Fetches the list of available voices from the MurfAI API."""
        headers = {
            "api-key": api_key,
        }
        url = "https://api.murf.ai/v1/speech/voices"
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_supported_langs() -> list:
        """Returns list of supported languages."""
        # You may want to update this list based on the languages supported by the paid API
        return ["en", "de"]
