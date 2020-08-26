import socket

from .terraria_types import (CLIENT_NAME, CONNECT,
                             DISCONNECT, SET_USER_SLOT,
                             PLAYER_INFO)
from .packet_builder import (PacketBuilder, PacketReader,
                             Player)


class Terraria:
    def __init__(self, ip, port=7777):
        self.ip = ip
        self.port = port
        self.sock = socket.socket()

        self.player = None
        self.endianess = "little"
        self.client_name = CLIENT_NAME

        self.running = False

    def connect(self, player):
        self.player = player

        self.sock.connect((self.ip, self.port))
        self.do_handshake()

    def send_packet(self, type_, payload):
        """
        Message struct:
            full length - 2 bytes unsigned
            packet type - 1 byte unsigned
            payload - ?
        """

        if hasattr(payload, 'serialize'):
            payload = payload.serialize()  # noqa

        length = 3+len(payload)

        data = length.to_bytes(2, self.endianess)+bytes((type_, ))+payload

        self.sock.sendall(data)

    def recvall(self, length):
        data = self.sock.recv(length)

        while len(data) < length:
            data += self.sock.recv(length-len(data))

        return data

    def read_packet(self):
        length = PacketReader(self.recvall(2)).read_int(2)
        type_ = PacketReader(self.recvall(1)).read_int(1)
        payload = self.recvall(length - 3)

        return type_, payload

    def do_handshake(self):
        builder = PacketBuilder()
        builder.add_string(self.client_name)

        self.send_packet(CONNECT, PacketBuilder().add_string(self.client_name).to_bytes())

    def run(self):
        self.running = True

        while self.running:
            type_, packet = self.read_packet()

            if type_ == SET_USER_SLOT:
                self.player.player_id = packet[0]

                self.send_packet(PLAYER_INFO, self.player)

