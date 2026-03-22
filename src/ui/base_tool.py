"""Base class for all tool panels."""
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk


class DropZone(ctk.CTkFrame):
    """A file drop zone with visual feedback."""

    def __init__(self, master, label="Drop files here\nor click to browse",
                 multiple=False, filetypes=None, **kwargs):
        super().__init__(master, **kwargs)
        self.multiple = multiple
        self.filetypes = filetypes or [("All files", "*.*")]
        self.files = []
        self.on_files_changed = None

        self.configure(
            corner_radius=12,
            border_width=2,
            border_color=("gray70", "gray40"),
            fg_color=("gray95", "gray17"),
        )

        self.inner = ctk.CTkFrame(self, fg_color="transparent")
        self.inner.pack(expand=True, fill="both", padx=20, pady=20)

        self.icon_label = ctk.CTkLabel(self.inner, text="📂", font=("Arial", 32))
        self.icon_label.pack(pady=(10, 5))

        self.label = ctk.CTkLabel(self.inner, text=label,
                                  font=("Arial", 13),
                                  text_color=("gray40", "gray60"),
                                  justify="center")
        self.label.pack(pady=(0, 10))

        self.files_frame = ctk.CTkScrollableFrame(self.inner, height=80, fg_color="transparent")
        self.files_frame.pack(fill="x", padx=5)

        btn_frame = ctk.CTkFrame(self.inner, fg_color="transparent")
        btn_frame.pack(pady=8)

        self.browse_btn = ctk.CTkButton(btn_frame, text="Browse", width=100,
                                         command=self._browse)
        self.browse_btn.pack(side="left", padx=4)

        self.clear_btn = ctk.CTkButton(btn_frame, text="Clear", width=80,
                                        fg_color=("gray80", "gray30"),
                                        hover_color=("gray70", "gray40"),
                                        text_color=("gray10", "gray90"),
                                        command=self._clear)
        self.clear_btn.pack(side="left", padx=4)

        self.bind("<Button-1>", lambda e: self._browse())
        self.label.bind("<Button-1>", lambda e: self._browse())
        self.icon_label.bind("<Button-1>", lambda e: self._browse())

        # Try to enable tkinterdnd2 drag & drop
        try:
            self.drop_target_register("DND_Files")  # type: ignore
            self.dnd_bind("<<Drop>>", self._on_drop)  # type: ignore
        except Exception:
            pass

    def _on_drop(self, event):
        raw = event.data
        # Parse file paths from drop event
        paths = []
        if raw.startswith("{"):
            import re
            paths = re.findall(r'\{([^}]+)\}', raw)
            rest = re.sub(r'\{[^}]+\}', '', raw).split()
            paths.extend(rest)
        else:
            paths = raw.split()
        paths = [p.strip() for p in paths if p.strip()]
        self._set_files(paths if self.multiple else paths[:1])

    def _browse(self):
        if self.multiple:
            paths = filedialog.askopenfilenames(filetypes=self.filetypes)
            if paths:
                self._set_files(list(paths))
        else:
            path = filedialog.askopenfilename(filetypes=self.filetypes)
            if path:
                self._set_files([path])

    def _clear(self):
        self._set_files([])

    def _set_files(self, paths):
        self.files = paths
        for w in self.files_frame.winfo_children():
            w.destroy()
        for p in paths:
            row = ctk.CTkFrame(self.files_frame, fg_color=("gray85", "gray25"),
                               corner_radius=6, height=28)
            row.pack(fill="x", pady=2, padx=2)
            row.pack_propagate(False)
            name = os.path.basename(p)
            ctk.CTkLabel(row, text=f"📄 {name}", font=("Arial", 11),
                         anchor="w").pack(side="left", padx=8, fill="x", expand=True)
        if self.on_files_changed:
            self.on_files_changed(paths)


class BaseTool(ctk.CTkFrame):
    """Base class for tool panels."""

    TITLE = "Tool"
    DESCRIPTION = ""

    def __init__(self, master, settings: dict, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.settings = settings
        self._build_header()
        self.build_ui()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 8))
        ctk.CTkLabel(header, text=self.TITLE, font=("Arial", 22, "bold")).pack(anchor="w")
        if self.DESCRIPTION:
            ctk.CTkLabel(header, text=self.DESCRIPTION,
                         font=("Arial", 13),
                         text_color=("gray40", "gray60")).pack(anchor="w", pady=(2, 0))
        ctk.CTkFrame(self, height=1, fg_color=("gray80", "gray30")).pack(fill="x", padx=24, pady=(4, 12))

    def build_ui(self):
        """Override in subclasses."""
        pass

    def _make_output_path(self, input_path: str, suffix: str = "_output", ext: str = "") -> str:
        out_dir = self.settings.get("default_output_dir") or os.path.dirname(input_path)
        stem = os.path.splitext(os.path.basename(input_path))[0]
        extension = ext or os.path.splitext(input_path)[1]
        return os.path.join(out_dir, f"{stem}{suffix}{extension}")

    def _run_in_thread(self, func, on_done=None, on_error=None):
        """Run a function in a background thread."""
        def target():
            try:
                result = func()
                if on_done:
                    self.after(0, lambda: on_done(result))
            except Exception as e:
                if on_error:
                    self.after(0, lambda: on_error(str(e)))
                else:
                    self.after(0, lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=target, daemon=True).start()

    def _show_success(self, msg: str):
        messagebox.showinfo("Success", msg)

    def _show_error(self, msg: str):
        messagebox.showerror("Error", msg)

    def _make_action_row(self, parent, label: str, command) -> ctk.CTkButton:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(12, 0))
        btn = ctk.CTkButton(row, text=label, font=("Arial", 13, "bold"),
                             height=40, command=command)
        btn.pack(side="left", padx=(0, 12))
        self._status_label = ctk.CTkLabel(row, text="", font=("Arial", 12),
                                           text_color=("gray40", "gray60"))
        self._status_label.pack(side="left")
        return btn

    def _set_status(self, msg: str, color: str = "gray"):
        if hasattr(self, "_status_label"):
            self._status_label.configure(text=msg, text_color=color)

    def _make_progress(self, parent) -> ctk.CTkProgressBar:
        pb = ctk.CTkProgressBar(parent)
        pb.set(0)
        pb.pack(fill="x", pady=(8, 0))
        return pb
