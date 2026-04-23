import zlib
import struct

def analyze_png_bytes(source_path, output_path):
    """
    喵～分析两个 PNG 文件的字节差异，确认是否为 zlib 压缩问题
    """
    print("\n🐾 正在检查 PNG 字节差异...")

    # ------------------- 读取原始 PNG 的 IDAT 数据 -------------------
    with source_path.open('rb') as f:
        sig = f.read(8)
        if sig != b'\x89PNG\r\n\x1a\n':
            print("❌ 源文件不是合法 PNG")
            return
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
    print(f"  📦 原始 IDAT 总大小: {len(src_idat)} bytes")

    # ------------------- 读取重写 PNG 的 IDAT 数据 -------------------
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
    print(f"  📦 重写 IDAT 总大小: {len(out_idat)} bytes")

    # ------------------- zlib 版本信息 -------------------
    print(f"  🧪 zlib 版本: {zlib.ZLIB_VERSION} (运行时)")
    print(f"  🧪 zlib 库名: {zlib.ZLIB_RUNTIME_VERSION}")

    # ------------------- 比较 IDAT 原始字节 -------------------
    if src_idat == out_idat:
        print("\n✅ IDAT 压缩数据完全一致！问题不在 zlib，可能是其他 chunk 差异喵。")
        # 但仍然可以继续检查像素
    else:
        print("\n⚠️  IDAT 压缩数据不同！（疑似 zlib 非确定性输出）")

    # ------------------- 解压并比较像素数据 -------------------
    src_pixels = zlib.decompress(src_idat)
    out_pixels = zlib.decompress(out_idat)
    print(f"  🎨 解压后原始像素大小: {len(src_pixels)} bytes")
    print(f"  🎨 解压后重写像素大小: {len(out_pixels)} bytes")

    if src_pixels == out_pixels:
        print("✅ 解压后的像素数据完全一致！")
        if src_idat != out_idat:
            print("👉 结论：**确认是 zlib 压缩输出不一致导致的问题喵～**")
            print("   尽管压缩流不同，但图像内容无损。测试应该比较像素而非字节。")
    else:
        print("❌ 解压后的像素数据也不一致！存在更深层的问题喵！")
        # 可以打印前几个不同字节帮助调试
        diff_pos = next((i for i, (a, b) in enumerate(zip(src_pixels, out_pixels)) if a != b), None)
        if diff_pos is not None:
            print(f"   第一个差异位置: 字节 {diff_pos}")

    # ------------------- 额外检查：文件大小 -------------------
    src_size = source_path.stat().st_size
    out_size = output_path.stat().st_size
    print(f"\n📄 源文件大小: {src_size} bytes")
    print(f"📄 重写文件大小: {out_size} bytes")
    if src_size != out_size:
        print("   （文件总大小不同，可能存在非 IDAT 块差异，例如 tEXt/chunk 顺序等）")

    return src_pixels == out_pixels


def main():
    from pathlib import Path
    import png

    project_root_dir = Path(__file__).parent.joinpath('..').resolve()
    source_file_path = project_root_dir.joinpath('assets', 'test.png')
    output_file_path = project_root_dir.joinpath('build', 'test.png')
    output_file_path.parent.mkdir(parents=True, exist_ok=True)

    # 读取 & 重写
    width, height, rows, info = png.Reader(filename=source_file_path).read()
    with output_file_path.open('wb') as file:
        writer = png.Writer(width, height, **info)
        writer.write(file, rows)

    # 喵～分析差异
    pixels_match = analyze_png_bytes(source_file_path, output_file_path)

    # 如果像素一致，我们可以认为测试通过
    if pixels_match:
        print("\n🎉 测试通过：图像内容无损，只是压缩流不同喵～")
    else:
        print("\n💥 测试失败：像素数据不一致，需要深入调查喵！")
        raise AssertionError("像素数据不一致！")


if __name__ == '__main__':
    main()
