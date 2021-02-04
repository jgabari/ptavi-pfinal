#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa cliente que abre un socket a un servidor
"""

import socket
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import time


# Clase para procesar el xml
class XMLHandler(ContentHandler):
    def __init__(self):
        self.content = {}
        self.names = {'account': ['username', 'passwd'],
                      'uaserver': ['ip', 'puerto'],
                      'rtpaudio': ['puerto'],
                      'regproxy': ['ip', 'puerto'],
                      'log': ['path'],
                      'audio': ['path']}

    def startElement(self, name, attrs):
        if name in list(self.names):
            auxdict = {}
            for attr in self.names[name]:
                auxdict[attr] = attrs.get(attr, "")
                self.content[name] = auxdict

    def get_tags(self):
        return self.content


def writelog(data, log):
    hora = time.strftime('%H', time.gmtime(time.time()))
    minuto = time.strftime('%M', time.gmtime(time.time()))
    segundo = time.strftime('%S', time.gmtime(time.time()))
    ss = int(hora)*3600 + int(minuto)*60 + int(segundo)
    fecha = time.strftime('%Y-%m-%d ', time.gmtime(time.time()))
    fich = open(log, 'a')
    fich.write(fecha + str(ss) + ' ' + data + '\r\n')
    fich.close()


if __name__ == '__main__':
    try:
        CONFXML = sys.argv[1]
        METHOD = sys.argv[2]
        OPTION = sys.argv[3]
    except IndexError:
        sys.exit("Usage: python3 uaclient.py config method option")

    parser = make_parser()
    xHandler = XMLHandler()
    parser.setContentHandler(xHandler)
    parser.parse(open(CONFXML))

    config = xHandler.get_tags()

    writelog('Starting...', config['log']['path'])

    CLIENT_NAME = config['account']['username']
    CLIENT_IP = config['uaserver']['ip']
    CLIENT_PORT = config['uaserver']['puerto']

    RTP_PORT = config['rtpaudio']['puerto']

    SDP = '\r\nv=0\r\no=' + CLIENT_NAME + ' ' + CLIENT_IP + '\r\n'
    SDP += 's=misesion\r\nt=0\r\nm=audio ' + RTP_PORT + ' RTP\r\n'
    content_type = 'Content-Type: application/sdp\r\n'
    content_length = 'Content-Length: ' + str(len(SDP)) + '\r\n'

    # Contenido que vamos a enviar
    if METHOD == 'REGISTER':
        LINE = 'REGISTER sip:' + CLIENT_NAME + ':' + CLIENT_PORT +\
               ' SIP/2.0\r\n'
        LINE += 'Expires: ' + str(OPTION)
    elif METHOD == 'INVITE':
        LINE = 'INVITE sip:' + OPTION + ' SIP/2.0\r\n'
        LINE += content_type + content_length + SDP
    elif METHOD == 'BYE':
        LINE = 'BYE sip:' + OPTION + ' SIP/2.0\r\n'

    ACK_LINE = 'ACK sip:' + OPTION + ' SIP/2.0\r\n'

    # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            my_socket.connect((config['regproxy']['ip'],
                               int(config['regproxy']['puerto'])))
        except ConnectionRefusedError:
            error = 'Error: No server listening at ' +\
                    config['regproxy']['ip'] + ' port ' +\
                    config['regproxy']['puerto']
            writelog(error, config['log']['path'])
            sys.exit('Conexión Fallida.')

        print("Enviando:\r\n" + LINE)
        my_socket.send(bytes(LINE, 'utf-8') + b'\r\n')
        sent = 'Sent to ' + config['regproxy']['ip'] + ':' +\
               config['regproxy']['puerto'] + ':' + LINE.replace('\r\n', ' ')
        writelog(sent, config['log']['path'])
        data = my_socket.recv(1024)
        received = 'Received from ' + config['regproxy']['ip'] + ':' +\
                   config['regproxy']['puerto'] + ': ' +\
                   data.decode('utf-8').replace('\r\n', ' ')
        writelog(received, config['log']['path'])

        print('Recibido --\r\n', data.decode('utf-8'))
        if data.decode('utf-8')[: data.decode('utf-8').index('\r\n')] ==\
                "SIP/2.0 100 Trying":
            print("Enviando: " + ACK_LINE)
            my_socket.send(bytes(ACK_LINE, 'utf-8') + b'\r\n')
            sentack = 'Sent to ' + config['regproxy']['ip'] + ':' +\
                      config['regproxy']['puerto'] + ':' +\
                      ACK_LINE.replace('\r\n', ' ')
            writelog(sentack, config['log']['path'])

        writelog('Finishing.', config['log']['path'])
        print("Terminando socket...")

    print("Fin.")
