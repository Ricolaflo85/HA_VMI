"""Helpers to parse EnOcean EEP payloads for the VMI custom integration."""
from __future__ import annotations

from typing import Any


def parse_profile_payload(profile_key: tuple[str, str, str], payload: bytes) -> dict[str, Any]:
    """Parse a raw EnOcean payload for supported EEPs used by the VMI installation."""
    rorg, func, typ = profile_key

    if profile_key == ("a5", "09", "04"):
        return _parse_a5_09_04(payload)
    if profile_key == ("a5", "04", "01"):
        return _parse_a5_04_01(payload)
    if profile_key == ("d2", "01", "12"):
        return _parse_d2_01_12(payload)
    if profile_key == ("d5", "00", "01"):
        return _parse_d5_00_01(payload)
    if profile_key == ("d106d", "00", "00"):
        return _parse_d106d_00_00(payload)
    if profile_key == ("d1079", "00", "00"):
        return _parse_d1079_00_00(payload)
    if profile_key == ("d1079", "01", "00"):
        return _parse_d1079_01_00(payload)
    if profile_key == ("f6", "02", "02"):
        return _parse_f6_02_02(payload)
    return {}


def _parse_a5_09_04(payload: bytes) -> dict[str, Any]:
    if len(payload) < 3:
        return {}
    hum_raw = payload[0]
    conc_raw = payload[1]
    tmp_raw = payload[2]
    humidity = round(hum_raw / 2.0, 1)
    co2 = conc_raw * 10
    temperature = round(tmp_raw * 51.0 / 255.0, 1)
    return {"HUM": humidity, "CONC": co2, "TMP": temperature}


def _parse_a5_04_01(payload: bytes) -> dict[str, Any]:
    if len(payload) < 3:
        return {}
    hum_raw = payload[1]
    tmp_raw = payload[2]
    humidity = round(hum_raw * 100.0 / 250.0, 1)
    temperature = round(tmp_raw * 40.0 / 250.0, 1)
    return {"HUM": humidity, "TMP": temperature}


def _parse_d2_01_12(payload: bytes) -> dict[str, Any]:
    if len(payload) < 3:
        return {}
    ov = payload[2] & 0x7F
    io = payload[1] & 0x1F
    pf = (payload[0] >> 0) & 0x01
    return {"OV": ov, "IO": io, "PF": pf}


def _parse_d5_00_01(payload: bytes) -> dict[str, Any]:
    if not payload:
        return {}
    contact_open = bool(payload[0] & 0x01)
    return {"CO": contact_open}


def _get_bits(payload: bytes, start_bit: int, length: int) -> int:
    if len(payload) * 8 < start_bit + length:
        return 0
    value = int.from_bytes(payload, byteorder="big")
    total_bits = len(payload) * 8
    shift = total_bits - (start_bit + length)
    return (value >> shift) & ((1 << length) - 1)


def _parse_d106d_00_00(payload: bytes) -> dict[str, Any]:
    if len(payload) < 6:
        return {}
    cmd = payload[2]
    if cmd not in (2, 3):
        return {}

    result = {
        "CMD": cmd,
        "IAQ_GLOBAL": _get_bits(payload, 24, 3),
        "IAQ_SOURCE": _get_bits(payload, 27, 4),
        "IAQ_DRY": _get_bits(payload, 31, 3),
        "IAQ_MOULD": _get_bits(payload, 34, 3),
        "IAQ_DM": _get_bits(payload, 37, 3),
        "HCI": _get_bits(payload, 40, 2),
    }

    if cmd == 3:
        result["IAQ_CO2"] = _get_bits(payload, 42, 3)

    return result


def _parse_d1079_00_00(payload: bytes) -> dict[str, Any]:
    if len(payload) < 6:
        return {}
    cmd = payload[1] & 0x0F
    if cmd not in (1, 3):
        return {}
    batt = payload[2]
    temp_raw = int.from_bytes(payload[3:5], byteorder="big")
    hum_raw = payload[5]
    temperature = round(temp_raw / 272.0, 1)
    humidity = hum_raw
    return {"TEMP": temperature, "HUM": humidity, "BATT": batt}


def _parse_d1079_01_00(payload: bytes) -> dict[str, Any]:
    if len(payload) < 9:
        return {}
    mf = payload[2]
    byp = (payload[3] >> 7) & 0x01
    plh = (payload[3] >> 6) & 0x01
    debf = (payload[3] >> 5) & 0x01
    surv = (payload[3] >> 4) & 0x01
    vac = (payload[3] >> 3) & 0x01
    boos = payload[4]
    temp_elec = payload[5]
    temp_souf = payload[6]
    temp_hydr = payload[7]
    temp_solar = payload[8]
    return {
        "MF": mf,
        "BYP": byp,
        "PLH": plh,
        "DEBF": debf,
        "SURV": surv,
        "VAC": vac,
        "BOOS": boos,
        "TEMPCELEC": temp_elec,
        "TEMPMSOUFFL": temp_souf,
        "TEMPCHYDROR": temp_hydr,
        "TEMPCSOLAR": temp_solar,
    }


def _parse_f6_02_02(payload: bytes) -> dict[str, Any]:
    if len(payload) < 2:
        return {}
    action = payload[1]
    if action in (0x70, 0x50, 0x30, 0x10, 0x37, 0x15):
        return {"STATE": True}
    return {"STATE": False}
