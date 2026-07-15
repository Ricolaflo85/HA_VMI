"""Constants for the EnOcean GPIO custom component."""
from __future__ import annotations

DOMAIN = "enocean_gpio"
CONF_PORT = "port"
CONF_NAME = "name"
DEFAULT_NAME = "EnOcean GPIO"
SIGNAL_ENOCEAN_EVENT = "enocean_gpio_event"

# Device profiles keyed by (rorg, func, type) or manufacturer-specific EEP
ALL_EEP_PROFILES = {
    # VMI purevent / Ventilairsec VMI
    ("d1079", "01", "00"): {
        "name": "VMI Ventilairsec",
        "device_class": None,
        "entities": {
            "MF": {"name": "Mode fonctionnement", "type": "sensor"},
            "BYP": {"name": "Bypass", "type": "binary_sensor"},
            "PLH": {"name": "Plage horaire", "type": "binary_sensor"},
            "DEBF": {"name": "Debit fixe", "type": "binary_sensor"},
            "SURV": {"name": "Sur ventilation", "type": "binary_sensor"},
            "VAC": {"name": "Vacances", "type": "binary_sensor"},
            "BOOS": {"name": "Boost", "type": "binary_sensor"},
            "TEMPCELEC": {"name": "Temperature consigne electrique", "type": "sensor", "unit": "°C"},
            "TEMPMSOUFFL": {"name": "Temperature max soufflage", "type": "sensor", "unit": "°C"},
            "TEMPCHYDROR": {"name": "Temperature consigne Hydror", "type": "sensor", "unit": "°C"},
            "TEMPCSOLAR": {"name": "Temperature consigne SolarR", "type": "sensor", "unit": "°C"},
            "DEBAS": {"name": "Debit air sortant", "type": "sensor", "unit": "m3/h"},
            "PCHAUFF": {"name": "Puissance chauffage", "type": "sensor", "unit": "%"},
            "TEMPEXT": {"name": "Temperature exterieure", "type": "sensor", "unit": "°C"},
            "CPDIFF": {"name": "Pression differentielle", "type": "sensor", "unit": "Pa"},
            "IEFIL": {"name": "Indice encrassement filtre", "type": "sensor", "unit": "%"},
            "TGLOB": {"name": "Etat sondes", "type": "binary_sensor"},
            "CERR1": {"name": "Code erreur 1", "type": "sensor"},
            "CERR2": {"name": "Code erreur 2", "type": "sensor"},
        },
    },
    # VMI Assist ventilairsec assistant
    ("d1079", "00", "00"): {
        "name": "Ventilairsec Assistant",
        "entities": {
            "TEMP": {"name": "Temperature assistant", "type": "sensor", "unit": "°C"},
            "HUM": {"name": "Humidite assistant", "type": "sensor", "unit": "%"},
            "BATT": {"name": "Batterie assistant", "type": "sensor"},
        },
    },
    # CO2 sensor
    ("a5", "09", "04"): {
        "name": "CO2 Sensor",
        "entities": {
            "CONC": {"name": "CO2 concentration", "type": "sensor", "unit": "ppm"},
            "TMP": {"name": "Temperature", "type": "sensor", "unit": "°C"},
            "HUM": {"name": "Humidite", "type": "sensor", "unit": "%"},
        },
    },
    # Temperature / humidity sensor
    ("a5", "04", "01"): {
        "name": "Temperature Humidite Sensor",
        "entities": {
            "TMP": {"name": "Temperature", "type": "sensor", "unit": "°C"},
            "HUM": {"name": "Humidite", "type": "sensor", "unit": "%"},
        },
    },
    # Bypass switch module
    ("d2", "01", "12"): {
        "name": "Bypass Switch",
        "entities": {
            "OV": {"name": "Sortie", "type": "switch", "unit": "%"},
            "IO": {"name": "Canal", "type": "sensor"},
            "PF": {"name": "Power failure", "type": "binary_sensor"},
        },
    },
}
