#!/usr/bin/env python3

import re
import sys
from pathlib import Path

GAMES = ("fe6", "fe8u", "fe8j")
ADDRESS_RE = re.compile(r"0x[0-9A-F]{8}")
SNAPSHOT_RE = re.compile(r"^[^ ]+ [0-9a-f]{40}$")


def read_linker(path):
    symbols = {}
    order = []

    for line in path.read_text().splitlines():
        if " = " not in line:
            continue
        name, value = line.removesuffix(";").split(" = ")
        if name in symbols:
            raise ValueError(f"{path}: duplicate symbol {name}")
        if not ADDRESS_RE.fullmatch(value):
            raise ValueError(f"{path}: non-normalized address {value}")
        symbols[name] = value
        order.append((int(value, 16), name))

    if order != sorted(order):
        raise ValueError(f"{path}: symbols are not sorted by address and name")

    return symbols


def read_reference(path):
    symbols = {}
    order = []

    for line in path.read_text().splitlines():
        if not line.startswith("SET_"):
            continue
        _, assignment = line.split(" ", 1)
        name, value = assignment.split(", ")
        if name in symbols:
            raise ValueError(f"{path}: duplicate symbol {name}")
        if not ADDRESS_RE.fullmatch(value):
            raise ValueError(f"{path}: non-normalized address {value}")
        symbols[name] = value
        order.append((int(value, 16), name))

    if order != sorted(order):
        raise ValueError(f"{path}: symbols are not sorted by address and name")

    return symbols


def read_defines(path):
    symbols = {}

    for line in path.read_text().splitlines():
        if not line.startswith("#define "):
            continue
        _, name, value = line.split()
        if name in symbols:
            raise ValueError(f"{path}: duplicate symbol {name}")
        if not ADDRESS_RE.fullmatch(value):
            raise ValueError(f"{path}: non-normalized address {value}")
        symbols[name] = value

    return symbols


def read_snapshot(path):
    for line in path.read_text().splitlines()[:5]:
        if "Snapshot:" in line:
            snapshot = line.split("Snapshot:", 1)[1].strip(" */@")
            if not SNAPSHOT_RE.fullmatch(snapshot):
                raise ValueError(f"{path}: invalid snapshot {snapshot!r}")
            return snapshot
    raise ValueError(f"{path}: snapshot header is missing")


def check_game(output_dir, game):
    linker_path = output_dir / f"{game}.lds"
    reference_path = output_dir / f"{game}-reference.s"
    defines_path = output_dir / f"{game}-defines.event"

    linker = read_linker(linker_path)
    reference = read_reference(reference_path)
    defines = read_defines(defines_path)
    snapshots = {
        read_snapshot(linker_path),
        read_snapshot(reference_path),
        read_snapshot(defines_path),
    }

    if len(snapshots) != 1:
        raise ValueError(f"{game}: output snapshots disagree")
    if reference != defines:
        raise ValueError(f"{game}: reference and Event Assembler symbols disagree")

    missing = {
        name: value
        for name, value in reference.items()
        if linker.get(name) != value
    }
    if missing:
        raise ValueError(f"{game}: {len(missing)} public symbols disagree with the linker script")

    print(
        f"{game}: linker={len(linker)} public={len(reference)} "
        f"snapshot={snapshots.pop()}"
    )


def main():
    output_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("output")
    for game in GAMES:
        check_game(output_dir, game)
    print("All generated outputs are internally consistent.")


if __name__ == "__main__":
    main()
