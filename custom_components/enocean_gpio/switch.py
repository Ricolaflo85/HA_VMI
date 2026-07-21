"""Switch platform for EnOcean GPIO."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import ALL_EEP_PROFILES, DOMAIN, SIGNAL_ENOCEAN_EVENT

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass: HomeAssistant, config: dict, async_add_entities, discovery_info=None) -> None:
    entities: dict[str, EnOceanSwitch] = {}

    @callback
    def handle_event(event: dict[str, Any]) -> None:
        profile_key = tuple(event["profile"])
        if profile_key not in ALL_EEP_PROFILES:
            return
        payload = event["payload"]
        device_id = event["id"]
        device_name = event.get("device_name", "EnOcean Device")

        for field, entity_def in ALL_EEP_PROFILES[profile_key]["entities"].items():
            if entity_def["type"] != "switch":
                continue
            if field not in payload:
                continue

            unique_id = f"{device_id}_{profile_key[0]}_{profile_key[1]}_{profile_key[2]}_{field}"
            if unique_id in entities:
                entities[unique_id]._set_state(bool(payload[field]))
                continue

            entity = EnOceanSwitch(device_id, device_name, profile_key, field, entity_def)
            entity._set_state(bool(payload[field]))
            entities[unique_id] = entity
            async_add_entities([entity], True)

    async_dispatcher_connect(hass, SIGNAL_ENOCEAN_EVENT, handle_event)


class EnOceanSwitch(SwitchEntity):
    def __init__(self, device_id: str, device_name: str, profile_key: tuple[str, str, str], field: str, definition: dict[str, Any]) -> None:
        self._device_id = device_id
        self._device_name = device_name
        self._profile_key = profile_key
        self._field = field
        self._definition = definition
        self._attr_name = f"{device_name} {definition['name']}"
        self._attr_is_on = False
        self._attr_unique_id = f"{device_id}_{profile_key[0]}_{profile_key[1]}_{profile_key[2]}_{field}"
        self._attr_extra_state_attributes = {
            "device_id": device_id,
            "profile": profile_key,
            "field": field,
        }

    def _set_state(self, value: bool) -> None:
        self._attr_is_on = value
        if self.hass is not None:
            self.async_write_ha_state()

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": self._device_name,
            "manufacturer": "EnOcean",
            "model": f"{self._profile_key[0]}-{self._profile_key[1]}-{self._profile_key[2]}",
        }

    @property
    def available(self) -> bool:
        return self._attr_is_on is not None
