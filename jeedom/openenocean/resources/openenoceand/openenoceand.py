# This file is part of Jeedom.
#
# Jeedom is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Jeedom is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Jeedom. If not, see <http://www.gnu.org/licenses/>.
import jeedom.openenocean.resources.openenoceand.globals as globals
import logging
import sys
import os
import time
import argparse
import threading
import signal
import traceback
import json
import queue

from jeedom.openenocean.resources.openenoceand.jeedom.jeedom import jeedom_socket, jeedom_utils, jeedom_com, JEEDOM_SOCKET_MESSAGE

# PARAMETERS
communicator = None


def listen():
    jeedom_socket.open()
    logging.debug("Start listening...")
    if globals.DEVICE == 'aruba':
        globals.COMMUNICATOR = ArubaCommunicator()
    else:
        globals.COMMUNICATOR = SerialCommunicator(port=_device)
    globals.COMMUNICATOR.start()
    if globals.COMMUNICATOR.base_id is None and globals.DEVICE != 'aruba':
        logging.error("No base id from enocean key, shutdown")
        shutdown()

    logging.info('The Base ID of your controler is %s.', jeedom.openenocean.resources.openenoceand.enocean.utils.to_hex_string(globals.COMMUNICATOR.base_id).replace(':', ''))
    globals.JEEDOM_COM.send_change_immediate({'baseid': str(jeedom.openenocean.resources.openenoceand.enocean.utils.to_hex_string(globals.COMMUNICATOR.base_id)).replace(':', '')})
    globals.WAITING_RES = False
    packet = Packet(PACKET.COMMON_COMMAND, [0x03])
    globals.COMMUNICATOR.send(packet)
    globals.WAITING_RES = False
    try:
        threading.Thread(target=read_socket, daemon=True).start()
        logging.debug('Read Socket Thread Launched')
        threading.Thread(target=read_communicator, daemon=True).start()
        logging.debug('Read Device Thread Launched')
        globals.JEEDOM_COM.send_change_immediate({'started': 1})
    except KeyboardInterrupt:
        logging.error("KeyboardInterrupt, shutdown")
        shutdown()


def read_communicator():
    while 1:
        try:
            if not globals.COMMUNICATOR.is_alive():
                logging.error("Exception on communicator, communicator is dead")
                shutdown()
            PacketAnalyser.decode_packet(globals.COMMUNICATOR.receive.get(block=True, timeout=1))
        except queue.Empty:
            continue
        except Exception as e:
            logging.error("Exception on enocean : %s", e)
            shutdown()
        time.sleep(0.02)


def read_socket():
    while 1:
        try:
            if not JEEDOM_SOCKET_MESSAGE.empty():
                logging.debug("Message received in socket JEEDOM_SOCKET_MESSAGE")
                message = JEEDOM_SOCKET_MESSAGE.get().decode('utf-8')
                message = json.loads(message)
                if message['apikey'] != _apikey:
                    logging.error("Invalid apikey from socket : %s", message)
                    return
                logging.debug('Received command from jeedom : %s', message['cmd'])
                if message['cmd'] == 'add':
                    logging.debug('Add device : %s', message['device'])
                    if 'id' in message['device'] and 'profils' in message['device']:
                        globals.KNOWN_DEVICES[message['device']['id']] = message['device']['profils']
                elif message['cmd'] == 'remove':
                    logging.debug('Remove device : %s', message['device'])
                    if 'id' in message['device']:
                        del globals.KNOWN_DEVICES[message['device']['id']]
                elif message['cmd'] == 'learnin':
                    logging.debug('Enter in learn mode')
                    globals.LEARN_MODE = True
                    globals.JEEDOM_COM.send_change_immediate({'learn_mode': 1})
                elif message['cmd'] == 'learnout':
                    logging.debug('Leave learn mode')
                    globals.LEARN_MODE = False
                    globals.JEEDOM_COM.send_change_immediate({'learn_mode': 0})
                elif message['cmd'] == 'excludein':
                    logging.debug('Enter exclude mode')
                    globals.EXCLUDE_MODE = True
                    globals.JEEDOM_COM.send_change_immediate({'exclude_mode': 1})
                elif message['cmd'] == 'excludeout':
                    logging.debug('Leave exclude mode')
                    globals.EXCLUDE_MODE = False
                    globals.JEEDOM_COM.send_change_immediate({'exclude_mode': 0})
                elif message['cmd'] == 'send':
                    logging.debug('Send command')
                    PacketAnalyser.send_command(message)
                elif message['cmd'] == 'learn':
                    logging.debug('Learn command')
                    learn.learn_packet_message(message)
                elif message['cmd'] == 'logdebug':
                    logging.info('Passage du demon en mode debug force')
                    log = logging.getLogger()
                    for hdlr in log.handlers[:]:
                        log.removeHandler(hdlr)
                    jeedom_utils.set_log_level('debug')
                    logging.debug('<----- La preuve ;)')
                elif message['cmd'] == 'lognormal':
                    logging.info('Passage du demon en mode de log initial')
                    log = logging.getLogger()
                    for hdlr in log.handlers[:]:
                        log.removeHandler(hdlr)
                    jeedom_utils.set_log_level(globals.LOG_LEVEL)
        except Exception as e:
            logging.error("Exception on socket : %s", e)
        time.sleep(0.02)


def handler(signum=None, frame=None):
    logging.debug("Signal %i caught, exiting...", signum)
    shutdown()


def shutdown():
    logging.debug("Shutdown")
    logging.debug("Removing PID file %s", _pidfile)
    try:
        communicator.stop()
    except:
        pass
    try:
        os.remove(_pidfile)
    except:
        pass
    try:
        jeedom_socket.close()
    except:
        pass
    logging.debug("Exit 0")
    sys.stdout.flush()
    os._exit(0)


_log_level = "error"
_socket_port = 55006
_socket_host = '127.0.0.1'
_pidfile = '/tmp/openenoceand.pid'
_device = 'auto'
_apikey = ''
_callback = ''
_cycle = 0.3

parser = argparse.ArgumentParser(description='OpenEnocean Daemon for Jeedom plugin')
parser.add_argument("--device", help="Device", type=str)
parser.add_argument("--socketport", help="Socketport for server", type=str)
parser.add_argument("--loglevel", help="Log Level for the daemon", type=str)
parser.add_argument("--callback", help="Callback", type=str)
parser.add_argument("--apikey", help="Apikey", type=str)
parser.add_argument("--cycle", help="Cycle to send event", type=str)
parser.add_argument("--pid", help="Pid file", type=str)
args = parser.parse_args()

if args.device:
    _device = args.device
if args.socketport:
    _socket_port = int(args.socketport)
if args.loglevel:
    _log_level = args.loglevel
if args.callback:
    _callback = args.callback
if args.apikey:
    _apikey = args.apikey
if args.pid:
    _pidfile = args.pid
if args.cycle:
    _cycle = float(args.cycle)

jeedom_utils.set_log_level(_log_level)
globals.LOG_LEVEL = _log_level
logging.info('Start openenoceand')
logging.info('Log level : %s', _log_level)
logging.info('Socket port : %s', _socket_port)
logging.info('Socket host : %s', _socket_host)
logging.info('PID file : %s', _pidfile)
logging.info('Callback : %s', _callback)
logging.info('Cycle : %s', _cycle)

if _device == 'auto':
    _device = jeedom_utils.find_tty_usb('0403', '6001', 'EnOcean')

if _device is None:
    _device = jeedom_utils.find_tty_usb('0403', '6001', 'ftdi')

if _device is None:
    logging.error('No device found')
    shutdown()
else:
    logging.info('Find device : %s', _device)

globals.DEVICE = _device
signal.signal(signal.SIGINT, handler)
signal.signal(signal.SIGTERM, handler)

import jeedom.openenocean.resources.openenoceand.enocean.utils
from jeedom.openenocean.resources.openenoceand.enocean.communicators.serialcommunicator import SerialCommunicator
from jeedom.openenocean.resources.openenoceand.enocean.communicators.arubacommunicator import ArubaCommunicator
from jeedom.openenocean.resources.openenoceand.enocean.protocol.constants import PACKET
from jeedom.openenocean.resources.openenoceand.enocean.protocol.packet import Packet
from jeedom.openenocean.resources.openenoceand.enocean import packet as PacketAnalyser
from jeedom.openenocean.resources.openenoceand.enocean import learn as learn

try:
    jeedom_utils.write_pid(str(_pidfile))
    globals.JEEDOM_COM = jeedom_com(apikey=_apikey, url=_callback, cycle=_cycle)
    if not globals.JEEDOM_COM.test():
        logging.error('Network communication issues. Please fixe your Jeedom network configuration.')
        shutdown()
    jeedom_socket = jeedom_socket(port=_socket_port, address=_socket_host)
    listen()
except Exception as e:
    logging.error('Fatal error : %s', e)
    logging.debug(traceback.format_exc())
    shutdown()
