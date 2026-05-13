from __future__ import annotations

import argparse
import sys
from pathlib import Path

from image2pdf_core import ConversionOptions, Image2PdfError, convert_images


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="image2pdf.py",
        description="Convert images into a combined multi-page PDF or one PDF per image.",
    )
    parser.add_argument("inputs", nargs="*", help="Image file paths or glob patterns.")
    parser.add_argument("-o", "--output", type=Path, help="Output PDF filename for combined mode.")
    parser.add_argument("--input-dir", type=Path, help="Folder of images to ingest non-recursively.")
    parser.add_argument("--output-dir", type=Path, help="Existing folder for output PDFs.")
    parser.add_argument("--title", help="Output title. Combined mode uses title.pdf; split mode uses title-001.pdf.")
    parser.add_argument("--mode", choices=("combined", "split"), default="combined", help="PDF output mode.")
    parser.add_argument("--page-size", choices=("A4", "Letter", "original"), default="A4")
    parser.add_argument("--standardize", action="store_true", help="Fit images to the selected page size.")
    parser.add_argument("--sort", action="store_true", help="Sort images naturally, so page2 comes before page10.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing output files.")
    parser.add_argument("--skip-invalid", action="store_true", help="Skip unreadable inputs with warnings.")
    parser.add_argument("--verbose", action="store_true", help="Print detailed processing information.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.inputs and args.input_dir is None:
        parser.error("provide at least one input image/glob or --input-dir")
    if args.output and args.output_dir and args.mode == "combined":
        parser.error("use either --output or --output-dir/--title for combined mode, not both")
    if args.output and args.mode == "split":
        parser.error("--output is only valid in combined mode; use --output-dir for split mode")

    options = ConversionOptions(
        inputs=tuple(args.inputs),
        input_dir=args.input_dir,
        output=args.output,
        output_dir=args.output_dir,
        title=args.title,
        mode=args.mode,
        page_size=args.page_size,
        sort=args.sort,
        overwrite=args.overwrite,
        skip_invalid=args.skip_invalid,
        verbose=args.verbose,
        standardize=args.standardize,
    )

    try:
        result = convert_images(
            options,
            warn=lambda message: print(f"Warning: {message}", file=sys.stderr),
            info=lambda message: print(message),
        )
    except Image2PdfError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if result.skipped:
        print(f"Skipped {len(result.skipped)} invalid input(s).", file=sys.stderr)
    if args.mode == "combined":
        print(f"Created {result.outputs[0]} ({result.page_count} page(s)).")
    else:
        print(f"Created {len(result.outputs)} PDF file(s) in {result.outputs[0].parent}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
