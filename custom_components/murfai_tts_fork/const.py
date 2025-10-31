""" Constants for MurfAI TTS custom component"""

DOMAIN = "murfai_tts_fork"
CONF_API_KEY = "api_key"
CONF_URL = "url"
CONF_MODEL = "model" # Corresponds to 'voiceId' in the API
CONF_STYLE = "style"
UNIQUE_ID = 'unique_id'

# Optional Parameters
CONF_FORMAT_MP3 = 'format_mp3' # Boolean switch for MP3 format
CONF_SAMPLE_RATE = "sample_rate"
CONF_MULTI_NATIVE_LOCALE = 'multi_native_locale'
CONF_LOCALE = "locale" # For multiNativeLocale
CONF_PRONUNCIATION_DICTIONARY = 'pronunciation_dictionary'

SAMPLE_RATES = [8000, 24000, 44100, 48000]
