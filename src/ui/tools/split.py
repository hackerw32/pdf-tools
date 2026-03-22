import os
from tkinter import filedialog
import customtkinter as ctk
from src.ui.base_tool import BaseTool, DropZone
from src.core import pdf_ops


class SplitTool(BaseTool):
    TITLE = "Split PDF"
    DESCRIPTION = "Split a PDF into individual pages or custom page ranges"

    def build_ui(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24)

        self.drop = DropZone(scroll, label="Drop a PDF file here\nor click to browse",
                             multiple=False, filetypes=[("PDF files", "*.pdf")])
        self.drop.configure(height=160)
        self.drop.pack(fill="x", pady=(0, 16))
        self.drop.on_files_changed = self._on_file_selected

        # Info
        self.info_label = ctk.CTkLabel(scroll, text="", font=("Arial", 12),
                                        text_color=("gray40", "gray60"))
        self.info_label.pack(anchor="w", pady=(0, 8))

        # Split mode
        mode_frame = ctk.CTkFrame(scroll, corner_radius=10, fg_color=("gray92", "gray18"))
        mode_frame.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(mode_frame, text="Split Mode",
                     font=("Arial", 13, "bold")).pack(anchor="w", padx=16, pady=(12, 6))

        self.mode_var = ctk.StringVar(value="all")
        modes = [
            ("Extract all pages (one file per page)", "all"),
            ("Custom page ranges", "ranges"),
            ("Split at every N pages", "every_n"),
        ]
        for text, val in modes:
            ctk.CTkRadioButton(mode_frame, text=text, variable=self.mode_var,
                               value=val, command=self._update_mode).pack(anchor="w", padx=20, pady=3)

        # Ranges input
        self.ranges_frame = ctk.CTkFrame(mode_frame, fg_color="transparent")
        ctk.CTkLabel(self.ranges_frame,
                     text="Enter ranges (e.g. 1-3, 4-7, 8-10):",
                     font=("Arial", 12)).pack(anchor="w", padx=20, pady=(4, 2))
        self.ranges_entry = ctk.CTkEntry(self.ranges_frame, placeholder_text="1-3, 5-8, 10-15",
                                          width=300)
        self.ranges_entry.pack(anchor="w", padx=20, pady=(0, 8))

        # Every N pages
        self.every_n_frame = ctk.CTkFrame(mode_frame, fg_color="transparent")
        n_row = ctk.CTkFrame(self.every_n_frame, fg_color="transparent")
        n_row.pack(anchor="w", padx=20, pady=(4, 8))
        ctk.CTkLabel(n_row, text="Split every", font=("Arial", 12)).pack(side="left")
        self.n_entry = ctk.CTkEntry(n_row, width=60, placeholder_text="2")
        self.n_entry.pack(side="left", padx=8)
        ctk.CTkLabel(n_row, text="pages", font=("Arial", 12)).pack(side="left")

        # Output dir
        out_row = ctk.CTkFrame(scroll, fg_color="transparent")
        out_row.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(out_row, text="Output folder:", font=("Arial", 12)).pack(side="left")
        self.out_dir_var = ctk.StringVar(value="Same as input")
        ctk.CTkEntry(out_row, textvariable=self.out_dir_var, width=280).pack(side="left", padx=8)
        ctk.CTkButton(out_row, text="Browse", width=80, command=self._pick_outdir).pack(side="left")

        self._action_btn = self._make_action_row(scroll, "✂  Split PDF", self._run)
        self.pb = self._make_progress(scroll)

        self._update_mode()

    def _on_file_selected(self, files):
        if files:
            try:
                info = pdf_ops.get_pdf_info(files[0])
                self.info_label.configure(text=f"📄 {info['pages']} pages  |  {info['size_bytes']//1024} KB")
            except Exception:
                pass

    def _update_mode(self):
        self.ranges_frame.pack_forget()
        self.every_n_frame.pack_forget()
        if self.mode_var.get() == "ranges":
            self.ranges_frame.pack(fill="x")
        elif self.mode_var.get() == "every_n":
            self.every_n_frame.pack(fill="x")

    def _pick_outdir(self):
        d = filedialog.askdirectory()
        if d:
            self.out_dir_var.set(d)

    def _parse_ranges(self, text):
        ranges = []
        for part in text.split(","):
            part = part.strip()
            if "-" in part:
                a, b = part.split("-", 1)
                ranges.append((int(a.strip()), int(b.strip())))
            elif part.isdigit():
                n = int(part)
                ranges.append((n, n))
        return ranges

    def _run(self):
        if not self.drop.files:
            self._show_error("Please select a PDF file.")
            return

        input_path = self.drop.files[0]
        out_dir = self.out_dir_var.get()
        if out_dir == "Same as input":
            out_dir = os.path.dirname(input_path)

        mode = self.mode_var.get()
        ranges = None

        if mode == "ranges":
            try:
                ranges = self._parse_ranges(self.ranges_entry.get())
                if not ranges:
                    self._show_error("Please enter valid page ranges.")
                    return
            except Exception:
                self._show_error("Invalid range format. Use e.g. 1-3, 5-8")
                return
        elif mode == "every_n":
            try:
                n = int(self.n_entry.get() or "1")
                info = pdf_ops.get_pdf_info(input_path)
                total = info["pages"]
                ranges = [(i+1, min(i+n, total)) for i in range(0, total, n)]
            except Exception as e:
                self._show_error(str(e))
                return

        self.pb.set(0)
        self._set_status("Splitting...", "orange")
        self._action_btn.configure(state="disabled")

        def work():
            return pdf_ops.split_pdf(input_path, out_dir, ranges)

        def done(outputs):
            self.pb.set(1)
            self._action_btn.configure(state="normal")
            self._set_status(f"Done! {len(outputs)} file(s) created.", "green")
            self._show_success(f"Created {len(outputs)} PDF file(s) in:\n{out_dir}")

        def error(e):
            self.pb.set(0)
            self._action_btn.configure(state="normal")
            self._set_status("Error!", "red")
            self._show_error(e)

        self._run_in_thread(work, done, error)
