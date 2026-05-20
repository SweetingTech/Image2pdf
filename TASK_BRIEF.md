# Task Brief

## Project summary

Image2pdf is a local Python 3.11+ utility that converts image files into PDF files. It supports combined multi-page PDFs, split one-page-per-image PDFs, and a small Tkinter GUI. The README is the source of truth for the product contract.

## Source-of-truth requirements from README.md

- Use Python 3.11 or newer.
- Runtime dependencies are `img2pdf` and `Pillow`.
- Create a combined multi-page PDF from explicit image files, glob patterns, or a non-recursive input folder.
- Create split output where each valid image becomes one one-page PDF.
- Append `.pdf` to output names that do not already end in `.pdf`.
- Preserve explicit CLI order unless natural sort is requested.
- Expand glob patterns in Python so Windows behavior is reliable.
- Use natural sorting when requested so `page1`, `page2`, `page10` sort correctly.
- Support page sizes `A4`, `Letter`, and `original`.
- For A4 and Letter, preserve aspect ratio, center images, avoid cropping/stretching, and use white margins.
- For `original`, preserve natural image dimensions and DPI where possible.
- Refuse to overwrite existing PDFs unless overwrite is explicitly enabled.
- Fail clearly for missing, corrupted, unsupported, or unreadable images by default.
- Skip invalid images only when requested, and fail if no valid images remain.
- Handle transparent PNG inputs by producing a white background.
- Handle EXIF-rotated images safely.
- Provide a Tkinter GUI for selecting files, input folder, output folder, title, output mode, page size, sorting, overwrite behavior, and invalid-file behavior.
- Include automated tests plus manual GUI validation guidance.

## Explicit non-goals

- No cloud services.
- No accounts.
- No telemetry.
- No OCR.
- No non-built-in GUI framework beyond Tkinter.
- No recursive folder ingestion for v1.
- No guaranteed HEIC support by default.
- No multi-page expansion of animated GIF or multi-frame TIFF for v1.
- No unnecessary runtime dependencies.

## Expected CLI behavior

- Combined mode examples:
  - `python image2pdf.py image1.jpg image2.png image3.webp --output document.pdf`
  - `python image2pdf.py --input-dir .\scans --output-dir .\out --title receipt`
- Split mode example:
  - `python image2pdf.py --input-dir .\pages --mode split --output-dir .\pdfs --title chapter`
- `--mode combined` is the default.
- `--mode split` creates `title-001.pdf`, `title-002.pdf`, and so on when a title is provided.
- If no split title is provided, output names should derive from source image stems.
- `--sort` applies natural sort.
- `--overwrite` is required to replace existing PDFs.
- `--skip-invalid` skips bad inputs with warnings.
- `--page-size` accepts only `A4`, `Letter`, and `original`.

## Expected GUI behavior

- `python image2pdf_gui.py` opens a Tkinter desktop app.
- The GUI must expose:
  - individual image selection
  - input folder selection
  - output folder selection
  - output title entry
  - combined vs split output mode
  - A4, Letter, and original page size selector
  - standardize option using fit-to-page behavior
  - natural sort toggle
  - overwrite toggle
  - skip-invalid toggle
  - status/log feedback
- The GUI must call the same shared conversion logic as the CLI.

## Expected validation behavior

- Use or create a virtual environment when practical.
- Install `requirements.txt`.
- Install test dependencies `pytest` and `pypdf`.
- Run `python -m pytest`.
- Run import/compile checks for project Python modules.
- Run CLI smoke tests using generated temporary images.
- Manually validate that the Tkinter GUI opens and can convert selected files or a selected input folder.
