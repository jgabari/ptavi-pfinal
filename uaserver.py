#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import socketserver
import sys
import simplertp
import secrets


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
            if line.decode('utf-8').split(' ')[0] == 'INVITE':
                self.wfile.write(b"SIP/2.0 100 Trying\r\n\r\n" +
                                 b"SIP/2.0 180 Ringing\r\n\r\n" +
                                 b"SIP/2.0 200 OK\r\n\r\n")
            elif line.decode('utf-8').split(' ')[0] == 'ACK':
                send_audio = True
            elif line.decode('utf-8').split(' ')[0] == 'BYE':
                self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
            else:
                self.wfile.write(b"SIP/2.0 405 Method Not Allowed\r\n\r\n")
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
        SERVER_IP = sys.argv[1]
        SERVER_PORT = int(sys.argv[2])
        AUDIO_FILE = sys.argv[3]
    except NameError:
        sys.exit('Usage: python3 server.py IP port audio_file')
    serv = socketserver.UDPServer((SERVER_IP, SERVER_PORT), EchoHandler)
    print("Listening...")
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print('Server ended.')
