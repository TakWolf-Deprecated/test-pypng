#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import struct
import zlib

import png


def analyze_png_bytes(source_path, output_path):
    """
    Analyze PNG byte differences to confirm if zlib compression is the cause.
    Returns True if pixel data matches (even if compressed bytes differ).
    """
    print("\n[Analyze] Checking PNG byte differences...")

    # --- Read IDAT chunks from source PNG ---
    with source_path.open('rb') as f:
        sig = f.read(8)
        if sig != b'\x89PNG\r\n\x1a\n':
            print("ERROR: Source file is not a valid PNG")
            return False
        idat_chunks_src = []
        while True:
            length_data = f.read(4)
            if len(length_data) < 4:
                break
            length = struct.unpack('!I', length_data)[0]
            chunk_type = f.read(4)
            chunk_data = f.read(length)
            f.read(4)  # CRC
            if chunk_type == b'IDAT':
                idat_chunks_src.append(chunk_data)
            elif chunk_type == b'IEND':
                break
    src_idat = b''.join(idat_chunks_src)
    print(f"  Original IDAT total size: {len(src_idat)} bytes")

    # --- Read IDAT chunks from output PNG ---
    with output_path.open('rb') as f:
        f.read(8)
        idat_chunks_out = []
        while True:
            length_data = f.read(4)
            if len(length_data) < 4:
                break
            length = struct.unpack('!I', length_data)[0]
            chunk_type = f.read(4)
            chunk_data = f.read(length)
            f.read(4)
            if chunk_type == b'IDAT':
                idat_chunks_out.append(chunk_data)
            elif chunk_type == b'IEND':
                break
    out_idat = b''.join(idat_chunks_out)
    print(f"  Output IDAT total size: {len(out_idat)} bytes")

    # --- zlib version info ---
    print(f"  zlib version: {zlib.ZLIB_VERSION} (runtime)")

    # --- Compare compressed bytes ---
    if src_idat == out_idat:
        print("\n[OK] IDAT compressed data is identical.")
    else:
        print("\n[WARN] IDAT compressed data differs (possible zlib non-determinism).")

    # --- Decompress and compare raw pixel data ---
    src_pixels = zlib.decompress(src_idat)
    out_pixels = zlib.decompress(out_idat)
    print(f"  Decompressed source pixel size: {len(src_pixels)} bytes")
    print(f"  Decompressed output pixel size: {len(out_pixels)} bytes")

    if src_pixels == out_pixels:
        print("[OK] Decompressed pixel data is identical!")
        if src_idat != out_idat:
            print("-> Conclusion: zlib compression output differs, but image content is lossless.")
            print("   Tests should compare pixel data, not raw bytes.")
        return True
    else:
        print("[ERROR] Decompressed pixel data differs! Deeper issue exists.")
        diff_pos = next((i for i, (a, b) in enumerate(zip(src_pixels, out_pixels)) if a != b), None)
        if diff_pos is not None:
            print(f"   First difference at byte offset: {diff_pos}")
        return False


def main():
    project_root_dir = Path(__file__).parent.joinpath('..').resolve()

    # Original PNG file (already formatted by pypng or any valid PNG)
    source_file_path = project_root_dir.joinpath('assets', 'test.png')

    # Output file
    output_file_path = project_root_dir.joinpath('build', 'test.png')
    output_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Read and rewrite PNG using pypng
    width, height, rows, info = png.Reader(filename=source_file_path).read()
    with output_file_path.open('wb') as file:
        writer = png.Writer(width, height, **info)
        writer.write(file, rows)

    # Analyze the byte differences
    pixels_match = analyze_png_bytes(source_file_path, output_file_path)

    # If pixel data is identical, the test passes (even if compressed bytes differ)
    if not pixels_match:
        raise AssertionError("Pixel data mismatch between source and rewritten PNG!")

    print("\n[PASS] Test completed successfully.")


if __name__ == '__main__':
    main()
