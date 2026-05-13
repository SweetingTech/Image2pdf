from __future__ import annotations

import glob
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Literal

import img2pdf
from PIL import Image, ImageOps, UnidentifiedImageError


PageSize = Literal["A4", "Letter", "original"]
OutputMode = Literal["combined", "split"]

COMMON_IMAGE_EXTENSIONS = {
    ".bmp",
    ".gif",
    ".jpeg",
    ".jpg",
    ".jp2",
    ".j2k",
    ".png",
    ".tif",
    ".tiff",
    ".webp",
}

DIRECT_IMG2PDF_FORMATS = {
    "JPEG",
    "MPO",
    "PNG",
    "TIFF",
    "JPEG2000",
}


class Image2PdfError(Exception):
    """Expected user-facing error."""


@dataclass(frozen=True)
class ConversionOptions:
    inputs: tuple[str, ...] = ()
    input_dir: Path | None = None
    output: Path | None = None
    output_dir: Path | None = None
    title: str | None = None
    mode: OutputMode = "combined"
    page_size: PageSize = "A4"
    sort: bool = False
    overwrite: bool = False
    skip_invalid: bool = False
    verbose: bool = False
    standardize: bool = False


@dataclass(frozen=True)
class ConversionResult:
    outputs: tuple[Path, ...]
    page_count: int
    skipped: tuple[str, ...] = ()


def natural_key(value: Path | str) -> list[int | str]:
    text = str(value)
    return [int(part) if part.isdigit() else part.casefold() for part in re.split(r"(\d+)", text)]


def resolve_output_path(path: Path) -> Path:
    return path if path.suffix.casefold() == ".pdf" else path.with_suffix(path.suffix + ".pdf")


def expand_inputs(inputs: Iterable[str], input_dir: Path | None = None, sort: bool = False) -> list[Path]:
    paths: list[Path] = []

    for raw in inputs:
        expanded = glob.glob(raw) if glob.has_magic(raw) else [raw]
        paths.extend(Path(item) for item in expanded)

    if input_dir is not None:
        if not input_dir.exists():
            raise Image2PdfError(f"Input directory does not exist: {input_dir}")
        if not input_dir.is_dir():
            raise Image2PdfError(f"Input directory is not a directory: {input_dir}")
        folder_images = [
            item
            for item in input_dir.iterdir()
            if item.is_file() and item.suffix.casefold() in COMMON_IMAGE_EXTENSIONS
        ]
        paths.extend(folder_images)

    if sort:
        paths = sorted(paths, key=natural_key)

    return paths


def validate_paths(paths: Iterable[Path], skip_invalid: bool = False) -> tuple[list[Path], list[str]]:
    valid: list[Path] = []
    skipped: list[str] = []

    for path in paths:
        try:
            if not path.exists():
                raise Image2PdfError(f"Missing input file: {path}")
            if not path.is_file():
                raise Image2PdfError(f"Input is not a file: {path}")
            with Image.open(path) as image:
                image.verify()
        except (OSError, UnidentifiedImageError, Image2PdfError) as exc:
            message = str(exc) or f"Unreadable image: {path}"
            if skip_invalid:
                skipped.append(f"{path}: {message}")
                continue
            raise Image2PdfError(message) from None
        valid.append(path)

    if not valid:
        raise Image2PdfError("No valid images were provided.")

    return valid, skipped


def image_needs_preprocessing(path: Path) -> bool:
    try:
        with Image.open(path) as image:
            image_format = image.format
            if getattr(image, "is_animated", False):
                return True
            if image_format not in DIRECT_IMG2PDF_FORMATS:
                return True
            if image.mode in {"RGBA", "LA", "PA"}:
                return True
            if image.mode == "P" and "transparency" in image.info:
                return True
            return False
    except (OSError, UnidentifiedImageError) as exc:
        raise Image2PdfError(f"Unreadable image: {path}: {exc}") from None


def preprocess_image(path: Path, temp_dir: Path, index: int) -> Path:
    try:
        with Image.open(path) as image:
            image.seek(0)
            image = ImageOps.exif_transpose(image)
            if image.mode in {"RGBA", "LA", "PA"} or (image.mode == "P" and "transparency" in image.info):
                rgba = image.convert("RGBA")
                background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
                background.alpha_composite(rgba)
                image = background.convert("RGB")
            elif image.mode not in {"1", "L", "RGB", "CMYK"}:
                image = image.convert("RGB")
            output = temp_dir / f"image2pdf-{index:04d}.png"
            image.save(output, format="PNG")
            return output
    except (OSError, UnidentifiedImageError) as exc:
        raise Image2PdfError(f"Could not preprocess image {path}: {exc}") from None


def prepare_images(paths: Iterable[Path], temp_dir: Path) -> list[Path]:
    prepared: list[Path] = []
    for index, path in enumerate(paths, start=1):
        if image_needs_preprocessing(path):
            prepared.append(preprocess_image(path, temp_dir, index))
        else:
            prepared.append(path)
    return prepared


def layout_for_page_size(page_size: PageSize):
    if page_size == "original":
        return img2pdf.default_layout_fun
    if page_size == "A4":
        pagesize = (img2pdf.mm_to_pt(210), img2pdf.mm_to_pt(297))
    elif page_size == "Letter":
        pagesize = (img2pdf.in_to_pt(8.5), img2pdf.in_to_pt(11))
    else:
        raise Image2PdfError(f"Unsupported page size: {page_size}")
    return img2pdf.get_layout_fun(pagesize=pagesize, fit=img2pdf.FitMode.into)


def write_pdf(images: list[Path], output: Path, page_size: PageSize, overwrite: bool) -> None:
    if output.exists() and not overwrite:
        raise Image2PdfError(f"Output already exists. Use --overwrite to replace it: {output}")
    if not output.parent.exists():
        raise Image2PdfError(f"Output directory does not exist: {output.parent}")
    if not output.parent.is_dir():
        raise Image2PdfError(f"Output parent is not a directory: {output.parent}")

    try:
        with output.open("wb") as stream:
            img2pdf.convert(
                *[str(path) for path in images],
                outputstream=stream,
                layout_fun=layout_for_page_size(page_size),
                rotation=img2pdf.Rotation.ifvalid,
                first_frame_only=True,
            )
    except PermissionError as exc:
        raise Image2PdfError(f"Permission denied writing output: {output}") from exc
    except Exception as exc:
        raise Image2PdfError(f"Could not create PDF {output}: {exc}") from None


def combined_output(options: ConversionOptions) -> Path:
    if options.output is not None:
        return resolve_output_path(options.output)

    output_dir = options.output_dir or Path.cwd()
    title = sanitize_title(options.title or "output")
    return output_dir / resolve_output_path(Path(title)).name


def sanitize_title(title: str) -> str:
    cleaned = title.strip()
    if not cleaned:
        raise Image2PdfError("Title cannot be empty.")
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", cleaned)
    return cleaned


def split_outputs(images: list[Path], options: ConversionOptions) -> list[Path]:
    output_dir = options.output_dir or (options.output.parent if options.output else Path.cwd())
    if not output_dir.exists():
        raise Image2PdfError(f"Output directory does not exist: {output_dir}")
    if not output_dir.is_dir():
        raise Image2PdfError(f"Output directory is not a directory: {output_dir}")

    outputs: list[Path] = []
    title = sanitize_title(options.title) if options.title else None
    for index, image in enumerate(images, start=1):
        if title:
            filename = f"{title}-{index:03d}.pdf"
        else:
            filename = f"{sanitize_title(image.stem)}.pdf"
        output = output_dir / filename
        if output in outputs:
            output = output_dir / f"{output.stem}-{index:03d}.pdf"
        outputs.append(output)
    return outputs


def convert_images(
    options: ConversionOptions,
    warn: Callable[[str], None] | None = None,
    info: Callable[[str], None] | None = None,
) -> ConversionResult:
    warn = warn or (lambda message: None)
    info = info or (lambda message: None)

    paths = expand_inputs(options.inputs, options.input_dir, options.sort)
    if not paths:
        raise Image2PdfError("No input images were provided.")

    valid_paths, skipped = validate_paths(paths, options.skip_invalid)
    for message in skipped:
        warn(message)

    if options.verbose:
        info(f"Using {len(valid_paths)} valid image(s).")

    with tempfile.TemporaryDirectory(prefix="image2pdf-") as temporary:
        temp_dir = Path(temporary)
        prepared = prepare_images(valid_paths, temp_dir)

        if options.mode == "combined":
            output = combined_output(options)
            write_pdf(prepared, output, options.page_size, options.overwrite)
            return ConversionResult(outputs=(output,), page_count=len(prepared), skipped=tuple(skipped))

        if options.mode == "split":
            outputs = split_outputs(valid_paths, options)
            for prepared_image, output in zip(prepared, outputs, strict=True):
                write_pdf([prepared_image], output, options.page_size, options.overwrite)
            return ConversionResult(outputs=tuple(outputs), page_count=len(prepared), skipped=tuple(skipped))

    raise Image2PdfError(f"Unsupported output mode: {options.mode}")
