# -*- encoding: utf-8 -*-
import logging


def parse(action, packet):
    logging.debug("Its a VLD message")
    for k in packet.parsed:
        action[k] = packet.parsed[k]
    if 'OV' in action:
        channel = action['IO']['raw_value']
        action['channel'+str(channel)+'-OV'] = action['OV']['raw_value']
    if 'DIV' in action and action['DIV']['raw_value'] == 1:
        for x in action:
            if x[0:2] == 'CH':
                action[x]['value'] = action[x]['raw_value']/float(10)
    if 'MV' in action:
        channel = 1
        value = action['MV']['value']
        type = 'P'
        if 'IO' in action:
            channel = action['IO']['raw_value'] + 1
        if 'UN' in action:
            if action['UN']['raw_value'] in [0, 1, 2]:
                type = 'C'
            if action['UN']['raw_value'] == 0:
                value = int(value)/float(3600000)
            elif action['UN']['raw_value'] == 1:
                value = int(value)/float(1000)
            elif action['UN']['raw_value'] == 4:
                value = int(value)*float(1000)
        action[type+str(int(channel))] = value

    return action
