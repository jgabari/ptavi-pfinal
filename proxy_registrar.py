#!/usr/bin/python3
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import socketserver
import sys
import json
import time
import uaclient
from xml.sax import make_parser


class SIPRegisterHandler(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """
    diccionario = {}
    format = '%Y-%m-%d %H:%M:%S'

    def handle(self):
        """
        handle method of the server class
        (all requests will be handled by this method)
        """
        self.json2registered()
        self.expiration()
        print('\r\nCliente en IP:' + str(self.client_address[0]) +
              ', puerto:' + str(self.client_address[1]) +
              ' manda:\r\n')
        text = self.rfile.read().decode('utf-8')
        print(text)

        word_list = text.split()
        if word_list[0] == 'REGISTER':
            client = word_list[1].split(':')[1]
            if client in self.diccionario:
                address = str(self.client_address[0])
                self.diccionario[client] = {'address': address}
                self.register2json()
                print('Actualizado ' + client + ' en el diccionario.\r')
            else:
                address = str(self.client_address[0])
                self.diccionario[client] = {'address': address}
                self.register2json()
                print('Añadido ' + client + ' al diccionario.\r')
            if word_list[3] == 'Expires:':
                expires_value = int(word_list[4].split('\r')[0])
                if expires_value == 0:
                    del self.diccionario[client]
                    print(client + ' se ha dado de baja.\r')
                    self.register2json()
                else:
                    expire_time = time.gmtime(time.time() + expires_value)
                    expires = time.strftime(self.format, expire_time)
                    self.diccionario[client]['expires'] = expires
                    self.register2json()
            self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
        elif word_list[0] == 'INVITE':
            self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
        elif word_list[0] == 'ACK':

        elif word_list[0] == 'BYE':
            self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
        elif word_list[0] != ('REGISTER', 'INVITE', 'ACK', 'BYE'):
            self.wfile.write(b"SIP/2.0 405 Method Not Allowed\r\n\r\n")
        else:
            self.wfile.write(b"SIP/2.0 400 Bad Request\r\n\r\n")

        print(self.diccionario)


    def expiration(self):
        """
        Look for and delete expired clients
        """
        keys = list(self.diccionario.keys())
        for client in keys:
            c_time = time.strftime(self.format, time.gmtime(time.time()))
            if 'expires' in self.diccionario[client]:
                if self.diccionario[client]['expires'] <= c_time:
                    del self.diccionario[client]
                    print('Expiró ' + client + '\r')
                    self.register2json()

    def register2json(self):
        """
        Saves the dictionary in a json file
        """
        with open('registered.json', 'w') as jsonfile:
            json.dump(self.diccionario, jsonfile, indent=4)

    def json2registered(self):
        """
        Import the dictionary from a json file if it exists
        """
        try:
            with open('registered.json', 'r') as jsonfile:
                self.diccionario = json.load(jsonfile)
        except FileNotFoundError:
            self.diccionario = self.diccionario


if __name__ == "__main__":
    # Listens at localhost ('') port puerto
    # and calls the EchoHandler class to manage the request
    try:
        CONFXML = sys.argv[1]
    except NameError:
        sys.exit('Usage: python3 proxy_registrar.py config')

    parser = make_parser()
    xHandler = uaclient.XMLHandler()
    parser.setContentHandler(xHandler)
    parser.parse(open(CONFXML))

    config = xHandler.get_tags()

    serv = socketserver.UDPServer((config['server']['ip'], config['server']['puerto']), SIPRegisterHandler)

    print("Server " + config['server']['name'] + " listening at port " + config['server']['puerto'] + "...")

    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Server ended.")
