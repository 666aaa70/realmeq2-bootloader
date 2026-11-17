#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Offline one-byte boot padding change for the exact tested RMX2117 F.12 image."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess

ORIGINAL = "06e21577d95029c898e8e4d7d8b1bd44afb80e72642566399bbdeb482d588113"
PATCHED = "d30d34b27209aa8d7fe472bf573c31733c26a0e3d6364f419c56b4715fab187b"
OFFSET = 0x1322000


def prepare(original: bytes) -> bytes:
    if len(original) != 33554432 or hashlib.sha256(original).hexdigest() != ORIGINAL:
        raise ValueError("Input is not the exact tested RMX2117 F.12 boot image")
    magic, major, minor, data_size, vbmeta_offset, vbmeta_size = struct.unpack(
        ">4sIIQQQ", original[-64:-28]
    )
    if (magic, major, minor) != (b"AVBf", 1, 0):
        raise ValueError("Unexpected AVB footer")
    if not (data_size <= vbmeta_offset < vbmeta_offset + vbmeta_size <= OFFSET
            and OFFSET + 4096 <= len(original) - 4096):
        raise ValueError("Selected offset is outside the expected unused padding")
    if original[OFFSET:OFFSET + 4096] != bytes(4096):
        raise ValueError("Padding is not zero")
    patched = bytearray(original)
    patched[OFFSET] = 1
    if patched[:OFFSET] != original[:OFFSET] or patched[OFFSET + 1:] != original[OFFSET + 1:]:
        raise ValueError("More than the intended byte changed")
    if hashlib.sha256(patched).hexdigest() != PATCHED:
        raise ValueError("Unexpected output hash")
    return bytes(patched)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path, help="New file named boot.img in a dedicated output directory")
    parser.add_argument("--avbtool", default="avbtool")
    args = parser.parse_args()
    if args.output.name != "boot.img":
        parser.error("Output basename must be boot.img for AVB descriptor verification")
    if not shutil.which(args.avbtool):
        parser.error("avbtool is required; install it before preparing the image")
    if args.input.resolve() == args.output.resolve():
        parser.error("Input and output must differ")
    patched = prepare(args.input.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as handle:
        handle.write(patched)
    subprocess.run([args.avbtool, "verify_image", "--image", str(args.output)], check=True)
    print(json.dumps({"bytes": len(patched), "sha256": PATCHED,
                      "changed_offset": hex(OFFSET), "old_byte": 0, "new_byte": 1,
                      "device_written": False, "avb_verified": True}, indent=2))


if __name__ == "__main__":
    main()
