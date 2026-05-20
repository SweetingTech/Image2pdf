#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
elif command -v python3.11 >/dev/null 2>&1; then
  PY="python3.11"
else
  PY="${PYTHON:-python3}"
fi

"$PY" - <<'PY'
import sys

if sys.version_info < (3, 11):
    raise SystemExit("Python 3.11 or newer is required.")
PY

echo "==> Install runtime dependencies"
"$PY" -m pip install -r requirements.txt

echo "==> Install test dependencies"
"$PY" -m pip install pytest pypdf

echo "==> Compile project modules"
"$PY" -m py_compile image2pdf.py image2pdf_core.py image2pdf_gui.py

echo "==> Run pytest"
"$PY" -m pytest

echo "==> Run CLI help smoke test"
"$PY" image2pdf.py --help >/dev/null

echo "==> Run generated-image CLI smoke tests"
TMPDIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMPDIR"
}
trap cleanup EXIT

INPUT_DIR="$TMPDIR/images"
OUTPUT_DIR="$TMPDIR/out"
mkdir -p "$INPUT_DIR" "$OUTPUT_DIR"

cat > "$TMPDIR/make_images.py" <<'PY'
from pathlib import Path
from PIL import Image
import sys

root = Path(sys.argv[1])
Image.new("RGB", (30, 20), (220, 30, 30)).save(root / "page2.jpg", dpi=(72, 72))
Image.new("RGB", (40, 20), (30, 220, 30)).save(root / "page10.jpg", dpi=(72, 72))
Image.new("RGBA", (20, 20), (30, 30, 220, 128)).save(root / "page1.png", dpi=(72, 72))
PY

"$PY" "$TMPDIR/make_images.py" "$INPUT_DIR"

"$PY" image2pdf.py \
  "$INPUT_DIR/page2.jpg" \
  "$INPUT_DIR/page10.jpg" \
  "$INPUT_DIR/page1.png" \
  --sort \
  --output "$TMPDIR/combined"

test -f "$TMPDIR/combined.pdf"

"$PY" image2pdf.py --input-dir "$INPUT_DIR" --mode split --output-dir "$OUTPUT_DIR" --title page --overwrite

split_count="$(find "$OUTPUT_DIR" -maxdepth 1 -name 'page-*.pdf' | wc -l | tr -d ' ')"
if [ "$split_count" != "3" ]; then
  echo "Split smoke test expected 3 PDFs but found $split_count" >&2
  exit 1
fi

echo "==> All Image2pdf validation steps passed"
