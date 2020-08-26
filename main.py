from pyterra.client import Terraria
from pyterra.packet_builder import Player

terraria = Terraria("127.0.0.1")
terraria.connect(Player(
    "Cat"
))

terraria.run()

