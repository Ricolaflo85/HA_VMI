"""EnOcean GPIO custom component for Home Assistant."""
from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import CONF_PORT as ENOCEAN_CONF_PORT, DOMAIN
from .hub import EnOceanHub

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(ENOCEAN_CONF_PORT, default="/dev/ttyS2"): cv.string,
            },
            extra=vol.ALLOW_EXTRA,
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    hass.data.setdefault(DOMAIN, {})

    if DOMAIN in config:
        await _async_start_hub(hass, config[DOMAIN].get(ENOCEAN_CONF_PORT, "/dev/ttyS2"))

    _LOGGER.info("EnOcean GPIO component initialized")
    return True


async def _async_start_hub(hass: HomeAssistant, port: str) -> None:
    hub = hass.data[DOMAIN].get("hub")
    if hub is not None:
        return

    hub = EnOceanHub(hass, port)
    hass.data[DOMAIN]["hub"] = hub

    try:
        await hub.async_start()
    except Exception as err:
        _LOGGER.error("Unable to start EnOcean hub: %s", err)
        raise


async def async_get_hub(hass: HomeAssistant, config: dict | None = None) -> EnOceanHub:
    hass.data.setdefault(DOMAIN, {})
    hub = hass.data[DOMAIN].get("hub")
    if hub is not None:
        return hub

    port = "/dev/ttyS2"
    if config is not None and isinstance(config, dict):
        port = config.get(ENOCEAN_CONF_PORT, port)

    await _async_start_hub(hass, port)
    return hass.data[DOMAIN]["hub"]
