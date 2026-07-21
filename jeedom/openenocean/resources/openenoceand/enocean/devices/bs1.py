# -*- encoding: utf-8 -*-
import logging
from jeedom.openenocean.resources.openenoceand.enocean import utils
import jeedom.openenocean.resources.openenoceand.globals as globals
from jeedom.openenocean.resources.openenoceand.enocean.protocol.packet import RadioPacket, UTETeachIn
from jeedom.openenocean.resources.openenoceand.enocean.protocol.constants import PACKET, RORG

def parse(action,packet):
    logging.debug("Its a BS1 message")
    for k in packet.parsed:
        action[k] = packet.parsed[k]
    return action

