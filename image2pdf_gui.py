from __future__ import annotations

import ctypes
import json
import platform
import queue
import threading
import tkinter as tk
from dataclasses import dataclass, field
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageDraw, ImageTk

from image2pdf_core import COMMON_IMAGE_EXTENSIONS, ConversionOptions, Image2PdfError, convert_images


APP_ROOT = Path(__file__).resolve().parent
SETTINGS_PATH = APP_ROOT / "image2pdf_settings.yaml"
LOGO_PATH = APP_ROOT / "image2pdf_logo.png"

DEFAULT_SETTINGS: dict[str, object] = {
    "output_dir": str(Path.cwd()),
    "mode": "combined",
    "page_size": "A4",
    "standardize": True,
    "sort": True,
    "overwrite": False,
    "skip_invalid": False,
}


@dataclass
class QueueItem:
    source: str
    inputs: tuple[Path, ...] = ()
    input_dir: Path | None = None
    title: str = ""
    status: str = "Queued"
    outputs: tuple[Path, ...] = field(default_factory=tuple)
    page_count: int = 0


class WindowsDropHandler:
    def __init__(self, root: tk.Tk, callback):
        self.root = root
        self.callback = callback
        self._installed = False
        if platform.system() == "Windows":
            self._install()

    def _install(self) -> None:
        try:
            user32 = ctypes.windll.user32
            shell32 = ctypes.windll.shell32
            hwnd = self.root.winfo_id()

            lresult = ctypes.c_ssize_t
            wndproc = ctypes.WINFUNCTYPE(
                lresult,
                ctypes.c_void_p,
                ctypes.c_uint,
                ctypes.c_size_t,
                ctypes.c_ssize_t,
            )
            wm_dropfiles = 0x0233
            gwl_wndproc = -4

            set_window_long_ptr = getattr(user32, "SetWindowLongPtrW", user32.SetWindowLongW)
            set_window_long_ptr.argtypes = (ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p)
            set_window_long_ptr.restype = ctypes.c_void_p
            user32.CallWindowProcW.argtypes = (
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.c_uint,
                ctypes.c_size_t,
                ctypes.c_ssize_t,
            )
            user32.CallWindowProcW.restype = lresult
            shell32.DragAcceptFiles.argtypes = (ctypes.c_void_p, ctypes.c_bool)
            shell32.DragQueryFileW.argtypes = (ctypes.c_size_t, ctypes.c_uint, ctypes.c_wchar_p, ctypes.c_uint)
            shell32.DragQueryFileW.restype = ctypes.c_uint
            shell32.DragFinish.argtypes = (ctypes.c_size_t,)

            def handle_drop(hdrop: int) -> list[Path]:
                paths: list[Path] = []
                count = shell32.DragQueryFileW(hdrop, 0xFFFFFFFF, None, 0)
                for index in range(count):
                    length = shell32.DragQueryFileW(hdrop, index, None, 0)
                    buffer = ctypes.create_unicode_buffer(length + 1)
                    shell32.DragQueryFileW(hdrop, index, buffer, length + 1)
                    paths.append(Path(buffer.value))
                shell32.DragFinish(hdrop)
                return paths

            def proc(hwnd, msg, wparam, lparam):
                if msg == wm_dropfiles:
                    self.root.after(0, lambda: self.callback(handle_drop(wparam)))
                    return 0
                return user32.CallWindowProcW(self._old_proc, hwnd, msg, wparam, lparam)

            self._wndproc = wndproc(proc)
            self._old_proc = set_window_long_ptr(hwnd, gwl_wndproc, ctypes.cast(self._wndproc, ctypes.c_void_p))
            if not self._old_proc:
                return
            shell32.DragAcceptFiles(hwnd, True)
            self._installed = True
            self.root.bind("<Destroy>", self._restore, add="+")
        except Exception:
            self._installed = False

    def _restore(self, _event=None) -> None:
        if not self._installed:
            return
        try:
            user32 = ctypes.windll.user32
            hwnd = self.root.winfo_id()
            set_window_long_ptr = getattr(user32, "SetWindowLongPtrW", user32.SetWindowLongW)
            set_window_long_ptr(hwnd, -4, self._old_proc)
            ctypes.windll.shell32.DragAcceptFiles(hwnd, False)
        except Exception:
            pass
        self._installed = False


class Image2PdfApp(ttk.Frame):
    def __init__(self, master: tk.Tk):
        super().__init__(master)
        self.master.title("Image2pdf")
        self.master.minsize(860, 620)
        self.grid(sticky="nsew")
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)

        self.queue_items: list[QueueItem] = []
        self.worker_events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.worker_thread: threading.Thread | None = None
        self.icons: dict[str, ImageTk.PhotoImage] = {}

        self.selected_files: list[Path] = []
        self.input_dir = tk.StringVar()
        self.saved_settings = load_settings()
        self.output_dir = tk.StringVar(value=str(self.saved_settings["output_dir"]))
        self.title = tk.StringVar()
        self.mode = tk.StringVar(value=str(self.saved_settings["mode"]))
        self.page_size = tk.StringVar(value=str(self.saved_settings["page_size"]))
        self.standardize = tk.BooleanVar(value=bool(self.saved_settings["standardize"]))
        self.sort = tk.BooleanVar(value=bool(self.saved_settings["sort"]))
        self.overwrite = tk.BooleanVar(value=bool(self.saved_settings["overwrite"]))
        self.skip_invalid = tk.BooleanVar(value=bool(self.saved_settings["skip_invalid"]))
        self.status = tk.StringVar(value="Ready. Add folders or drop them into the queue.")

        self._build()
        self._apply_window_logo()
        self.drop_handler = WindowsDropHandler(master, self.add_dropped_paths)

    def _build(self) -> None:
        self._configure_style()
        self._build_menu()
        self._build_toolbar()
        self._build_drop_zone()
        self._build_output_bar()
        self._build_queue()
        self._build_options()
        self._build_log_and_status()

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#d8d8d2")
        style.configure("Toolbar.TFrame", background="#d8d8d2")
        style.configure("TLabel", background="#d8d8d2")
        style.configure("Treeview", rowheight=26, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        style.configure("Horizontal.TProgressbar", troughcolor="#bdbdb8", background="#2ea32e")

    def _build_menu(self) -> None:
        menu = tk.Menu(self.master)
        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(label="Add Images", command=self.add_images)
        file_menu.add_command(label="Add Folder", command=self.choose_input_dir)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.master.destroy)
        queue_menu = tk.Menu(menu, tearoff=False)
        queue_menu.add_command(label="Start Queue", command=self.convert)
        queue_menu.add_command(label="Remove Selected", command=self.remove_selected)
        queue_menu.add_command(label="Clear Completed", command=self.clear_completed)
        help_menu = tk.Menu(menu, tearoff=False)
        help_menu.add_command(label="About", command=self.show_help)
        menu.add_cascade(label="File", menu=file_menu)
        menu.add_cascade(label="Queue", menu=queue_menu)
        menu.add_cascade(label="Help", menu=help_menu)
        self.master.config(menu=menu)

    def _build_toolbar(self) -> None:
        toolbar = ttk.Frame(self, style="Toolbar.TFrame", padding=(8, 8, 8, 6))
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.columnconfigure(7, weight=1)

        buttons = [
            ("add", "Add", self.add_images),
            ("remove", "Remove", self.remove_selected),
            ("folder", "Add Folder", self.choose_input_dir),
            ("settings", "Settings", self.open_settings),
            ("help", "Help", self.show_help),
            ("start", "Start", self.convert),
            ("exit", "Exit", self.master.destroy),
        ]
        for column, (icon, label, command) in enumerate(buttons):
            image = self._icon(icon)
            button = tk.Button(
                toolbar,
                image=image,
                text=label,
                compound="top",
                command=command,
                bd=0,
                relief="flat",
                width=76,
                bg="#d8d8d2",
                activebackground="#c8c8c2",
                font=("Segoe UI", 8),
            )
            button.grid(row=0, column=column, padx=(0, 8), sticky="n")

    def _build_drop_zone(self) -> None:
        self.drop_canvas = tk.Canvas(self, height=132, bd=1, relief="sunken", highlightthickness=0)
        self.drop_canvas.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
        self.drop_canvas.bind("<Configure>", self._paint_drop_zone)
        self.drop_canvas.bind("<Button-1>", lambda _event: self.choose_input_dir())

    def _build_output_bar(self) -> None:
        bar = ttk.Frame(self, padding=(8, 0, 8, 8))
        bar.grid(row=2, column=0, sticky="ew")
        bar.columnconfigure(1, weight=1)
        ttk.Label(bar, text="Output folder").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Entry(bar, textvariable=self.output_dir).grid(row=0, column=1, sticky="ew")
        ttk.Button(bar, text="Browse", command=self.choose_output_dir).grid(row=0, column=2, sticky="e", padx=(8, 0))
        ttk.Label(bar, text="Selected title").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(6, 0))
        ttk.Entry(bar, textvariable=self.title).grid(row=1, column=1, sticky="ew", pady=(6, 0))
        ttk.Button(bar, text="Set Title", command=self.set_selected_title).grid(
            row=1, column=2, sticky="e", padx=(8, 0), pady=(6, 0)
        )

    def _build_queue(self) -> None:
        frame = ttk.Frame(self, padding=(8, 0, 8, 8))
        frame.grid(row=3, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        columns = ("source", "title", "status")
        self.queue_view = ttk.Treeview(frame, columns=columns, show="headings", selectmode="extended", height=8)
        self.queue_view.heading("source", text="Queued item")
        self.queue_view.heading("title", text="Output title")
        self.queue_view.heading("status", text="Status")
        self.queue_view.column("source", minwidth=220, width=390, stretch=True)
        self.queue_view.column("title", minwidth=140, width=200, stretch=True)
        self.queue_view.column("status", minwidth=110, width=130, stretch=False)
        self.queue_view.grid(row=0, column=0, sticky="nsew")
        self.queue_view.bind("<<TreeviewSelect>>", self.load_selected_title)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.queue_view.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.queue_view.configure(yscrollcommand=scrollbar.set)

    def _build_options(self) -> None:
        options = ttk.Frame(self, padding=(8, 0, 8, 8))
        options.grid(row=4, column=0, sticky="ew")
        for column in range(8):
            options.columnconfigure(column, weight=0)
        options.columnconfigure(7, weight=1)

        ttk.Label(options, text="Mode").grid(row=0, column=0, sticky="w")
        ttk.Combobox(options, textvariable=self.mode, values=("combined", "split"), width=12, state="readonly").grid(
            row=0, column=1, sticky="w", padx=(6, 18)
        )
        ttk.Label(options, text="Page").grid(row=0, column=2, sticky="w")
        ttk.Combobox(options, textvariable=self.page_size, values=("A4", "Letter", "original"), width=12, state="readonly").grid(
            row=0, column=3, sticky="w", padx=(6, 18)
        )
        ttk.Checkbutton(options, text="Standardize", variable=self.standardize).grid(row=0, column=4, sticky="w", padx=(0, 14))
        ttk.Checkbutton(options, text="Natural sort", variable=self.sort).grid(row=0, column=5, sticky="w", padx=(0, 14))
        ttk.Checkbutton(options, text="Overwrite", variable=self.overwrite).grid(row=0, column=6, sticky="w", padx=(0, 14))
        ttk.Checkbutton(options, text="Skip invalid", variable=self.skip_invalid).grid(row=0, column=7, sticky="w")

    def _build_log_and_status(self) -> None:
        bottom = ttk.Frame(self, padding=(8, 0, 8, 8))
        bottom.grid(row=5, column=0, sticky="ew")
        bottom.columnconfigure(0, weight=1)
        self.progress = ttk.Progressbar(bottom, mode="determinate", maximum=1)
        self.progress.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Label(bottom, textvariable=self.status).grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.log = tk.Text(self, height=5, wrap="word", bd=1, relief="sunken", font=("Segoe UI", 9))
        self.log.grid(row=6, column=0, sticky="ew", padx=8, pady=(0, 8))

    def _paint_drop_zone(self, _event=None) -> None:
        canvas = self.drop_canvas
        width = max(canvas.winfo_width(), 1)
        height = max(canvas.winfo_height(), 1)
        canvas.delete("all")
        for index in range(width):
            ratio = index / max(width - 1, 1)
            green = int(126 + 56 * (1 - abs(ratio - 0.45)))
            color = f"#{36:02x}{green:02x}{31:02x}"
            canvas.create_line(index, 0, index, height, fill=color)
        for x in range(0, width, max(width // 6, 1)):
            canvas.create_rectangle(x, 0, x + width // 7, height, fill="#ffffff", stipple="gray75", outline="")
        canvas.create_text(
            width // 2 + 2,
            height // 2 + 2,
            text="Drag & Drop Folders Here",
            fill="#1d451d",
            font=("Segoe UI", 24, "bold"),
        )
        canvas.create_text(
            width // 2,
            height // 2,
            text="Drag & Drop Folders Here",
            fill="white",
            font=("Segoe UI", 24, "bold"),
        )

    def _icon(self, name: str) -> ImageTk.PhotoImage:
        if name in self.icons:
            return self.icons[name]
        image = Image.new("RGBA", (42, 42), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        if name == "add":
            draw.ellipse((5, 5, 37, 37), fill="#2fb22f", outline="#118611", width=2)
            draw.rectangle((18, 10, 24, 32), fill="white")
            draw.rectangle((10, 18, 32, 24), fill="white")
        elif name == "remove":
            draw.ellipse((5, 5, 37, 37), fill="#e52828", outline="#a91515", width=2)
            draw.rectangle((11, 18, 31, 24), fill="white")
        elif name == "folder":
            draw.rectangle((6, 14, 37, 34), fill="#f2b636", outline="#b77800")
            draw.rectangle((9, 9, 24, 16), fill="#ffd56d", outline="#b77800")
        elif name == "settings":
            draw.rectangle((9, 9, 33, 33), fill="#2c83d7", outline="#16508b")
            draw.line((14, 14, 28, 28), fill="white", width=3)
            draw.line((28, 14, 14, 28), fill="white", width=3)
        elif name == "help":
            draw.ellipse((7, 7, 35, 35), fill="#f27c22", outline="#a84910", width=2)
            draw.ellipse((13, 13, 29, 29), outline="white", width=5)
        elif name == "start":
            draw.polygon((8, 6, 36, 21, 8, 36), fill="#30b335", outline="#148615")
        elif name == "exit":
            draw.polygon((8, 6, 34, 21, 8, 36), fill="#32b239", outline="#148615")
            draw.rectangle((5, 16, 18, 26), fill="#32b239")
        photo = ImageTk.PhotoImage(image)
        self.icons[name] = photo
        return photo

    def add_images(self) -> None:
        names = filedialog.askopenfilenames(title="Select images")
        if names:
            paths = tuple(Path(name) for name in names)
            self.selected_files.extend(paths)
            title = paths[0].parent.name if paths else "selected-images"
            self.add_queue_item(QueueItem(source=f"{len(paths)} selected image(s)", inputs=paths, title=title))

    def choose_input_dir(self) -> None:
        name = filedialog.askdirectory(title="Select input folder")
        if name:
            path = Path(name)
            self.input_dir.set(str(path))
            self.add_queue_item(QueueItem(source=str(path), input_dir=path, title=path.name))

    def choose_output_dir(self) -> None:
        name = filedialog.askdirectory(title="Select output folder")
        if name:
            self.output_dir.set(name)

    def add_dropped_paths(self, paths: list[Path]) -> None:
        added = 0
        for path in paths:
            if path.is_dir():
                self.add_queue_item(QueueItem(source=str(path), input_dir=path, title=path.name))
                added += 1
            elif path.is_file() and path.suffix.casefold() in COMMON_IMAGE_EXTENSIONS:
                self.add_queue_item(QueueItem(source=str(path), inputs=(path,), title=path.stem))
                added += 1
        if added:
            self.status.set(f"Queued {added} dropped item(s).")

    def add_queue_item(self, item: QueueItem) -> None:
        self.queue_items.append(item)
        self.refresh_queue()

    def remove_selected(self) -> None:
        selected = {int(item_id) for item_id in self.queue_view.selection()}
        if not selected:
            return
        self.queue_items = [item for index, item in enumerate(self.queue_items) if index not in selected]
        self.refresh_queue()

    def clear_completed(self) -> None:
        self.queue_items = [item for item in self.queue_items if item.status not in {"Done", "Failed"}]
        self.refresh_queue()

    def load_selected_title(self, _event=None) -> None:
        selected = self.queue_view.selection()
        if len(selected) == 1:
            self.title.set(self.queue_items[int(selected[0])].title)

    def set_selected_title(self) -> None:
        selected = self.queue_view.selection()
        if not selected:
            return
        title = self.title.get().strip()
        if not title:
            messagebox.showerror("Image2pdf", "Title cannot be empty.")
            return
        for item_id in selected:
            self.queue_items[int(item_id)].title = title
        self.refresh_queue()
        self.status.set("Updated selected queue title.")

    def refresh_queue(self) -> None:
        self.queue_view.delete(*self.queue_view.get_children())
        for index, item in enumerate(self.queue_items):
            self.queue_view.insert("", "end", iid=str(index), values=(item.source, item.title, item.status))
        total = max(len(self.queue_items), 1)
        completed = sum(1 for item in self.queue_items if item.status in {"Done", "Failed"})
        self.progress.configure(maximum=total, value=completed)

    def focus_options(self) -> None:
        self.status.set("Adjust output folder and options, then start the queue.")

    def _apply_window_logo(self) -> None:
        if not LOGO_PATH.exists():
            return
        try:
            self.logo_image = tk.PhotoImage(file=str(LOGO_PATH))
            self.master.iconphoto(True, self.logo_image)
        except tk.TclError:
            pass

    def open_settings(self) -> None:
        window = tk.Toplevel(self.master)
        window.title("Image2pdf Settings")
        window.transient(self.master)
        window.grab_set()
        window.resizable(False, False)
        window.configure(background="#d8d8d2")

        settings_output_dir = tk.StringVar(value=self.output_dir.get())
        settings_mode = tk.StringVar(value=self.mode.get())
        settings_page_size = tk.StringVar(value=self.page_size.get())
        settings_standardize = tk.BooleanVar(value=self.standardize.get())
        settings_sort = tk.BooleanVar(value=self.sort.get())
        settings_overwrite = tk.BooleanVar(value=self.overwrite.get())
        settings_skip_invalid = tk.BooleanVar(value=self.skip_invalid.get())

        content = ttk.Frame(window, padding=16)
        content.grid(row=0, column=0, sticky="nsew")
        content.columnconfigure(1, weight=1)

        ttk.Label(content, text="Output folder").grid(row=0, column=0, sticky="w", pady=4, padx=(0, 8))
        ttk.Entry(content, textvariable=settings_output_dir, width=48).grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Button(
            content,
            text="Browse",
            command=lambda: self._choose_settings_output_dir(settings_output_dir),
        ).grid(row=0, column=2, sticky="e", padx=(8, 0), pady=4)

        ttk.Label(content, text="Output mode").grid(row=1, column=0, sticky="w", pady=4, padx=(0, 8))
        ttk.Combobox(
            content,
            textvariable=settings_mode,
            values=("combined", "split"),
            width=18,
            state="readonly",
        ).grid(row=1, column=1, sticky="w", pady=4)

        ttk.Label(content, text="Page size").grid(row=2, column=0, sticky="w", pady=4, padx=(0, 8))
        ttk.Combobox(
            content,
            textvariable=settings_page_size,
            values=("A4", "Letter", "original"),
            width=18,
            state="readonly",
        ).grid(row=2, column=1, sticky="w", pady=4)

        checks = ttk.Frame(content)
        checks.grid(row=3, column=0, columnspan=3, sticky="w", pady=(10, 4))
        ttk.Checkbutton(checks, text="Standardize pages", variable=settings_standardize).grid(row=0, column=0, sticky="w", padx=(0, 18))
        ttk.Checkbutton(checks, text="Natural sort", variable=settings_sort).grid(row=0, column=1, sticky="w", padx=(0, 18))
        ttk.Checkbutton(checks, text="Overwrite existing PDFs", variable=settings_overwrite).grid(row=1, column=0, sticky="w", padx=(0, 18), pady=(6, 0))
        ttk.Checkbutton(checks, text="Skip invalid images", variable=settings_skip_invalid).grid(row=1, column=1, sticky="w", pady=(6, 0))

        actions = ttk.Frame(content)
        actions.grid(row=4, column=0, columnspan=3, sticky="e", pady=(16, 0))
        ttk.Button(window, text="Cancel", command=window.destroy).grid(row=1, column=0, sticky="e", padx=(0, 104), pady=(0, 16))
        ttk.Button(
            window,
            text="Save",
            command=lambda: self.save_settings_from_window(
                window,
                {
                    "output_dir": settings_output_dir.get(),
                    "mode": settings_mode.get(),
                    "page_size": settings_page_size.get(),
                    "standardize": settings_standardize.get(),
                    "sort": settings_sort.get(),
                    "overwrite": settings_overwrite.get(),
                    "skip_invalid": settings_skip_invalid.get(),
                },
            ),
        ).grid(row=1, column=0, sticky="e", padx=(0, 16), pady=(0, 16))

    def _choose_settings_output_dir(self, variable: tk.StringVar) -> None:
        name = filedialog.askdirectory(title="Select default output folder")
        if name:
            variable.set(name)

    def save_settings_from_window(self, window: tk.Toplevel, values: dict[str, object]) -> None:
        output_dir = Path(str(values["output_dir"]).strip() or ".")
        if not output_dir.exists() or not output_dir.is_dir():
            messagebox.showerror("Image2pdf", f"Output folder does not exist: {output_dir}")
            return
        settings = normalize_settings(values)
        save_settings(settings)
        self.apply_settings(settings)
        window.destroy()
        self.status.set(f"Settings saved to {SETTINGS_PATH.name}.")

    def apply_settings(self, settings: dict[str, object]) -> None:
        self.output_dir.set(str(settings["output_dir"]))
        self.mode.set(str(settings["mode"]))
        self.page_size.set(str(settings["page_size"]))
        self.standardize.set(bool(settings["standardize"]))
        self.sort.set(bool(settings["sort"]))
        self.overwrite.set(bool(settings["overwrite"]))
        self.skip_invalid.set(bool(settings["skip_invalid"]))

    def show_help(self) -> None:
        messagebox.showinfo(
            "Image2pdf",
            "Queue folders or image files, choose one output folder, then start the queue. "
            "Folder jobs use the folder name as the PDF title unless changed in the queue data.",
        )

    def append_log(self, message: str) -> None:
        self.log.insert("end", message + "\n")
        self.log.see("end")

    def convert(self) -> None:
        if self.worker_thread and self.worker_thread.is_alive():
            return
        if not self.queue_items:
            self._queue_legacy_single_item()
        if not self.queue_items:
            messagebox.showerror("Image2pdf", "Add folders or images to the queue first.")
            return

        output_dir = Path(self.output_dir.get().strip() or ".")
        if not output_dir.exists() or not output_dir.is_dir():
            messagebox.showerror("Image2pdf", f"Output folder does not exist: {output_dir}")
            return

        for item in self.queue_items:
            if item.status != "Done":
                item.status = "Queued"
        self.refresh_queue()
        self.status.set("Converting queued items...")
        self.append_log("Starting queue.")

        settings = {
            "mode": self.mode.get(),
            "page_size": self.page_size.get(),
            "sort": self.sort.get(),
            "overwrite": self.overwrite.get(),
            "skip_invalid": self.skip_invalid.get(),
            "standardize": self.standardize.get(),
        }
        self.worker_thread = threading.Thread(target=self._run_queue, args=(output_dir, settings), daemon=True)
        self.worker_thread.start()
        self.after(100, self._poll_worker)

    def _queue_legacy_single_item(self) -> None:
        input_dir = Path(self.input_dir.get().strip()) if self.input_dir.get().strip() else None
        if self.selected_files or input_dir:
            title = self.title.get().strip() or (input_dir.name if input_dir else "selected-images")
            self.add_queue_item(
                QueueItem(
                    source=str(input_dir) if input_dir else f"{len(self.selected_files)} selected image(s)",
                    inputs=tuple(self.selected_files),
                    input_dir=input_dir,
                    title=title,
                )
            )

    def _run_queue(self, output_dir: Path, settings: dict[str, object]) -> None:
        for index, item in enumerate(self.queue_items):
            if item.status == "Done":
                continue
            self.worker_events.put(("status", (index, "Running")))
            options = ConversionOptions(
                inputs=tuple(str(path) for path in item.inputs),
                input_dir=item.input_dir,
                output_dir=output_dir,
                title=item.title,
                mode=settings["mode"],  # type: ignore[arg-type]
                page_size=settings["page_size"],  # type: ignore[arg-type]
                sort=bool(settings["sort"]),
                overwrite=bool(settings["overwrite"]),
                skip_invalid=bool(settings["skip_invalid"]),
                verbose=True,
                standardize=bool(settings["standardize"]),
            )
            try:
                result = convert_images(
                    options,
                    warn=lambda message, item=item: self.worker_events.put(("log", f"{item.title}: {message}")),
                    info=lambda message, item=item: self.worker_events.put(("log", f"{item.title}: {message}")),
                )
            except Image2PdfError as exc:
                self.worker_events.put(("failed", (index, str(exc))))
                continue
            self.worker_events.put(("done", (index, result.outputs, result.page_count)))
        self.worker_events.put(("finished", None))

    def _poll_worker(self) -> None:
        while True:
            try:
                kind, payload = self.worker_events.get_nowait()
            except queue.Empty:
                break
            if kind == "status":
                index, status = payload  # type: ignore[misc]
                self.queue_items[index].status = status
            elif kind == "log":
                self.append_log(str(payload))
            elif kind == "failed":
                index, message = payload  # type: ignore[misc]
                self.queue_items[index].status = "Failed"
                self.append_log("Error: " + message)
            elif kind == "done":
                index, outputs, page_count = payload  # type: ignore[misc]
                item = self.queue_items[index]
                item.status = "Done"
                item.outputs = outputs
                item.page_count = page_count
                for output in outputs:
                    self.append_log(f"Created: {output}")
            elif kind == "finished":
                done = sum(1 for item in self.queue_items if item.status == "Done")
                failed = sum(1 for item in self.queue_items if item.status == "Failed")
                self.status.set(f"Queue complete. {done} done, {failed} failed.")
        self.refresh_queue()
        if self.worker_thread and self.worker_thread.is_alive():
            self.after(100, self._poll_worker)

    def _finish_error(self, message: str) -> None:
        self.status.set("Conversion failed.")
        self.append_log("Error: " + message)
        messagebox.showerror("Image2pdf", message)

    def _finish_success(self, outputs: tuple[Path, ...], page_count: int) -> None:
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


def normalize_settings(values: dict[str, object]) -> dict[str, object]:
    settings = dict(DEFAULT_SETTINGS)
    settings.update(values)
    if settings["mode"] not in {"combined", "split"}:
        settings["mode"] = DEFAULT_SETTINGS["mode"]
    if settings["page_size"] not in {"A4", "Letter", "original"}:
        settings["page_size"] = DEFAULT_SETTINGS["page_size"]
    for key in ("standardize", "sort", "overwrite", "skip_invalid"):
        settings[key] = parse_bool(settings[key])
    settings["output_dir"] = str(settings["output_dir"] or DEFAULT_SETTINGS["output_dir"])
    return settings


def parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().casefold() in {"true", "yes", "1", "on"}


def load_settings(path: Path = SETTINGS_PATH) -> dict[str, object]:
    if not path.exists():
        return dict(DEFAULT_SETTINGS)
    values: dict[str, object] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if key not in DEFAULT_SETTINGS:
            continue
        if raw_value in {"true", "false"}:
            values[key] = raw_value == "true"
        else:
            try:
                values[key] = json.loads(raw_value)
            except json.JSONDecodeError:
                values[key] = raw_value.strip('"')
    return normalize_settings(values)


def save_settings(settings: dict[str, object], path: Path = SETTINGS_PATH) -> None:
    normalized = normalize_settings(settings)
    lines = [
        "# Image2pdf GUI settings",
        "# This file is written by the Settings window.",
    ]
    for key in DEFAULT_SETTINGS:
        value = normalized[key]
        if isinstance(value, bool):
            rendered = "true" if value else "false"
        else:
            rendered = json.dumps(str(value), ensure_ascii=False)
        lines.append(f"{key}: {rendered}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
