import requests
import json
import logging
from io import BytesIO

_LOGGER = logging.getLogger(__name__)

class MurfAITTSEngine:
    def __init__(self, api_key: str, style: str, model: str, url: str, format_mp3: bool, multi_native_locale: str | None, pronunciation_dictionary: str, sample_rate: int, voice_locale: str | None):
        self._api_key = api_key
        self._style = style
        self._model = model
        self._url = url
        self._format = "MP3" if format_mp3 else "WAV"
        self._multi_native_locale = multi_native_locale
        self._pronunciation_dictionary = json.loads(pronunciation_dictionary) if pronunciation_dictionary else None
        self._sample_rate = sample_rate
        self._voice_locale = voice_locale

    def get_tts(self, text: str, language: str | None = None):
        headers = {"Content-Type": "application/json", "Accept": "application/json", "api-key": self._api_key}
        voice_id_to_send = self._model
        effective_locale = language or self._multi_native_locale

        if effective_locale and self._voice_locale and self._model.startswith(self._voice_locale):
            prefix_to_remove = f"{self._voice_locale}-"
            voice_id_to_send = self._model.replace(prefix_to_remove, '', 1)

        data = {
            "text": text,
            "voiceId": voice_id_to_send,
            "style": self._style,
            "format": self._format,
            "sampleRate": self._sample_rate,
        }
        if effective_locale:
            data["multiNativeLocale"] = effective_locale
        if self._pronunciation_dictionary:
            data["pronunciationDictionary"] = self._pronunciation_dictionary

        _LOGGER.debug("Sending Murf.ai TTS request with payload: %s", data)
        resp = requests.post(self._url, headers=headers, json=data)
        resp.raise_for_status()

        audio_url = resp.json().get("audioFile")
        if not audio_url:
            raise Exception("No audio file URL in response")

        audio_resp = requests.get(audio_url)
        audio_resp.raise_for_status()
        return audio_resp.content

    @staticmethod
    def get_voices(api_key: str):
        headers = {"api-key": api_key}
        url = "https://api.murf.ai/v1/speech/voices"
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_supported_langs() -> list:
        return ["en", "de"]
