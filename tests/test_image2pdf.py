from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path

import pytest
from PIL import Image
from pypdf import PdfReader

from image2pdf import main


def make_image(path: Path, size: tuple[int, int] = (40, 30), mode: str = "RGB", color=(200, 40, 40)) -> Path:
    image = Image.new(mode, size, color)
    save_kwargs = {"dpi": (72, 72)} if path.suffix.lower() in {".jpg", ".jpeg", ".png"} else {}
    image.save(path, **save_kwargs)
    return path


def page_count(path: Path) -> int:
    return len(PdfReader(str(path)).pages)


def page_sizes(path: Path) -> list[tuple[float, float]]:
    sizes: list[tuple[float, float]] = []
    for page in PdfReader(str(path)).pages:
        box = page.mediabox
        sizes.append((round(float(box.width), 2), round(float(box.height), 2)))
    return sizes


def run_cli(args: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str, str]:
    code = main(args)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_one_jpg_creates_one_page_pdf(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    image = make_image(tmp_path / "scan.jpg")
    output = tmp_path / "document.pdf"

    code, _out, err = run_cli([str(image), "--output", str(output)], capsys)

    assert code == 0, err
    assert output.exists()
    assert page_count(output) == 1


def test_multiple_images_preserve_argument_order(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    first = make_image(tmp_path / "b.jpg", size=(20, 10))
    second = make_image(tmp_path / "a.jpg", size=(35, 10))
    output = tmp_path / "ordered.pdf"

    code, _out, err = run_cli([str(first), str(second), "--page-size", "original", "--output", str(output)], capsys)

    assert code == 0, err
    assert page_sizes(output) == [(20.0, 10.0), (35.0, 10.0)]


def test_sort_naturally_orders_page_names(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    page10 = make_image(tmp_path / "page10.jpg", size=(30, 10))
    page2 = make_image(tmp_path / "page2.jpg", size=(20, 10))
    page1 = make_image(tmp_path / "page1.jpg", size=(10, 10))
    output = tmp_path / "sorted.pdf"

    code, _out, err = run_cli(
        [str(page10), str(page2), str(page1), "--sort", "--page-size", "original", "--output", str(output)],
        capsys,
    )

    assert code == 0, err
    assert page_sizes(output) == [(10.0, 10.0), (20.0, 10.0), (30.0, 10.0)]


def test_output_name_without_pdf_suffix_gets_pdf(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    image = make_image(tmp_path / "scan.jpg")
    output = tmp_path / "no_suffix"

    code, _out, err = run_cli([str(image), "--output", str(output)], capsys)

    assert code == 0, err
    assert (tmp_path / "no_suffix.pdf").exists()


def test_existing_output_is_protected_without_overwrite(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    image = make_image(tmp_path / "scan.jpg")
    output = tmp_path / "document.pdf"
    output.write_bytes(b"existing")

    code, _out, err = run_cli([str(image), "--output", str(output)], capsys)

    assert code == 1
    assert "already exists" in err
    assert output.read_bytes() == b"existing"


def test_missing_file_fails_clearly(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, _out, err = run_cli([str(tmp_path / "missing.jpg"), "--output", str(tmp_path / "out.pdf")], capsys)

    assert code == 1
    assert "Missing input file" in err


def test_corrupted_image_fails_by_default(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    corrupt = tmp_path / "bad.jpg"
    corrupt.write_bytes(b"not an image")

    code, _out, err = run_cli([str(corrupt), "--output", str(tmp_path / "out.pdf")], capsys)

    assert code == 1
    assert "cannot identify image file" in err or "Unreadable image" in err


def test_corrupted_image_is_skipped_with_skip_invalid(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    good = make_image(tmp_path / "good.jpg")
    corrupt = tmp_path / "bad.jpg"
    corrupt.write_bytes(b"not an image")
    output = tmp_path / "out.pdf"

    code, _out, err = run_cli([str(corrupt), str(good), "--skip-invalid", "--output", str(output)], capsys)

    assert code == 0, err
    assert "Skipped 1 invalid" in err
    assert page_count(output) == 1


def test_transparent_png_is_flattened_and_converted(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    image = make_image(tmp_path / "transparent.png", mode="RGBA", color=(40, 80, 120, 120))
    output = tmp_path / "transparent.pdf"

    code, _out, err = run_cli([str(image), "--output", str(output)], capsys)

    assert code == 0, err
    assert page_count(output) == 1


def test_exif_rotated_image_converts_successfully(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    image = Image.new("RGB", (20, 40), (20, 140, 200))
    exif = Image.Exif()
    exif[274] = 6
    path = tmp_path / "rotated.jpg"
    image.save(path, exif=exif, dpi=(72, 72))
    output = tmp_path / "rotated.pdf"

    code, _out, err = run_cli([str(path), "--output", str(output)], capsys)

    assert code == 0, err
    assert page_count(output) == 1


@pytest.mark.parametrize("page_size", ["A4", "Letter", "original"])
def test_page_size_modes_work(tmp_path: Path, capsys: pytest.CaptureFixture[str], page_size: str) -> None:
    image = make_image(tmp_path / f"{page_size}.jpg")
    output = tmp_path / f"{page_size}.pdf"

    code, _out, err = run_cli([str(image), "--page-size", page_size, "--output", str(output)], capsys)

    assert code == 0, err
    assert page_count(output) == 1


def test_combined_mode_creates_one_multi_page_pdf(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    images = [make_image(tmp_path / f"{index}.jpg") for index in range(3)]
    output = tmp_path / "combined.pdf"

    code, _out, err = run_cli([*(str(image) for image in images), "--mode", "combined", "--output", str(output)], capsys)

    assert code == 0, err
    assert page_count(output) == 3


def test_split_mode_creates_one_pdf_per_image(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    images = [make_image(tmp_path / f"{index}.jpg") for index in range(2)]
    out_dir = tmp_path / "pdfs"
    out_dir.mkdir()

    code, _out, err = run_cli(
        [*(str(image) for image in images), "--mode", "split", "--output-dir", str(out_dir), "--title", "chapter"],
        capsys,
    )

    assert code == 0, err
    outputs = sorted(out_dir.glob("chapter-*.pdf"))
    assert [path.name for path in outputs] == ["chapter-001.pdf", "chapter-002.pdf"]
    assert [page_count(path) for path in outputs] == [1, 1]


def test_folder_input_ingestion_and_title_output(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    input_dir = tmp_path / "images"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    output_dir.mkdir()
    make_image(input_dir / "one.jpg")
    make_image(input_dir / "two.png")

    code, _out, err = run_cli(
        ["--input-dir", str(input_dir), "--output-dir", str(output_dir), "--title", "receipt"],
        capsys,
    )

    output = output_dir / "receipt.pdf"
    assert code == 0, err
    assert output.exists()
    assert page_count(output) == 2


def test_gui_module_imports_and_builds_without_mainloop() -> None:
    if sys.platform.startswith("linux"):
        pytest.skip("Tk display availability varies on Linux CI.")
    import image2pdf_gui

    try:
        root, app = image2pdf_gui.create_app()
    except tk.TclError as exc:
        pytest.skip(f"Tk is unavailable: {exc}")
    try:
        assert app.mode.get() == "combined"
        assert app.page_size.get() == "A4"
    finally:
        root.destroy()
