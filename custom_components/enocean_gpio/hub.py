"""EnOcean hub implementation for Home Assistant."""
from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import Any

import serial
from serial import SerialException

from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import ALL_EEP_PROFILES, DOMAIN, SIGNAL_ENOCEAN_EVENT
from .eeps import parse_profile_payload

_LOGGER = logging.getLogger(__name__)

# Serial telegram header constants
SYNC_BYTE = 0x55


class EnOceanHub:
    def __init__(self, hass: HomeAssistant, port: str) -> None:
        self.hass = hass
        self.port = port
        self._serial: serial.Serial | None = None
        self._read_task: asyncio.Task | None = None
        self._buffer: bytearray = bytearray()
        self._connected = False

    async def async_start(self) -> None:
        await self._async_connect()
        self._read_task = self.hass.async_create_task(self._read_loop())

    async def async_stop(self) -> None:
        if self._read_task:
            self._read_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._read_task
        if self._serial and self._serial.is_open:
            self._serial.close()

    async def _async_connect(self) -> None:
        try:
            self._serial = serial.Serial(self.port, 57600, timeout=0.5)
            self._connected = True
            _LOGGER.info("Connected to EnOcean port %s", self.port)
        except SerialException as exc:
            self._connected = False
            _LOGGER.error("Cannot open EnOcean port %s: %s", self.port, exc)
            raise

    async def _read_loop(self) -> None:
        while True:
            if not self._connected:
                try:
                    await self._async_connect()
                except Exception:
                    await asyncio.sleep(5)
                    continue
            try:
                data = await self.hass.async_add_executor_job(self._serial.read, 64)
                if data:
                    self._buffer.extend(data)
                    await self._process_buffer()
                else:
                    await asyncio.sleep(0.1)
            except SerialException as exc:
                _LOGGER.warning("Serial exception on %s: %s", self.port, exc)
                self._connected = False
                if self._serial:
                    self._serial.close()
                await asyncio.sleep(2)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                _LOGGER.exception("Unexpected error reading EnOcean port: %s", exc)
                await asyncio.sleep(2)

    async def _process_buffer(self) -> None:
        while True:
            if len(self._buffer) < 6:
                return
            if self._buffer[0] != SYNC_BYTE:
                del self._buffer[0]
                continue
            packet_header = self._buffer[1:6]
            if len(packet_header) < 5:
                return
            data_length = int.from_bytes(packet_header[0:2], byteorder="big")
            opt_length = packet_header[2]
            packet_length = 6 + data_length + opt_length + 1
            if len(self._buffer) < packet_length:
                return
            packet = bytes(self._buffer[:packet_length])
            del self._buffer[:packet_length]
            try:
                telegram = self._parse_packet(packet)
                if telegram:
                    async_dispatcher_send(self.hass, SIGNAL_ENOCEAN_EVENT, telegram)
            except Exception as exc:
                _LOGGER.warning("Failed to parse EnOcean packet: %s", exc)

    def _parse_packet(self, packet: bytes) -> dict[str, Any] | None:
        if len(packet) < 6:
            return None
        header = packet[0]
        if header != SYNC_BYTE:
            return None
        data_length = int.from_bytes(packet[1:3], byteorder="big")
        opt_length = packet[3]
        packet_type = packet[4]
        data_offset = 6
        data = packet[data_offset : data_offset + data_length]
        opt = packet[data_offset + data_length : data_offset + data_length + opt_length]
        rorg = data[0] if data else None
        if rorg is None:
            return None
        sender = opt[0:4] if len(opt) >= 4 else b""
        sender_id = sender.hex()
        destination = opt[4:8] if len(opt) >= 8 else b""
        dest_id = destination.hex()
        if rorg == 0xA5:
            func = f"{data[1]:02x}"
            typ = f"{data[2]:02x}"
        elif rorg == 0xD2:
            func = f"{data[1]:02x}"
            typ = f"{data[2]:02x}"
        elif rorg == 0xD1:
            func = f"{data[1]:02x}"
            typ = f"{data[2]:02x}"
        else:
            func = f"{data[1]:02x}" if len(data) > 1 else ""
            typ = f"{data[2]:02x}" if len(data) > 2 else ""
        profile_key = (f"{rorg:02x}", func, typ)
        # If exact profile not found, try to match manufacturer-specific
        # profiles that start with the rorg hex (e.g. 'd1079' starts with 'd1').
        if profile_key not in ALL_EEP_PROFILES:
            for key in ALL_EEP_PROFILES.keys():
                if key[1] == func and key[2] == typ and key[0].startswith(f"{rorg:02x}"):
                    profile_key = key
                    break
            else:
                return None
        payload = self._parse_eep(payload=data[1:], profile_key=profile_key)
        if not payload:
            return None
        return {
            "id": sender_id,
            "destination": dest_id,
            "profile": profile_key,
            "payload": payload,
            "device_name": ALL_EEP_PROFILES[profile_key]["name"],
        }

    def _parse_eep(self, payload: bytes, profile_key: tuple[str, str, str]) -> dict[str, Any]:
        return parse_profile_payload(profile_key, payload)

    async def async_poll(self) -> None:
        if not self._connected:
            return
        # nothing to poll explicitly; state updates come from telegrams
