"""Config flow for MurfAI text-to-speech custom component."""
from __future__ import annotations
from typing import Any
import voluptuous as vol
import logging
import json
import requests
from urllib.parse import urlparse

from homeassistant import data_entry_flow
from homeassistant.config_entries import ConfigFlow
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
            json.loads(user_input[CONF_PRONUNCIATION_DICTIONARY])
        except json.JSONDecodeError:
            raise ValueError("Pronunciation dictionary is not valid JSON")

class MurfAITTSConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MurfAI TTS."""
    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.data = {}
        self.voices = []
        self.selected_voice = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step of getting the API key."""
        errors = {}
        if user_input is not None:
            try:
                # Store the API key and fetch voices
                self.data[CONF_API_KEY] = user_input[CONF_API_KEY]
                self.voices = await self.hass.async_add_executor_job(
                    MurfAITTSEngine.get_voices, self.data[CONF_API_KEY]
                )
                return await self.async_step_model()
            except requests.exceptions.HTTPError as e:
                _LOGGER.exception(str(e))
                errors["base"] = "invalid_api_key"
            except Exception as e:
                _LOGGER.exception(str(e))
                errors["base"] = "unknown_error"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): str}),
            errors=errors,
        )

    async def async_step_model(self, user_input: dict[str, Any] | None = None):
        """Handle the voice model selection step."""
        if user_input is not None:
            self.data[CONF_MODEL] = user_input[CONF_MODEL]
            # Find the selected voice details
            self.selected_voice = next(
                (v for v in self.voices if v["voiceId"] == self.data[CONF_MODEL]), None
            )
            return await self.async_step_style()

        # Filter voices for English and German
        filtered_voices = [
            v for v in self.voices if v['locale'].startswith('en-') or v['locale'].startswith('de-')
        ]
        models = {v['voiceId']: f"{v['displayName']} ({v['locale']})" for v in filtered_voices}

        return self.async_show_form(
            step_id="model",
            data_schema=vol.Schema({vol.Required(CONF_MODEL): vol.In(models)}),
        )

    async def async_step_style(self, user_input: dict[str, Any] | None = None):
        """Handle the voice style selection step."""
        if user_input is not None:
            self.data[CONF_STYLE] = user_input[CONF_STYLE]
            return await self.async_step_options()

        styles = self.selected_voice.get("availableStyles", [])
        if not styles:
            # If no styles are available, use a default value and proceed
            self.data[CONF_STYLE] = "standard"
            return await self.async_step_options()

        return self.async_show_form(
            step_id="style",
            data_schema=vol.Schema({vol.Required(CONF_STYLE): vol.In(styles)}),
        )

    async def async_step_options(self, user_input: dict[str, Any] | None = None):
        """Handle the final options step."""
        errors = {}
        if user_input is not None:
            try:
                self.data.update(user_input)
                await validate_user_input(self.data)
                unique_id = generate_unique_id(self.data)
                self.data[UNIQUE_ID] = unique_id
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"MurfAI TTS ({self.selected_voice['displayName']}, {self.data[CONF_STYLE]})",
                    data=self.data,
                )
            except data_entry_flow.AbortFlow:
                return self.async_abort(reason="already_configured")
            except ValueError as e:
                _LOGGER.exception(str(e))
                errors["base"] = str(e)
            except Exception as e:
                _LOGGER.exception(str(e))
                errors["base"] = "unknown_error"

        options_schema = vol.Schema({
            vol.Optional(CONF_URL, default="https://api.murf.ai/v1/speech/generate"): str,
            vol.Optional(CONF_FORMAT_MP3, default=False): bool,
            vol.Optional(CONF_MULTI_NATIVE_LOCALE): str,
            vol.Optional(CONF_PRONUNCIATION_DICTIONARY): selector({"text": {"multiline": True}}),
            vol.Optional(CONF_SAMPLE_RATE, default=44100): selector({
                "select": {
                    "options": SAMPLE_RATES,
                    "mode": "dropdown",
                }
            }),
        })

        return self.async_show_form(
            step_id="options",
            data_schema=options_schema,
            errors=errors,
        )