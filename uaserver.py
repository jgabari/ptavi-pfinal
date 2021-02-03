#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import socketserver
import sys
import simplertp
import secrets
import uaclient
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class EchoHandler(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """
    client_ip = ''
    client_port = 0

    def handle(self):
        # Escribe dirección y puerto del cliente (de tupla client_address)
        send_audio = False
        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()
            uaclient.writelog(line.decode('utf-8').replace('\r\n', ' '), config['log']['path'])
            if line.decode('utf-8').split(' ')[0] == 'INVITE':
                SDP = '\r\nv=0\r\no=' + config['account']['username'] + ' ' + config['uaserver']['ip'] + '\r\n'
                SDP += 's=misesion\r\nt=0\r\nm=audio ' + config['rtpaudio']['puerto'] + ' RTP\r\n'
                content_type = 'Content-Type: application/sdp\r\n'
                content_length = 'Content-Length: ' + str(len(SDP)) + '\r\n'

                answer = "SIP/2.0 100 Trying\r\n\r\nSIP/2.0 180 Ringing\r\n\r\nSIP/2.0 200 OK\r\n\r\n" + content_type + content_length + SDP + "\r\n"
                self.wfile.write(bytes(answer, 'utf-8'))
                uaclient.writelog(answer.replace('\r\n', ' '), config['log']['path'])

            elif line.decode('utf-8').split(' ')[0] == 'ACK':
                send_audio = True
            elif line.decode('utf-8').split(' ')[0] == 'BYE':
                answer = "SIP/2.0 200 OK\r\n\r\n"
                self.wfile.write(bytes(answer, 'utf-8'))
                uaclient.writelog(answer.replace('\r\n', ' '), config['log']['path'])
            elif line.decode('utf-8').split(' ')[0] != ('INVITE', 'ACK', 'BYE'):
                answer = "SIP/2.0 405 Method Not Allowed\r\n\r\n"
                self.wfile.write(bytes(answer, 'utf-8'))
                uaclient.writelog(answer.replace('\r\n', ' '), config['log']['path'])
            else:
                answer = "SIP/2.0 400 Bad Request\r\n\r\n"
                self.wfile.write(bytes(answer, 'utf-8'))
                uaclient.writelog(answer.replace('\r\n', ' '), config['log']['path'])
            if send_audio:
                # Extraemos del sdp la dirección a la que enviar el audio
                while 1:
                    line2 = self.rfile.read()
                    cadena = line2.decode('utf-8')
                    if cadena.split('=')[0] == 'o':
                        self.client_ip = cadena.split('=')[1].split(' ')[1]
                    if cadena.split('=')[0] == 'm':
                        self.client_port = cadena.split('=')[1].split(' ')[1]
                    if not line2:
                        break
                # Enviamos el audio
                self.send_rtp()
                uaclient.writelog('Sending audio...', config['log']['path'])

            # Si no hay más líneas salimos del bucle infinito
            if not line:
                break

    def send_rtp(self):
        RTP_header = simplertp.RtpHeader()
        RTP_header.set_header(version=2, marker=secrets.randbits(1),
                              payload_type=14, ssrc=200002)
        audio = simplertp.RtpPayloadMp3(AUDIO_FILE)
        simplertp.send_rtp_packet(RTP_header, audio,
                                  self.client_ip, self.client_port)


if __name__ == "__main__":
    # Creamos servidor de eco y escuchamos
    try:
        CONFXML = sys.argv[1]
    except NameError:
        sys.exit('Usage: python3 uaserver.py config')

    parser = make_parser()
    xHandler = uaclient.XMLHandler()
    parser.setContentHandler(xHandler)
    parser.parse(open(CONFXML))

    config = xHandler.get_tags()

    AUDIO_FILE = open(config['audio']['path'])
    serv = socketserver.UDPServer((config['uaserver']['ip'], config['uaserver']['puerto']), EchoHandler)
    print("Listening...")
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print('Server ended.')
