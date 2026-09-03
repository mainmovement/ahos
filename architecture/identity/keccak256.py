# -*- coding: utf-8 -*-
"""Keccak-256 (Ethereum / EIP-55), not SHA3-256.

Implementation derived from Gilles Van Assche CompactFIPS202 (CC0 1.0):
https://github.com/XKCP/XKCP/blob/master/Standalone/CompactFIPS202/Python/CompactFIPS202.py
"""
from __future__ import annotations


def _rol64(a: int, n: int) -> int:
    n %= 64
    return ((a >> (64 - n)) + (a << n)) % (1 << 64)


def _keccak_f1600_on_lanes(lanes: list[list[int]]) -> list[list[int]]:
    r = 1
    for _round in range(24):
        c = [lanes[x][0] ^ lanes[x][1] ^ lanes[x][2] ^ lanes[x][3] ^ lanes[x][4] for x in range(5)]
        d = [c[(x + 4) % 5] ^ _rol64(c[(x + 1) % 5], 1) for x in range(5)]
        lanes = [[lanes[x][y] ^ d[x] for y in range(5)] for x in range(5)]
        x, y = 1, 0
        current = lanes[x][y]
        for t in range(24):
            x, y = y, (2 * x + 3 * y) % 5
            current, lanes[x][y] = lanes[x][y], _rol64(current, (t + 1) * (t + 2) // 2)
        for y in range(5):
            t = [lanes[x][y] for x in range(5)]
            for x in range(5):
                lanes[x][y] = t[x] ^ ((~t[(x + 1) % 5]) & t[(x + 2) % 5])
        for j in range(7):
            r = ((r << 1) ^ ((r >> 7) * 0x71)) % 256
            if r & 2:
                lanes[0][0] = lanes[0][0] ^ (1 << ((1 << j) - 1))
    return lanes


def _load64(b: bytes) -> int:
    return sum(b[i] << (8 * i) for i in range(8))


def _store64(a: int) -> list[int]:
    return [(a >> (8 * i)) % 256 for i in range(8)]


def _keccak_f1600(state: bytearray) -> bytearray:
    lanes = [[_load64(state[8 * (x + 5 * y): 8 * (x + 5 * y) + 8]) for y in range(5)] for x in range(5)]
    lanes = _keccak_f1600_on_lanes(lanes)
    out = bytearray(200)
    for x in range(5):
        for y in range(5):
            out[8 * (x + 5 * y): 8 * (x + 5 * y) + 8] = _store64(lanes[x][y])
    return out


def keccak256(data: bytes) -> bytes:
    """Ethereum Keccak-256 (delimited suffix 0x01)."""
    rate_bytes = 136
    state = bytearray(200)
    offset = 0
    block_size = 0
    while offset < len(data):
        block_size = min(len(data) - offset, rate_bytes)
        for i in range(block_size):
            state[i] ^= data[i + offset]
        offset += block_size
        if block_size == rate_bytes:
            state = _keccak_f1600(state)
            block_size = 0
    state[block_size] ^= 0x01
    state[rate_bytes - 1] ^= 0x80
    state = _keccak_f1600(state)
    return bytes(state[:32])
