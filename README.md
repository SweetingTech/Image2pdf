# Image2pdf

Image2pdf is a local Python utility for converting images into PDF files. It can create one combined multi-page PDF, ebook-style, or split each image into its own one-page PDF.

It has no cloud services, no accounts, no telemetry, no OCR, and no GUI framework beyond Python's built-in Tkinter.

## Installation

Use Python 3.11 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

On Windows, you can also use the startup script. It checks for an existing `.venv` or `venv` folder, creates `.venv` when needed, installs dependencies, and starts the GUI:

```powershell
.\Start-Image2pdf.ps1
```

## CLI Usage

Create one combined PDF:

```powershell
python image2pdf.py image1.jpg image2.png image3.webp --output document.pdf
```

Create a combined PDF from a folder:

```powershell
python image2pdf.py --input-dir .\scans --output-dir .\out --title receipt
```

Create one PDF per image:

```powershell
python image2pdf.py --input-dir .\pages --mode split --output-dir .\pdfs --title chapter
```

If an output name does not end with `.pdf`, Image2pdf appends `.pdf` automatically.

## GUI Usage

Run:

```powershell
python image2pdf_gui.py
```

Or use the setup/startup script:

```powershell
.\Start-Image2pdf.ps1
```

The GUI lets you choose individual images, add one or more input folders to a queue, set one shared output folder, override queued output titles when needed, choose combined or split output, page size, sorting, overwrite behavior, and invalid-file handling.

Queued folder jobs run one after another. By default, each folder job uses the folder name as the output PDF title. Unicode names, including Japanese folder and file names, are supported by Python paths and are preserved in generated PDF filenames where the operating system allows them.

On Windows, the GUI supports dragging files or folders onto the drop zone. If drag and drop is not available in your environment, use Add Images or Add Folder.

## Page Ordering

By default, images stay in the exact order supplied on the command line. Glob patterns are expanded inside Python so behavior is consistent on Windows and other platforms. When multiple glob arguments are used, each glob expands in place.

Folder ingestion is non-recursive in this version. Folder images are appended after explicitly selected files. Folder ingestion uses deterministic natural filename ordering so page-numbered files are not dependent on filesystem enumeration order.

Use `--sort` to apply natural sorting:

```powershell
python image2pdf.py page10.jpg page2.jpg page1.jpg --sort --output book.pdf
```

Natural sort places `page1`, `page2`, and `page10` in that order.

## Page Size And Standardization

`--page-size` supports:

- `A4`: fit each image inside an A4 page.
- `Letter`: fit each image inside a US Letter page.
- `original`: use each image's natural dimensions and DPI where possible.

For A4 and Letter, Image2pdf preserves aspect ratio, centers the image, avoids cropping or stretching, and leaves white margins when needed. This is the standardization behavior. In `original` mode, standardization is ignored because each page follows the source image.

## Overwrite And Invalid Files

Image2pdf will not overwrite existing PDFs unless `--overwrite` is passed.

By default, missing, corrupted, unsupported, or unreadable images stop the conversion with a clear error. With `--skip-invalid`, bad inputs are skipped with warnings. If no valid images remain, the command still fails.

## Known Limitations

- HEIC support is optional and depends on extra Pillow/runtime support installed on your machine. It is not promised by default.
- Multi-frame GIF and TIFF files are treated as one input image in this version.
- Folder ingestion is non-recursive.
- Drag and drop depends on Windows desktop shell support. Use Add Images or Add Folder if it is unavailable.
- Image2pdf does not do OCR, image editing, cloud uploads, accounts, or telemetry.

## Test Plan

This repository may keep local validation tests in ignored `test/` or `tests/` folders. Those folders are intentionally excluded from GitHub by `.gitignore`.

When local tests are present, run:

```powershell
python -m pytest
```

The main project validation command is:

```powershell
.\scripts\Validate-GoalLite.ps1
```

Manual checks:

- One JPG input creates a one-page PDF.
- Multiple images create pages in input order.
- `--sort` naturally orders `page1`, `page2`, `page10`.
- Output names without `.pdf` get `.pdf` appended.
- Existing output files are protected unless `--overwrite` is set.
- Missing and corrupted images fail clearly by default.
- Corrupted images are skipped with `--skip-invalid`.
- Transparent PNG inputs convert successfully with a white background.
- EXIF-rotated images convert successfully.
- A4, Letter, and original page size modes create valid PDFs.
- Split mode creates one PDF per image.
- The GUI opens, queues multiple folders, uses one output folder, and converts queued jobs one after another.
- Folder names with Japanese characters are preserved as default output titles.
