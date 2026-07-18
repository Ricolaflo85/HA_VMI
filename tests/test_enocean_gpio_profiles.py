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
