from pathlib import Path

import png


def main():
    project_root_dir = Path(__file__).parent.joinpath('..').resolve()

    # Already format by pypng
    source_file_path = project_root_dir.joinpath('assets', 'test.png')

    # New format output
    output_file_path = project_root_dir.joinpath('build', 'test.png')
    output_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Reformat
    width, height, rows, info = png.Reader(filename=source_file_path).read()
    with output_file_path.open('wb') as file:
        writer = png.Writer(width, height, **info)
        writer.write(file, rows)

    # Check Equals
    assert source_file_path.read_bytes() == output_file_path.read_bytes()


if __name__ == '__main__':
    main()
