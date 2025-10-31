"""Config flow for MurfAI text-to-speech custom component."""
from __future__ import annotations
from typing import Any
import voluptuous as vol
import logging
import json
import requests
from urllib.parse import urlparse

from homeassistant import config_entries # Import config_entries
from homeassistant.data_entry_flow import AbortFlow
from homeassistant.helpers.selector import selector
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_API_KEY,
    CONF_MODEL,
    CONF_STYLE,
    CONF_URL,
    CONF_FORMAT_MP3,
    CONF_MULTI_NATIVE_LOCALE,
    CONF_PRONUNCIATION_DICTIONARY,
    CONF_SAMPLE_RATE,
    DOMAIN,
    SAMPLE_RATES,
    UNIQUE_ID,
)
from .murfaitts_engine import MurfAITTSEngine

_LOGGER = logging.getLogger(__name__)

def generate_unique_id(user_input: dict) -> str:
    """Generate a unique id from user input."""
    return f"{user_input[CONF_MODEL]}_{user_input[CONF_STYLE]}"

async def validate_user_input(user_input: dict):
    """Validate user input fields."""
    if not user_input.get(CONF_API_KEY):
        raise ValueError("API Key is required")
    if user_input.get(CONF_PRONUNCIATION_DICTIONARY):
        try:
            if user_input[CONF_PRONUNCIATION_DICTIONARY]:
                json.loads(user_input[CONF_PRONUNCIATION_DICTIONARY])
        except json.JSONDecodeError:
            raise ValueError("Pronunciation dictionary is not valid JSON")

# This is the decorator that was missing
@config_entries.HANDLERS.register(DOMAIN)
class MurfAITTSConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MurfAI TTS."""
    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.config_data = {}
        self.voices = []
        _LOGGER.debug("Initializing MurfAI TTS config flow")

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step of getting the API key."""
        _LOGGER.debug("Step: user, user_input: %s", user_input)
        errors = {}
        if user_input is not None:
            try:
                api_key = user_input[CONF_API_KEY]
                _LOGGER.debug("Fetching voices with API key")
                self.voices = await self.hass.async_add_executor_job(
                    MurfAITTSEngine.get_voices, api_key
                )
                self.config_data[CONF_API_KEY] = api_key
                _LOGGER.debug("Voices fetched successfully, proceeding to model step")
                return await self.async_step_model()
            except requests.exceptions.HTTPError as e:
                _LOGGER.error("MurfAI API key validation failed: %s", e)
                errors["base"] = "invalid_api_key"
            except Exception as e:
                _LOGGER.error("An unknown error occurred during API key validation: %s", e)
                errors["base"] = "unknown_error"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): str}),
            errors=errors,
        )

    async def async_step_model(self, user_input: dict[str, Any] | None = None):
        """Handle the voice model selection step."""
        _LOGGER.debug("Step: model, user_input: %s", user_input)
        if user_input is not None:
            self.config_data.update(user_input)
            _LOGGER.debug("Model selected, proceeding to style step. Current data: %s", self.config_data)
            return await self.async_step_style()

        filtered_voices = [
            v for v in self.voices if v.get('locale', '').startswith(('en-', 'de-'))
        ]
        models = {v['voiceId']: f"{v['displayName']} ({v['locale']})" for v in filtered_voices}

        return self.async_show_form(
            step_id="model",
            data_schema=vol.Schema({vol.Required(CONF_MODEL): vol.In(models)}),
        )

    async def async_step_style(self, user_input: dict[str, Any] | None = None):
        """Handle the voice style selection step."""
        _LOGGER.debug("Step: style, user_input: %s", user_input)
        selected_model_id = self.config_data.get(CONF_MODEL)
        selected_voice = next(
            (v for v in self.voices if v["voiceId"] == selected_model_id), None
        )

        if user_input is not None:
            self.config_data.update(user_input)
            _LOGGER.debug("Style selected, proceeding to options step. Current data: %s", self.config_data)
            return await self.async_step_options()

        if not selected_voice:
            _LOGGER.error("No voice found for model ID: %s", selected_model_id)
            return self.async_abort(reason="no_voice_selected")

        styles = selected_voice.get("availableStyles", [])
        if not styles:
            _LOGGER.debug("No styles available for selected voice, using 'standard'")
            self.config_data[CONF_STYLE] = "standard"
            return await self.async_step_options()

        return self.async_show_form(
            step_id="style",
            data_schema=vol.Schema({vol.Required(CONF_STYLE): vol.In(styles)}),
        )

    async def async_step_options(self, user_input: dict[str, Any] | None = None):
        """Handle the final options step and create the entry."""
        _LOGGER.debug("Step: options, user_input: %s", user_input)
        errors = {}
        if user_input is not None:
            self.config_data.update(user_input)
            _LOGGER.debug("Final config data before validation: %s", self.config_data)
            try:
                await validate_user_input(self.config_data)
                _LOGGER.debug("Validation successful")

                unique_id = generate_unique_id(self.config_data)
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                _LOGGER.debug("Unique ID set: %s", unique_id)

                selected_model_id = self.config_data.get(CONF_MODEL)
                selected_voice = next(
                    (v for v in self.voices if v["voiceId"] == selected_model_id), None
                )
                title_name = selected_voice['displayName'] if selected_voice else selected_model_id

                _LOGGER.debug("Creating entry with title: %s and data: %s", f"MurfAI TTS ({title_name}, {self.config_data[CONF_STYLE]})", self.config_data)
                return self.async_create_entry(
                    title=f"MurfAI TTS ({title_name}, {self.config_data[CONF_STYLE]})",
                    data=self.config_data,
                )
            except AbortFlow as e:
                _LOGGER.warning("Configuration aborted: %s", e)
                return self.async_abort(reason="already_configured")
            except ValueError as e:
                _LOGGER.error("Validation error: %s", e)
                errors["base"] = str(e)
            except Exception as e:
                _LOGGER.error("An unknown error occurred while creating entry: %s", e, exc_info=True)
                errors["base"] = "unknown_error"

        options_schema = vol.Schema({
            vol.Optional(CONF_URL, default="https://api.murf.ai/v1/speech/generate"): str,
            vol.Optional(CONF_FORMAT_MP3, default=False): bool,
            vol.Optional(CONF_MULTI_NATIVE_LOCALE, default=""): str,
            vol.Optional(CONF_PRONUNCIATION_DICTIONARY, default=""): selector({"text": {"multiline": True}}),
            vol.Optional(CONF_SAMPLE_RATE, default="44100"): selector({
                "select": { "options": SAMPLE_RATES, "mode": "dropdown" }
            }),
        })

        return self.async_show_form(
            step_id="options",
            data_schema=options_schema,
            errors=errors,
        )