from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from image2pdf_core import ConversionOptions, Image2PdfError, convert_images


class Image2PdfApp(ttk.Frame):
    def __init__(self, master: tk.Misc):
        super().__init__(master, padding=16)
        self.master.title("Image2pdf")
        self.master.minsize(720, 560)
        self.grid(sticky="nsew")
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)

        self.selected_files: list[Path] = []
        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar(value=str(Path.cwd()))
        self.title = tk.StringVar(value="output")
        self.mode = tk.StringVar(value="combined")
        self.page_size = tk.StringVar(value="A4")
        self.standardize = tk.BooleanVar(value=True)
        self.sort = tk.BooleanVar(value=False)
        self.overwrite = tk.BooleanVar(value=False)
        self.skip_invalid = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value="Select files or an input folder.")

        self._build()

    def _build(self) -> None:
        self.columnconfigure(1, weight=1)

        ttk.Button(self, text="Add Images", command=self.add_images).grid(row=0, column=0, sticky="ew", pady=4)
        self.file_label = ttk.Label(self, text="No individual files selected")
        self.file_label.grid(row=0, column=1, sticky="w", padx=8)

        ttk.Button(self, text="Input Folder", command=self.choose_input_dir).grid(row=1, column=0, sticky="ew", pady=4)
        ttk.Entry(self, textvariable=self.input_dir).grid(row=1, column=1, sticky="ew", padx=8)

        ttk.Button(self, text="Output Folder", command=self.choose_output_dir).grid(row=2, column=0, sticky="ew", pady=4)
        ttk.Entry(self, textvariable=self.output_dir).grid(row=2, column=1, sticky="ew", padx=8)

        ttk.Label(self, text="Output title").grid(row=3, column=0, sticky="w", pady=4)
        ttk.Entry(self, textvariable=self.title).grid(row=3, column=1, sticky="ew", padx=8)

        options = ttk.LabelFrame(self, text="Options", padding=12)
        options.grid(row=4, column=0, columnspan=2, sticky="ew", pady=12)
        options.columnconfigure(1, weight=1)

        ttk.Label(options, text="Output mode").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Combobox(options, textvariable=self.mode, values=("combined", "split"), state="readonly").grid(
            row=0, column=1, sticky="ew", padx=8
        )

        ttk.Label(options, text="Page size").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Combobox(options, textvariable=self.page_size, values=("A4", "Letter", "original"), state="readonly").grid(
            row=1, column=1, sticky="ew", padx=8
        )

        checks = ttk.Frame(options)
        checks.grid(row=2, column=0, columnspan=2, sticky="w", pady=8)
        ttk.Checkbutton(checks, text="Standardize to selected page size", variable=self.standardize).grid(
            row=0, column=0, sticky="w", padx=(0, 16)
        )
        ttk.Checkbutton(checks, text="Natural sort", variable=self.sort).grid(row=0, column=1, sticky="w", padx=(0, 16))
        ttk.Checkbutton(checks, text="Overwrite", variable=self.overwrite).grid(row=0, column=2, sticky="w", padx=(0, 16))
        ttk.Checkbutton(checks, text="Skip invalid", variable=self.skip_invalid).grid(row=0, column=3, sticky="w")

        self.log = tk.Text(self, height=12, wrap="word")
        self.log.grid(row=5, column=0, columnspan=2, sticky="nsew")
        self.rowconfigure(5, weight=1)

        bottom = ttk.Frame(self)
        bottom.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        bottom.columnconfigure(0, weight=1)
        ttk.Label(bottom, textvariable=self.status).grid(row=0, column=0, sticky="w")
        self.convert_button = ttk.Button(bottom, text="Convert", command=self.convert)
        self.convert_button.grid(row=0, column=1, sticky="e")

    def add_images(self) -> None:
        names = filedialog.askopenfilenames(title="Select images")
        if names:
            self.selected_files.extend(Path(name) for name in names)
            self.file_label.configure(text=f"{len(self.selected_files)} individual file(s) selected")

    def choose_input_dir(self) -> None:
        name = filedialog.askdirectory(title="Select input folder")
        if name:
            self.input_dir.set(name)

    def choose_output_dir(self) -> None:
        name = filedialog.askdirectory(title="Select output folder")
        if name:
            self.output_dir.set(name)

    def append_log(self, message: str) -> None:
        self.log.insert("end", message + "\n")
        self.log.see("end")

    def convert(self) -> None:
        if not self.selected_files and not self.input_dir.get().strip():
            messagebox.showerror("Image2pdf", "Select images or an input folder first.")
            return
        output_dir = Path(self.output_dir.get().strip() or ".")
        input_dir = Path(self.input_dir.get().strip()) if self.input_dir.get().strip() else None

        options = ConversionOptions(
            inputs=tuple(str(path) for path in self.selected_files),
            input_dir=input_dir,
            output_dir=output_dir,
            title=self.title.get(),
            mode=self.mode.get(),  # type: ignore[arg-type]
            page_size=self.page_size.get(),  # type: ignore[arg-type]
            sort=self.sort.get(),
            overwrite=self.overwrite.get(),
            skip_invalid=self.skip_invalid.get(),
            verbose=True,
            standardize=self.standardize.get(),
        )

        self.convert_button.configure(state="disabled")
        self.status.set("Converting...")
        self.append_log("Starting conversion.")

        def log_from_worker(message: str) -> None:
            self.after(0, lambda: self.append_log(message))

        def worker() -> None:
            try:
                result = convert_images(options, warn=log_from_worker, info=log_from_worker)
            except Image2PdfError as exc:
                self.after(0, lambda: self._finish_error(str(exc)))
                return
            self.after(0, lambda: self._finish_success(result.outputs, result.page_count))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_error(self, message: str) -> None:
        self.convert_button.configure(state="normal")
        self.status.set("Conversion failed.")
        self.append_log("Error: " + message)
        messagebox.showerror("Image2pdf", message)

    def _finish_success(self, outputs: tuple[Path, ...], page_count: int) -> None:
        self.convert_button.configure(state="normal")
        self.status.set(f"Created {len(outputs)} PDF file(s), {page_count} page(s).")
        for output in outputs:
            self.append_log(f"Created: {output}")
        messagebox.showinfo("Image2pdf", self.status.get())


def create_app() -> tuple[tk.Tk, Image2PdfApp]:
    root = tk.Tk()
    app = Image2PdfApp(root)
    return root, app


def main() -> None:
    root, _app = create_app()
    root.mainloop()


if __name__ == "__main__":
    main()
