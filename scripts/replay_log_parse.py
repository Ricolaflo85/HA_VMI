#!/usr/bin/env python3
import re
import ast
import sys
from pathlib import Path
import importlib.util

# Load hub module directly to avoid importing package __init__ (voluptuous may be absent)
ROOT = Path(__file__).resolve().parents[1]
hub_path = ROOT / 'custom_components' / 'enocean_gpio' / 'hub.py'
const_path = ROOT / 'custom_components' / 'enocean_gpio' / 'const.py'

# Load const module first and register package names to satisfy relative imports
spec2 = importlib.util.spec_from_file_location('custom_components.enocean_gpio.const', str(const_path))
const_mod = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(const_mod)

# register package modules
import types as _types
pkg_mod = _types.ModuleType('custom_components')
pkg_sub = _types.ModuleType('custom_components.enocean_gpio')
sys.modules['custom_components'] = pkg_mod
sys.modules['custom_components.enocean_gpio'] = pkg_sub
sys.modules['custom_components.enocean_gpio.const'] = const_mod

spec = importlib.util.spec_from_file_location('custom_components.enocean_gpio.hub', str(hub_path))
hub_mod = importlib.util.module_from_spec(spec)
# Provide a fake minimal serial module to satisfy imports when parsing offline
import types
fake_serial = types.SimpleNamespace(SerialException=Exception)
sys.modules['serial'] = fake_serial
# Provide minimal homeassistant stubs required by hub module
ha_pkg = types.ModuleType('homeassistant')
core_mod = types.ModuleType('homeassistant.core')
helpers_mod = types.ModuleType('homeassistant.helpers')
dispatcher_mod = types.ModuleType('homeassistant.helpers.dispatcher')

class HomeAssistant:  # minimal stub
    def async_create_task(self, coro):
        return None
    async def async_add_executor_job(self, func, *args, **kwargs):
        return func(*args)

core_mod.HomeAssistant = HomeAssistant
def async_dispatcher_send(hass, signal, data):
    # simply print for debug
    print('DISPATCH', signal, data)

dispatcher_mod.async_dispatcher_send = async_dispatcher_send
helpers_mod.dispatcher = dispatcher_mod
sys.modules['homeassistant'] = ha_pkg
sys.modules['homeassistant.core'] = core_mod
sys.modules['homeassistant.helpers'] = helpers_mod
sys.modules['homeassistant.helpers.dispatcher'] = dispatcher_mod
spec.loader.exec_module(hub_mod)

spec.loader.exec_module(hub_mod)

EnOceanHub = hub_mod.EnOceanHub
ALL_EEP_PROFILES = const_mod.ALL_EEP_PROFILES

LOG = Path('f93730fa_ha_enoceanmqtt_aseracorp_2026-07-14T15-20-19.062Z.log')
LINE_RE = re.compile(r"0x01")


def extract_two_lists(s: str):
    i = s.find('0x01')
    if i == -1:
        return None
    # find first '[' after i
    first = s.find('[', i)
    if first == -1:
        return None
    # find matching ']' for first list
    second = s.find(']', first)
    if second == -1:
        return None
    list1 = s[first: second+1]
    # find next '[' after second
    third = s.find('[', second+1)
    if third == -1:
        return None
    fourth = s.find(']', third)
    if fourth == -1:
        return None
    list2 = s[third: fourth+1]
    return list1, list2


def parse_hex_list(s):
    # convert "['0xa5', '0x0', ...]" to bytes
    lst = ast.literal_eval(s)
    return bytes(int(x, 16) for x in lst)


def main():
    if not LOG.exists():
        print('Log file not found:', LOG)
        return

    hub = EnOceanHub(None, '/dev/null')
    counts = {}
    text = LOG.read_text()
    idx = 0
    while True:
        pos = text.find('0x01', idx)
        if pos == -1:
            break
        # extract two lists from text starting at pos
        def extract_from(text, i):
            first = text.find('[', i)
            if first == -1:
                return None, -1
            second = text.find(']', first)
            if second == -1:
                return None, -1
            list1 = text[first: second+1]
            third = text.find('[', second+1)
            if third == -1:
                return None, -1
            fourth = text.find(']', third)
            if fourth == -1:
                return None, -1
            list2 = text[third: fourth+1]
            return (list1, list2), fourth+1

        lists, newidx = extract_from(text, pos)
        if not lists:
            idx = pos + 3
            continue
        data_s, opt_s = lists
        # debug: show first bytes found
        print('DEBUG_EXTRACT:', data_s)
        # continue scanning
        idx = newidx
        try:
            data = parse_hex_list(data_s)
        except Exception:
            continue
        if len(data) == 0:
            continue
        # find RORG inside data (handle radio headers that precede RORG)
        rorg_idx = None
        for i, b in enumerate(data):
            if b in (0xa5, 0xd1, 0xd2):
                rorg_idx = i
                break
        if rorg_idx is None:
            continue
        payload = data[rorg_idx:]
        found = False
        for key in ALL_EEP_PROFILES:
            try:
                decoded = hub._parse_eep(payload, key)
            except Exception:
                decoded = {}
            if decoded:
                counts.setdefault(key, 0)
                counts[key] += 1
                print('FOUND', key, '->', decoded)
                found = True
                break
        if not found:
            # try default profile key based on rorg/func/typ
            rorg = payload[0]
            func = f"{payload[1]:02x}" if len(payload) > 1 else '00'
            typ = f"{payload[2]:02x}" if len(payload) > 2 else '00'
            profile_key = (f"{rorg:02x}", func, typ)
            print('UNHANDLED', profile_key, 'payload', payload.hex())
    print('\nSummary counts:')
    for k, v in counts.items():
        print(k, v)


if __name__ == '__main__':
    main()
