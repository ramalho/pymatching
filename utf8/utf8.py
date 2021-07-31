"""
utf8.decode(…): The world's slowest UTF-8 decoder function.

Code to demonstrate one (mis)use of pattern matching in Python.

Also may be useful as executable pseudocode to explain how the
UTF-8 encoding/decoding algorithm works.

Maybe one day Python can have a syntax for efficient pattern matching
of bit patterns, like Erlang has:

https://erlang.org/doc/programming_examples/bit_syntax.html

Meanwhile, this example expands bytes into lists of bits.
That makes everything super slow, but allows the use of
`match/case` with a list of bits as the subject.

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
                case [0, *rest]:                    # 0xxx_xxxx
                    out_bits = rest                 # -> 7 bits
                case [1, 1, 0, *head]:              # 110x_xxxx
                    tail = unpack(next(stream), 6)  # 10xx_xxxx
                    out_bits = head + tail          # -> 11 bits
                case [1, 1, 1, 0, *head]:           # 1110_xxxx
                    t0 = unpack(next(stream), 6)    # 10xx_xxxx
                    t1 = unpack(next(stream), 6)    # 10xx_xxxx
                    out_bits = head + t0 + t1       # -> 16 bits
                case [1, 1, 1, 1, 0, *head]:        # 1111_0xxx
                    t0 = unpack(next(stream), 6)    # 10xx_xxxx
                    t1 = unpack(next(stream), 6)    # 10xx_xxxx
                    t2 = unpack(next(stream), 6)    # 10xx_xxxx
                    out_bits = head + t0 + t1 + t2  # -> 21 bits
                case _:
                    bit_str = f'{pack(bits):_b}'
                    raise ValueError(f'Invalid UTF-8 start pattern: {bit_str}')
        except StopIteration:
            raise ValueError('Incomplete UTF-8 byte sequence')
        out.append(chr(pack(out_bits)))
    return ''.join(out)


def encode(text: str) -> bytes:
    out = bytearray()
    for char in text:
        code = ord(char)
        if code < 0x80:
            out.append(code)                             # 0xxx_xxxx
        elif 0x80 <= code < 0x800:
            head = code >> 6 | 0b1100_0000               # 110x_xxxx
            tail = code & 0b11_1111 | 0b1000_0000        # 10xx_xxxx
            out.extend([head, tail])
        elif 0x800 <= code < 0x1_0000:
            head = code >> 12 | 0b1110_0000              # 1110_xxxx
            body = code >> 6 & 0b11_1111 | 0b1000_0000   # 10xx_xxxx
            tail = code & 0b11_1111 | 0b1000_0000        # 10xx_xxxx
            out.extend([head, body, tail])
        else:
            head = code >> 18 | 0b1111_0000              # 1111_0xxx
            neck = code >> 12 & 0b11_1111 | 0b1000_0000  # 10xx_xxxx
            body = code >> 6 & 0b11_1111 | 0b1000_0000   # 10xx_xxxx
            tail = code & 0b11_1111 | 0b1000_0000        # 10xx_xxxx
            out.extend([head, neck, body, tail])
    return bytes(out)
