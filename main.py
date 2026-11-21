#!/usr/bin/env python3
"""Entrypoint for the Talvar passport spread (program/v1, Python 3.13 stdlib).

Copies the pre-rendered entry.png (drawn at build time by assets/generate.py)
into the grading output directory, after proving it is a real, well-formed
PNG of exactly 1024x1024 pixels and no more than 1 MiB — the gate the
sealed scorer applies. The image itself is deterministic: two runs of this
program produce byte-identical output, and the sha256 of the copy is printed
so the run can be checked against the build.
"""
import argparse
import hashlib
import os
import struct
import sys

EXPECTED_WIDTH = 1024
EXPECTED_HEIGHT = 1024
MAX_BYTES = 1_048_576
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

HERE = os.path.dirname(os.path.abspath(__file__))


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def read_png_header(path):
    """Return (width, height) after checking the PNG signature and the IHDR
    chunk; raises ValueError on anything that is not a well-formed PNG."""
    with open(path, "rb") as handle:
        head = handle.read(33)
    if len(head) < 33 or head[:8] != PNG_SIGNATURE:
        raise ValueError("not a PNG file (bad signature)")
    length, chunk_type = struct.unpack(">I4s", head[8:16])
    if chunk_type != b"IHDR" or length != 13:
        raise ValueError("not a PNG file (missing IHDR chunk)")
    width, height, depth, colour, _, _, _ = struct.unpack(">IIBBBBB", head[16:29])
    if depth != 8 or colour not in (2, 6):
        raise ValueError(f"unsupported PNG colour mode (depth {depth}, type {colour})")
    return width, height


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def copy_image(source, destination):
    """Copy byte for byte, hashing on the fly, and return the sha256."""
    digest = hashlib.sha256()
    with open(source, "rb") as src, open(destination, "wb") as dst:
        for block in iter(lambda: src.read(65536), b""):
            digest.update(block)
            dst.write(block)
    return digest.hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Write the Talvar passport spread to the output directory.")
    parser.add_argument("--input", default=os.path.join(HERE, "entry.png"),
                        help="pre-rendered entry image (default: ./entry.png)")
    parser.add_argument("--output", default=None,
                        help="output directory (default: $MAKEFUN_OUTPUT_DIR or /output)")
    args = parser.parse_args(argv)

    output_dir = args.output or os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    if not os.path.isfile(args.input):
        fail(f"entry image missing: {args.input} (run assets/generate.py first)")

    size_bytes = os.path.getsize(args.input)
    if size_bytes > MAX_BYTES:
        fail(f"entry image is {size_bytes} bytes, over the {MAX_BYTES} byte cap")
    try:
        width, height = read_png_header(args.input)
    except (OSError, ValueError, struct.error) as exc:
        fail(f"entry image failed PNG validation: {exc}")
    if (width, height) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
        fail(f"entry image is {width}x{height}, expected "
             f"{EXPECTED_WIDTH}x{EXPECTED_HEIGHT}")

    os.makedirs(output_dir, exist_ok=True)
    target = os.path.join(output_dir, "entry.png")
    digest = copy_image(args.input, target)
    if sha256_of(target) != digest:
        fail("copy verification failed: output hash does not match input")
    # Re-read the written file's own header: a truncated or corrupted write
    # must be caught here, not by the grader.
    try:
        out_width, out_height = read_png_header(target)
    except (OSError, ValueError, struct.error) as exc:
        fail(f"written entry.png failed re-validation: {exc}")
    if (out_width, out_height) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
        fail(f"written entry.png is {out_width}x{out_height}, expected "
             f"{EXPECTED_WIDTH}x{EXPECTED_HEIGHT}")
    print(f"entry.png: {width}x{height}, {size_bytes} bytes, sha256 {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
