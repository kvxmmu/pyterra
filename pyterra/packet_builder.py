from struct import pack, unpack


def get_signed_or_unsigned(unsigned, sign):
    return sign.upper() if unsigned else sign


SOFTCORE = 0
MEDIUMCORE = 1
HARDCORE = 2
EXTRA_ACCESSORY = 4
CREATIVE = 8


class PacketBuilder:
    def __init__(self, endianess="little"):
        self.endianess = endianess

        self.buffer = bytearray()

    def pack(self, fmt, *args):
        return pack(("<" if self.endianess == "little" else ">") + fmt, *args)

    def add_single(self, single):
        """
            Add single precision float to the buffer
        """

        self.buffer.extend(self.pack("f", single))

        return self

    def add_byte(self, i8):
        self.buffer.append(i8)

        return self

    def add_buffer(self, buffer):
        self.buffer.extend(buffer.serialize())

        return self

    def add_int16(self, i16, unsigned=True):
        sign = get_signed_or_unsigned(unsigned, 'h')

        self.buffer.extend(self.pack(sign, i16))

        return self

    def add_int32(self, i32, unsigned=True):
        sign = get_signed_or_unsigned(unsigned, 'i')

        self.buffer.extend(self.pack(sign, i32))

        return self

    def add_int64(self, i64, unsigned=True):
        sign = get_signed_or_unsigned(unsigned, 'q')

        self.buffer.extend(self.pack(sign, i64))

        return self

    def add_string(self, string, length_size=1):
        length_bytes = len(string).to_bytes(length_size, self.endianess)
        self.buffer.extend(length_bytes)

        self.buffer.extend(string if isinstance(string, bytes) else string.encode())

        return self

    def to_bytes(self):
        return bytes(self.buffer)

    def clear(self):
        self.buffer.clear()

        return self


class PacketReader:
    def __init__(self, buffer, endianess='little'):
        self.buffer = buffer
        self.endianess = endianess

    def set_buffer(self, buffer):
        self.buffer = buffer

        return self

    def unpack(self, fmt, *args):
        sign = "<" if self.endianess == "little" else ">"

        return unpack(sign + fmt, *args)

    def read_int(self, size=2, unsigned=True):
        data = int.from_bytes(self.buffer[:size], self.endianess,
                              signed=not unsigned)

        self.buffer = self.buffer[size:]

        return data

    def read_buffer(self, length):
        buffer = self.buffer[:length]

        self.buffer = self.buffer[length:]

        return buffer

    def read_byte(self):
        byte = self.buffer[0]

        self.buffer = self.buffer[1:]

        return byte

    def read_single(self):
        """
            Read single precision float from buffer
        """

        single = self.unpack("f", self.buffer[:4])  # 4 bytes length
        self.buffer = self.buffer[4:]

        return single

    def read_string(self, size_length=1,
                    auto_decode=True):
        size = self.read_int(size_length)
        string = self.buffer[:size]

        self.buffer = self.buffer[len(string):]

        if auto_decode:
            try:
                return string.decode()
            except UnicodeDecodeError:
                return string

        return string


class RGB:
    def __init__(self, red, green, blue):
        self.red = red
        self.green = green
        self.blue = blue

    def serialize(self):
        return pack("<BBB", self.red, self.green, self.blue)


white_color = RGB(255, 255, 255)
black_color = RGB(0, 0, 0)


class Player:
    def __init__(self, name,
                 skin_variant=0, hair=0,
                 hair_dye=0, hide_visuals=0,
                 hide_visuals2=0, hide_misc=0,
                 hair_color=black_color, skin_color=white_color,
                 eye_color=black_color, shirt_color=black_color,
                 under_shirt_color=black_color, pants_color=black_color,
                 difficulty_flags=MEDIUMCORE, torch_flags=0,
                 shoe_color=black_color, journey_mode=True):
        if journey_mode:
            difficulty_flags |= CREATIVE

        self.name = name
        self.skin_variant = skin_variant
        self.hair = hair
        self.hair_dye = hair_dye
        self.hide_visuals = hide_visuals
        self.hide_visuals2 = hide_visuals2
        self.hide_misc = hide_misc
        self.hair_color = hair_color
        self.skin_color = skin_color
        self.eye_color = eye_color
        self.shirt_color = shirt_color
        self.under_shirt_color = under_shirt_color
        self.pants_color = pants_color
        self.difficulty_flags = difficulty_flags
        self.torch_flags = torch_flags
        self.shoe_color = shoe_color

        self.player_id = 0

    def serialize(self):
        builder = PacketBuilder()

        return builder.add_byte(self.player_id).add_byte(
            self.skin_variant
        ).add_byte(self.hair).add_string(
            self.name
        ).add_byte(self.hair_dye).add_byte(
            self.hide_visuals
        ).add_byte(self.hide_visuals2).add_byte(
            self.hide_misc
        ).add_buffer(self.hair_color).add_buffer(
            self.skin_color
        ).add_buffer(self.eye_color).add_buffer(
            self.shirt_color
        ).add_buffer(self.under_shirt_color).add_buffer(
            self.pants_color
        ).add_buffer(self.shoe_color).add_byte(
            self.difficulty_flags
        ).add_byte(self.torch_flags).to_bytes()

