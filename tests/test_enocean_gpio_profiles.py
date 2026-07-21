from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

module_path = Path(__file__).resolve().parents[1] / "custom_components" / "enocean_gpio" / "eeps.py"
spec = spec_from_file_location("enocean_gpio_epps", module_path)
module = module_from_spec(spec)
spec.loader.exec_module(module)
parse_profile_payload = module.parse_profile_payload


def test_parse_d5_00_01_contact_open():
    payload = parse_profile_payload(("d5", "00", "01"), bytes([0x01]))
    assert payload["CO"] is True


def test_parse_d5_00_01_contact_closed():
    payload = parse_profile_payload(("d5", "00", "01"), bytes([0x00]))
    assert payload["CO"] is False


def test_parse_a5_04_01_temperature_and_humidity():
    payload = parse_profile_payload(("a5", "04", "01"), bytes([0x00, 0x64, 0x64]))
    assert payload["HUM"] == 40.0
    assert payload["TMP"] == 16.0


def test_parse_d1079_00_00_temperature_humidity_battery():
    payload = parse_profile_payload(("d1079", "00", "00"), bytes([0x07, 0x91, 0x05, 0x18, 0xBA, 0x38]))
    assert payload["TEMP"] == 23.3
    assert payload["HUM"] == 56
    assert payload["BATT"] == 5


def test_parse_d106d_00_00_iaq():
    payload = parse_profile_payload(("d106d", "00", "00"), bytes([0x06, 0xD2, 0x02, 0x00, 0x00, 0x40, 0x81]))
    assert payload["CMD"] == 2
    assert payload["IAQ_GLOBAL"] == 0
    assert payload["IAQ_SOURCE"] == 0
    assert payload["IAQ_DRY"] == 0
    assert payload["IAQ_MOULD"] == 0
    assert payload["IAQ_DM"] == 0
    assert payload["HCI"] == 1
