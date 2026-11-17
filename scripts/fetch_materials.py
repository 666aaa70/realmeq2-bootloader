#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Download selected public materials and verify hashes; never connects to a phone."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import urllib.request
import zipfile


def fetch(item, output):
    dest = output / item["filename"]
    if dest.exists():
        if hashlib.sha256(dest.read_bytes()).hexdigest() == item["sha256"]:
            print(f"Already verified: {dest.name}")
            return
        raise ValueError(f"Existing file has wrong hash; preserve and inspect it: {dest}")
    with tempfile.TemporaryDirectory(prefix="realmeq2-material-") as temp:
        tmp = Path(temp) / "download"
        request = urllib.request.Request(item["download_url"], headers={"User-Agent": "realmeq2-materials"})
        with urllib.request.urlopen(request, timeout=60) as response, tmp.open("wb") as handle:
            while chunk := response.read(1024 * 1024):
                handle.write(chunk)
        if item.get("zip_member"):
            with zipfile.ZipFile(tmp) as archive:
                # Read exactly the named member; no archive path extraction.
                data = archive.read(item["zip_member"])
        else:
            data = tmp.read_bytes()
        if len(data) != item["bytes"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise ValueError(f"Download size or SHA256 mismatch: {item['name']}")
        with dest.open("xb") as handle:
            handle.write(data)
    print(f"Verified: {dest.name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("downloads"))
    parser.add_argument("--include-optional", action="store_true")
    args = parser.parse_args()
    manifest = json.loads((Path(__file__).resolve().parents[1] / "materials.json").read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    for item in manifest["downloads"]:
        if item.get("optional") and not args.include_optional:
            continue
        fetch(item, args.output)


if __name__ == "__main__":
    main()
