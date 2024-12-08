import requests
import urllib.parse
from io import BytesIO

class MurfAITTSEngine:

    def __init__(self, style: str, model: str, url: str):
        self._style = style
        self._model = model
        self._url = url

    def get_tts(self, text: str):
        """ Makes request to MurfAI TTS engine to convert text into audio"""
        url=self._url+"?voiceId="+self._model+"&style="+self._style+"&text="+urllib.parse.quote_plus(text)
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.content

    @staticmethod
    def get_supported_langs() -> list:
        """Returns list of supported languages. Note: the model determines the provides language automatically."""
        # return ["af", "ar", "hy", "az", "be", "bs", "bg", "ca", "zh", "hr", "cs", "da", "nl", "en", "et", "fi", "fr", "gl", "de", "el", "he", "hi", "hu", "is", "id", "it", "ja", "kn", "kk", "ko", "lv", "lt", "mk", "ms", "mr", "mi", "ne", "no", "fa", "pl", "pt", "ro", "ru", "sr", "sk", "sl", "es", "sw", "sv", "tl", "ta", "th", "tr", "uk", "ur", "vi", "cy"]
        return ["en"]