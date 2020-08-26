from uuid import uuid4

import socket

from .terraria_types import (CLIENT_NAME, CONNECT,
                             DISCONNECT, SET_USER_SLOT,
                             PLAYER_INFO, CLIENT_UUID,
                             PLAYER_HP, PLAYER_MANA,
                             PLAYER_INVENTORY_SLOT, REQUEST_WORLD_DATA,
                             REQUEST_ESSENTIAL_TILES, WORLD_INFO,
                             SPAWN_PLAYER, UPDATE_PLAYER)
from .packet_builder import (PacketBuilder, PacketReader,
                             Player)

from time import sleep


class Terraria:
    def __init__(self, ip, port=7777):
        self.ip = ip
        self.port = port
        self.sock = socket.socket()

        self.player = None
        self.endianess = "little"
        self.client_name = CLIENT_NAME
        self.my_uuid = str(uuid4())

        self.running = False
        self.world_info = None
        self.player_spawned = False

        self.my_x = 0
        self.my_y = 0

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

    def send_uuid(self):
        self.send_packet(CLIENT_UUID, self.my_uuid.encode())

    def send_hp(self, hp, max_hp=100):
        builder = PacketBuilder().add_byte(self.player.player_id)

        self.send_packet(PLAYER_HP, builder.add_int16(hp).add_int16(
            max_hp
        ).to_bytes())

    def send_mana(self, mana, max_mana=100):
        builder = PacketBuilder().add_byte(self.player.player_id)

        self.send_packet(PLAYER_MANA, builder.add_int16(mana).add_int16(
            max_mana
        ).to_bytes())

    def send_inventory_slot(self, slot_id, stack=1,
                            prefix=0, item_netid=0):
        builder = PacketBuilder().add_byte(self.player.player_id)

        self.send_packet(PLAYER_INVENTORY_SLOT, builder.add_int16(
            slot_id
        ).add_int16(stack).add_byte(prefix).add_int16(
            item_netid
        ).to_bytes())

    def fill_inventory(self, netid=0, stack=0,
                       slot_start=0, slot_end=259):
        for slot_id in range(slot_start, slot_end):
            self.send_inventory_slot(slot_id,
                                     stack, item_netid=netid)

    def request_world_info(self):
        self.send_packet(REQUEST_WORLD_DATA, b'')

    def parse_world_info(self, packet):
        packet_reader = PacketReader(packet)

        self.world_info = {
            'time': packet_reader.read_int(4),
            'day_and_moon_info': packet_reader.read_byte(),
            'moon_phase': packet_reader.read_byte(),
            'max_tiles_x': packet_reader.read_int(2),
            'max_tiles_y': packet_reader.read_int(2),
            'spawn_x': packet_reader.read_int(2),
            'spawn_y': packet_reader.read_int(2),
            'world_surface': packet_reader.read_int(2),
            'rock_layer': packet_reader.read_int(2),
            'world_id': packet_reader.read_int(4),
            'world_name': packet_reader.read_string(),
            'game_mode': packet_reader.read_byte(),
        }

    def get_section(self):
        self.send_packet(REQUEST_ESSENTIAL_TILES, b'')

    def spawn_player(self, spawn_x=None, spawn_y=None,
                     respawn_time_remaining=0,
                     player_spawn_context=1):
        if spawn_x is None:
            spawn_x = self.world_info['spawn_x']

        if spawn_y is None:
            spawn_y = self.world_info['spawn_y']

        self.my_x = spawn_x * 16.0
        self.my_y = spawn_y * 16.0

        builder = PacketBuilder().add_byte(self.player.player_id)

        self.send_packet(SPAWN_PLAYER, builder.add_int16(spawn_x, unsigned=False).add_int16(
            spawn_y, unsigned=False
        ).add_int32(respawn_time_remaining).add_byte(player_spawn_context).to_bytes())

    def move_player(self, x_step=1, y_step=0,
                    velocity_x=0.01, velocity_y=0.0):
        builder = PacketBuilder().add_byte(self.player.player_id)

        self.send_packet(UPDATE_PLAYER, builder.add_byte(
            8 | 64
        ).add_byte(0).add_byte(0).add_byte(0).add_byte(
            0
        ).add_single(self.my_x+x_step).add_single(self.my_y+y_step).add_single(
            velocity_x
        ).add_single(velocity_y).add_single(self.my_x).add_single(
            self.my_y
        ).add_single(0.).add_single(0.).to_bytes())

        self.my_x += x_step
        self.my_y += y_step

    def run(self):
        self.running = True

        while self.running:
            type_, packet = self.read_packet()

            if type_ == SET_USER_SLOT:
                self.player.player_id = packet[0]

                self.send_packet(PLAYER_INFO, self.player)
                self.send_uuid()
                self.send_hp(100)
                self.send_mana(100)
                self.fill_inventory(0)

                self.request_world_info()
            elif type_ == WORLD_INFO:
                self.parse_world_info(packet)

                if not self.player_spawned:
                    self.get_section()
                    self.spawn_player()

                    self.player_spawned = True


