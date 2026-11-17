#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Offline, exact-input RMX2117 F.12 variant of the Max_Goblin boot1 layout patch.

Method: Shocked-Cat/oppo-mtk-fastboot-unlock, path_preloader.py.
Never opens a device or modifies the input. Other firmware is intentionally refused.
"""
import argparse
import hashlib
import json
from pathlib import Path

ORIGINAL = "deee5b7ff2e8c3a42c663b47314fa01135c0e2d0e1ee9842fd26594f910fca89"
PATCHED = "c5359d4b96ef1000fcf4cf73046df72cc55165e7b6fce3bec04db50cb40ef022"


def prepare(original: bytes) -> bytes:
    if len(original) != 0x400000 or hashlib.sha256(original).hexdigest() != ORIGINAL:
        raise ValueError("Input is not the exact tested 4 MiB RMX2117 F.12 boot1 backup")
    if original[0x131C:0x1329] != b"AND_ROMINFO_v":
        raise ValueError("Unexpected ROMINFO layout")
    raw = original[0x1000:len(original) - 0x3000]
    flag = original[0x131C:0x131C + 0x78]
    patched = bytearray(original)
    patched[0x1000:] = bytes(len(original) - 0x1000)
    patched[0x2000:0x2000 + len(raw)] = raw
    for offset, value in ((0x20D, 0x20), (0x21D, 0x20), (0x211, 0x10),
                          (0x212, 0x10), (0x221, 0x10), (0x222, 0x10)):
        patched[offset] = value
    patched[0x1000:0x1000 + len(flag)] = flag
    patched[0x104C] = 0
    if patched[0x2000:0x2000 + len(raw)] != raw:
        raise ValueError("Relocated payload differs")
    if hashlib.sha256(patched).hexdigest() != PATCHED:
        raise ValueError("Output differs from the fully read-back tested image")
    return bytes(patched)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    patched = prepare(args.input.read_bytes())
    if args.input.resolve() == args.output.resolve():
        parser.error("Input and output must differ")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as handle:
        handle.write(patched)
    print(json.dumps({"bytes": len(patched), "sha256": PATCHED,
                      "device_written": False}, indent=2))


if __name__ == "__main__":
    main()
