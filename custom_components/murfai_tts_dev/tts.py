"""
Setting up TTS entity.
"""
import logging
from typing import AsyncGenerator

from homeassistant.components.tts import TextToSpeechEntity, TtsAudioType
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
from homeassistant.exceptions import HomeAssistantError

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
        config_entry.data.get(CONF_VOICE_LOCALE),
    )
    async_add_entities([MurfAITTSEntity(hass, config_entry, engine)])


class MurfAITTSEntity(TextToSpeechEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False
    # This property tells Home Assistant that we support streaming
    _attr_can_stream = True

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
        """Return name of entity"""
        return f"{self._config.data[CONF_STYLE]}"

    async def async_stream_get_tts_audio(
        self, message: str, language: str, options: dict
    ) -> TtsAudioType:
        """Stream TTS audio."""
        last_lang_state: State | None = self.hass.states.get(LAST_LANG_HELPER)
        effective_language = language
        if last_lang_state and last_lang_state.state not in ("unknown", "unavailable"):
            detected_lang = last_lang_state.state
            effective_language = self.language_map.get(detected_lang, detected_lang)

        try:
            # Run the synchronous, streaming API call in an executor
            audio_stream = await self.hass.async_add_executor_job(
                self._engine.get_tts_audio_stream, message, effective_language
            )

            # This async generator will yield the chunks as they come in
            async def stream_generator() -> AsyncGenerator[bytes, None]:
                for chunk in audio_stream:
                    yield chunk

            return (
                self._engine._format.lower(),
                stream_generator(),
            )
        except Exception as e:
            _LOGGER.error("Unknown Error during streaming: %s", e)
            raise HomeAssistantError(e) from e

    # We still need the old method for services that don't support streaming
    def get_tts_audio(self, message: str, language: str, options: dict) -> TtsAudioType:
        """Get TTS audio."""
        last_lang_state: State | None = self.hass.states.get(LAST_LANG_HELPER)
        effective_language = language
        if last_lang_state and last_lang_state.state not in ("unknown", "unavailable"):
            detected_lang = last_lang_state.state
            effective_language = self.language_map.get(detected_lang, detected_lang)
        
        try:
            # We need to collect all chunks into a single byte string
            audio_stream = self._engine.get_tts_audio_stream(message, effective_language)
            audio_bytes = b"".join(audio_stream)
            
            return (self._engine._format.lower(), audio_bytes)
        except Exception as e:
            _LOGGER.error("Unknown Error during TTS generation: %s", e)
            raise HomeAssistantError(e) from e
