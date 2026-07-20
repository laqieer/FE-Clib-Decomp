#!/usr/bin/env python3

import argparse
import filecmp
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    from .make_linker_script import write_linker_script
    from .make_lyn_reference import (
        iter_export_symbols,
        sorted_symbols,
        write_ea_defines,
        write_lyn_reference,
    )
except ImportError:
    from make_linker_script import write_linker_script
    from make_lyn_reference import (
        iter_export_symbols,
        sorted_symbols,
        write_ea_defines,
        write_lyn_reference,
    )


@dataclass(frozen=True)
class Game:
    key: str
    repository: str
    elf_name: str


GAMES = (
    Game("fe6", "FireEmblemUniverse/fireemblem6j", "fe6.elf"),
    Game("fe8u", "laqieer/fireemblem8u", "fireemblem8.elf"),
    Game("fe8j", "laqieer/fireemblem8j", "fireemblem8.elf"),
)


def git_output(source, *args):
    return subprocess.check_output(
        ["git", "-C", os.fspath(source), *args],
        text=True,
    ).strip()


def verify_source(source, expected_ref):
    head = git_output(source, "rev-parse", "HEAD")
    if expected_ref and head != expected_ref:
        raise RuntimeError(f"{source}: expected {expected_ref}, found {head}")

    status = git_output(source, "status", "--porcelain", "--untracked-files=no")
    if status:
        raise RuntimeError(f"{source}: tracked source changes are present")

    return head


def elf_would_be_relinked(dry_run_output, elf_name):
    return bool(
        re.search(
            rf"(?:^|\s)-o\s+{re.escape(elf_name)}(?:\s|$)",
            dry_run_output,
            flags=re.MULTILINE,
        )
    )


def verify_elf_is_current(source, elf_name):
    result = subprocess.run(
        ["make", "-C", os.fspath(source), "-n", elf_name],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.returncode:
        raise RuntimeError(f"{source}: make dry-run failed:\n{result.stdout}")
    if elf_would_be_relinked(result.stdout, elf_name):
        raise RuntimeError(f"{source / elf_name}: ELF is stale; rebuild it from the requested ref")


def collect_symbols(elf_path, include_local):
    conflicts = []
    with elf_path.open("rb") as elf_file:
        symbols = sorted_symbols(
            iter_export_symbols(
                elf_file,
                include_local=include_local,
                on_conflict=lambda name, candidates: conflicts.append((name, candidates)),
            )
        )
    return symbols, conflicts


def generate_game(game, source, expected_ref, output_dir):
    head = verify_source(source, expected_ref)
    elf_path = source / game.elf_name
    if not elf_path.is_file():
        raise RuntimeError(f"{elf_path}: ELF does not exist")
    verify_elf_is_current(source, game.elf_name)

    snapshot = f"{game.repository} {head}"
    global_symbols, global_conflicts = collect_symbols(elf_path, include_local=False)
    all_symbols, all_conflicts = collect_symbols(elf_path, include_local=True)

    with (output_dir / f"{game.key}.lds").open("w", newline="\n") as outfile:
        write_linker_script(outfile, all_symbols, game.elf_name, snapshot)
    with (output_dir / f"{game.key}-reference.s").open("w", newline="\n") as outfile:
        write_lyn_reference(outfile, global_symbols, game.elf_name, snapshot)
    with (output_dir / f"{game.key}-defines.event").open("w", newline="\n") as outfile:
        write_ea_defines(outfile, global_symbols, game.elf_name, snapshot)

    print(
        f"{game.key}: {len(all_symbols)} linker symbols, "
        f"{len(global_symbols)} public symbols, "
        f"{len(all_conflicts) + len(global_conflicts)} ambiguous names skipped",
        file=sys.stderr,
    )


def expected_outputs(output_dir):
    for game in GAMES:
        yield output_dir / f"{game.key}.lds"
        yield output_dir / f"{game.key}-reference.s"
        yield output_dir / f"{game.key}-defines.event"


def main():
    parser = argparse.ArgumentParser(description="Regenerate all committed FE-Clib outputs.")
    parser.add_argument("--fe6-source", type=Path, default=Path("../fireemblem6j"))
    parser.add_argument("--fe8u-source", type=Path, default=Path("../fireemblem8u"))
    parser.add_argument("--fe8j-source", type=Path, default=Path("../fireemblem8j"))
    parser.add_argument("--fe6-ref", default="")
    parser.add_argument("--fe8u-ref", default="")
    parser.add_argument("--fe8j-ref", default="")
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    parser.add_argument(
        "--check",
        action="store_true",
        help="Regenerate into a staging directory and fail if committed outputs differ.",
    )
    args = parser.parse_args()

    sources = {
        "fe6": (args.fe6_source.resolve(), args.fe6_ref),
        "fe8u": (args.fe8u_source.resolve(), args.fe8u_ref),
        "fe8j": (args.fe8j_source.resolve(), args.fe8j_ref),
    }
    output_dir = args.output_dir.resolve()
    staging = output_dir.parent / f".{output_dir.name}.staging-{os.getpid()}"

    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    try:
        for game in GAMES:
            source, expected_ref = sources[game.key]
            generate_game(game, source, expected_ref, staging)

        if args.check:
            mismatches = [
                path.name
                for path in expected_outputs(staging)
                if not filecmp.cmp(path, output_dir / path.name, shallow=False)
            ]
            if mismatches:
                print("Generated outputs differ: " + ", ".join(mismatches), file=sys.stderr)
                return 1
            print("All generated outputs are current.", file=sys.stderr)
            return 0

        output_dir.mkdir(parents=True, exist_ok=True)
        for path in expected_outputs(staging):
            os.replace(path, output_dir / path.name)
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
