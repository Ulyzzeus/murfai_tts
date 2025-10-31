"""Config flow for MurfAI text-to-speech custom component."""
from __future__ import annotations
from typing import Any
import voluptuous as vol
import logging
from urllib.parse import urlparse

from homeassistant import data_entry_flow
from homeassistant.config_entries import ConfigFlow
from homeassistant.helpers.selector import selector
from homeassistant.exceptions import HomeAssistantError

from .const import CONF_API_KEY, CONF_MODEL, CONF_STYLE, CONF_URL, DOMAIN, MODELS, STYLES, UNIQUE_ID # Add CONF_API_KEY

_LOGGER = logging.getLogger(__name__)

def generate_unique_id(user_input: dict) -> str:
    """Generate a unique id from user input."""
    url = urlparse(user_input[CONF_URL])
    return f"{url.hostname}_{user_input[CONF_MODEL]}_{user_input[CONF_STYLE]}"
				return self.async_create_entry(title=f"MurfAI TTS Fork ({hostname}, {user_input[CONF_MODEL]})", data=user_input) #

async def validate_user_input(user_input: dict):
    """Validate user input fields."""
    if user_input.get(CONF_MODEL) is None:
        raise ValueError("Model is required")
    if user_input.get(CONF_STYLE) is None:
        raise ValueError("Style is required")

class MurfAITTSConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MurfAI TTS."""
    VERSION = 1
    data_schema = vol.Schema({
        vol.Optional(CONF_URL, default="https://murf.ai/Prod/anonymous-tts/audio"): str,
        vol.Required(CONF_MODEL, default="VM0165993640063143B"): selector({
            "select": {
                "options": MODELS,
                "mode": "dropdown",
                "sort": True,
                "custom_value": True
            }
        }),
        vol.Required(CONF_STYLE, default="Inspirational"): selector({
            "select": {
                "options": STYLES,
                "mode": "dropdown",
                "sort": True,
                "custom_value": True
            }
        })
    })

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                await validate_user_input(user_input)
                unique_id = generate_unique_id(user_input)
                user_input[UNIQUE_ID] = unique_id
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                hostname = urlparse(user_input[CONF_URL]).hostname
                return self.async_create_entry(title=f"MurfAI TTS ({hostname}, {user_input[CONF_MODEL]}, {user_input[CONF_STYLE]})", data=user_input)
            except data_entry_flow.AbortFlow:
                return self.async_abort(reason="already_configured")
            except HomeAssistantError as e:
                _LOGGER.exception(str(e))
                errors["base"] = str(e)
            except ValueError as e:
                _LOGGER.exception(str(e))
                errors["base"] = str(e)
            except Exception as e:  # pylint: disable=broad-except
                _LOGGER.exception(str(e))
                errors["base"] = "unknown_error"
        return self.async_show_form(step_id="user", data_schema=self.data_schema, errors=errors, description_placeholders=user_input)
