"""
Setting up TTS entity.
"""
import logging
from homeassistant.components.tts import TextToSpeechEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import generate_entity_id
from .const import (
    CONF_API_KEY,
    CONF_MODEL,
    CONF_STYLE,
    CONF_URL,
    CONF_FORMAT_MP3,
    CONF_MULTI_NATIVE_LOCALE,
    CONF_PRONUNCIATION_DICTIONARY,
    CONF_SAMPLE_RATE,
    CONF_VOICE_LOCALE,
    DOMAIN,
    UNIQUE_ID,
)
from .murfaitts_engine import MurfAITTSEngine
from homeassistant.exceptions import MaxLengthExceeded

_LOGGER = logging.getLogger(__name__)

LAST_LANG_HELPER = "input_text.last_detected_language"

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MurfAI Text-to-speech platform via config entry."""
    engine = MurfAITTSEngine(
        config_entry.data[CONF_API_KEY],
        config_entry.data[CONF_STYLE],
        config_entry.data[CONF_MODEL],
        config_entry.data[CONF_URL],
        config_entry.data.get(CONF_FORMAT_MP3, False),
        config_entry.data.get(CONF_MULTI_NATIVE_LOCALE),
        config_entry.data.get(CONF_PRONUNCIATION_DICTIONARY),
        int(config_entry.data.get(CONF_SAMPLE_RATE, 44100)),
        # This .get() is the fix. It provides 'None' if the key is missing in old configs.
        config_entry.data.get(CONF_VOICE_LOCALE),
    )
    async_add_entities([MurfAITTSEntity(hass, config_entry, engine)])

class MurfAITTSEntity(TextToSpeechEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, hass, config, engine):
        """Initialize TTS entity."""
        self.hass = hass
        self._engine = engine
        self._config = config
        self.language_map = {"de": "de-DE", "en": "en-UK"}
        self._attr_unique_id = config.data.get(UNIQUE_ID)
        if self._attr_unique_id is None:
            self._attr_unique_id = f"{config.data[CONF_STYLE]}_{config.data[CONF_MODEL]}"
        self.entity_id = generate_entity_id(f"tts.{DOMAIN}_" + "{}", config.data[CONF_STYLE], hass=hass)

    @property
    def default_language(self):
        return self._config.data.get(CONF_MULTI_NATIVE_LOCALE) or "en-US"

    @property
    def supported_languages(self):
        return self._engine.get_supported_langs()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._attr_unique_id)},
            "model": f"{self._config.data[CONF_STYLE]}",
            "manufacturer": "MurfAI (Dev)"
        }

    @property
    def name(self):
        return f"{self._config.data[CONF_STYLE]}"

    def get_tts_audio(self, message, language, options=None):
        try:
            if len(message) > 4096:
                raise MaxLengthExceeded

            last_lang_state: State | None = self.hass.states.get(LAST_LANG_HELPER)
            effective_language = language
            if last_lang_state and last_lang_state.state not in ("unknown", "unavailable"):
                detected_lang = last_lang_state.state
                effective_language = self.language_map.get(detected_lang, detected_lang)

            speech = self._engine.get_tts(message, language=effective_language)
            return self._engine._format.lower(), speech
        except MaxLengthExceeded:
            _LOGGER.error("Maximum length of the message exceeded")
        except Exception as e:
            _LOGGER.error("Unknown Error: %s", e)
        return None, None
