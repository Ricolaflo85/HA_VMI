# -*- encoding: utf-8 -*-
import logging
from jeedom.openenocean.resources.openenoceand.enocean import utils
import jeedom.openenocean.resources.openenoceand.globals as globals
from jeedom.openenocean.resources.openenoceand.enocean.protocol.packet import RadioPacket
from jeedom.openenocean.resources.openenoceand.enocean.protocol.constants import PACKET, RORG

def send(rorg,raw,sender,destination):
    logging.debug('Sending Raw message ' + str(raw))
    data = [rorg] + utils.string_to_list(raw) + sender +[0x80]
    optional = [0x03] + [0xFF,0xFF,0xFF,0xFF] + [0xFF, 0x00]
    globals.COMMUNICATOR.send(RadioPacket(PACKET.RADIO, data=data, optional=optional))
