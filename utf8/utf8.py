"""
utf8.decode: The world's slowest UTF-8 decoder

Crated only to demonstrate one (mis)use of pattern matching in Python.

Also may be useful as executable pseudocode to explain how
the UTF-8 encoding/decoding algorithm work.

Maybe one day we can have an efficient syntax for matching bit patterns,
like Erlang has:

https://erlang.org/doc/programming_examples/bit_syntax.html

"""

def unpack(octet: int, width: int = 8) -> list[int]:
    bits = [0] * width
    for i in range(width):
        bits[i] = octet & 1
        octet >>= 1
    return list(reversed(bits))


def pack(bits: list[int]) -> int:
    octet = 0
    for i, bit in enumerate(reversed(bits)):
        octet += 2 ** i * bit
    return octet


def decode(octets: bytes) -> str:
    stream = iter(octets)
    out: list[str] = []
    while True:
        try:
            bits = unpack(next(stream))
        except StopIteration:
            break
        try:
            match bits:
                case [0, *rest]:
                    out_bits = rest
                case [1, 1, 0, *rest]:
                    tail = unpack(next(stream), 6)
                    out_bits = rest + tail
                case [1, 1, 1, 0, *rest]:
                    t0 = unpack(next(stream), 6)
                    t1 = unpack(next(stream), 6)
                    out_bits = rest + t0 + t1
                case [1, 1, 1, 1, 0, *rest]:
                    t0 = unpack(next(stream), 6)
                    t1 = unpack(next(stream), 6)
                    t2 = unpack(next(stream), 6)
                    out_bits = rest + t0 + t1 + t2
                case _:
                    raise ValueError(f'Invalid UTF-8 bit pattern: {pack(bits):_b}')
        except StopIteration:
            raise ValueError('Incomplete UTF-8 byte sequence')
        out.append(chr(pack(out_bits)))

    return ''.join(out)


def encode(text: str) -> bytes:
    out = bytearray()
    for char in text:
        code = ord(char)
        if code < 0x80:
            out.append(code)
        elif 0x80 <= code < 0x800:
            head = code >> 6 | 0b1100_0000
            tail = code & 0b11_1111 | 0b1000_0000
            out.extend([head, tail])
        elif 0x800 <= code < 0x1_0000:
            head = code >> 12 | 0b1110_0000
            middle = code >> 6 & 0b11_1111 | 0b1000_0000
            tail = code & 0b11_1111 | 0b1000_0000
            out.extend([head, middle, tail])
        else:
            head = code >> 18 | 0b1111_0000
            neck = code >> 12 & 0b11_1111 | 0b1000_0000
            middle = code >> 6 & 0b11_1111 | 0b1000_0000
            tail = code & 0b11_1111 | 0b1000_0000
            out.extend([head, neck, middle, tail])
    return bytes(out)
