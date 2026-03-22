import os
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from PIL import ImageTk
from src.ui.base_tool import BaseTool, DropZone
from src.core import pdf_ops


class RotateTool(BaseTool):
    TITLE = "Rotate Pages"
    DESCRIPTION = "Rotate individual or all pages in a PDF"

    def build_ui(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24)

        self.drop = DropZone(scroll, label="Drop a PDF file here\nor click to browse",
                             multiple=False, filetypes=[("PDF files", "*.pdf")])
        self.drop.configure(height=150)
        self.drop.pack(fill="x", pady=(0, 12))
        self.drop.on_files_changed = self._load_pdf

        self.info_label = ctk.CTkLabel(scroll, text="", font=("Arial", 12),
                                        text_color=("gray40", "gray60"))
        self.info_label.pack(anchor="w", pady=(0, 8))

        # Mode
        mode_frame = ctk.CTkFrame(scroll, corner_radius=10, fg_color=("gray92", "gray18"))
        mode_frame.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(mode_frame, text="Rotation Options",
                     font=("Arial", 13, "bold")).pack(anchor="w", padx=16, pady=(12, 6))

        self.mode_var = ctk.StringVar(value="all")
        ctk.CTkRadioButton(mode_frame, text="Rotate all pages",
                           variable=self.mode_var, value="all").pack(anchor="w", padx=20, pady=3)
        ctk.CTkRadioButton(mode_frame, text="Rotate specific pages",
                           variable=self.mode_var, value="specific",
                           command=self._update_mode).pack(anchor="w", padx=20, pady=3)
        self.mode_var.trace("w", lambda *_: self._update_mode())

        self.pages_frame = ctk.CTkFrame(mode_frame, fg_color="transparent")
        ctk.CTkLabel(self.pages_frame,
                     text="Page numbers (e.g. 1, 3, 5-8):",
                     font=("Arial", 12)).pack(anchor="w", padx=20, pady=(4, 2))
        self.pages_entry = ctk.CTkEntry(self.pages_frame, placeholder_text="1, 3, 5-8",
                                         width=250)
        self.pages_entry.pack(anchor="w", padx=20, pady=(0, 10))

        # Rotation angle
        angle_frame = ctk.CTkFrame(scroll, corner_radius=10, fg_color=("gray92", "gray18"))
        angle_frame.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(angle_frame, text="Rotation Angle",
                     font=("Arial", 13, "bold")).pack(anchor="w", padx=16, pady=(12, 6))

        self.angle_var = ctk.StringVar(value="90")
        btn_row = ctk.CTkFrame(angle_frame, fg_color="transparent")
        btn_row.pack(anchor="w", padx=16, pady=(0, 12))
        for angle in ["90", "180", "270"]:
            ctk.CTkRadioButton(btn_row, text=f"{angle}° CW",
                               variable=self.angle_var, value=angle).pack(side="left", padx=12)

        out_row = ctk.CTkFrame(scroll, fg_color="transparent")
        out_row.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(out_row, text="Output file:", font=("Arial", 12)).pack(side="left")
        self.out_var = ctk.StringVar()
        ctk.CTkEntry(out_row, textvariable=self.out_var, width=300).pack(side="left", padx=8)
        ctk.CTkButton(out_row, text="Browse", width=80, command=self._pick_out).pack(side="left")

        self._action_btn = self._make_action_row(scroll, "↻  Rotate Pages", self._run)
        self.pb = self._make_progress(scroll)

    def _load_pdf(self, files):
        if files:
            try:
                info = pdf_ops.get_pdf_info(files[0])
                self.info_label.configure(text=f"📄 {info['pages']} pages")
                self.out_var.set(self._make_output_path(files[0], "_rotated"))
            except Exception:
                pass

    def _update_mode(self, *_):
        if self.mode_var.get() == "specific":
            self.pages_frame.pack(fill="x")
        else:
            self.pages_frame.pack_forget()

    def _pick_out(self):
        path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                             filetypes=[("PDF files", "*.pdf")])
        if path:
            self.out_var.set(path)

    def _parse_pages(self, text, total):
        pages = set()
        for part in text.split(","):
            part = part.strip()
            if "-" in part:
                a, b = part.split("-", 1)
                pages.update(range(int(a.strip()) - 1, int(b.strip())))
            elif part.isdigit():
                pages.add(int(part) - 1)
        return {p for p in pages if 0 <= p < total}

    def _run(self):
        if not self.drop.files:
            self._show_error("Please select a PDF file.")
            return

        input_path = self.drop.files[0]
        out = self.out_var.get()
        if not out:
            self._show_error("Please specify an output file path.")
            return

        angle = int(self.angle_var.get())
        info = pdf_ops.get_pdf_info(input_path)
        total = info["pages"]

        if self.mode_var.get() == "all":
            page_rots = {i: angle for i in range(total)}
        else:
            try:
                pages = self._parse_pages(self.pages_entry.get(), total)
                if not pages:
                    self._show_error("No valid pages specified.")
                    return
                page_rots = {p: angle for p in pages}
            except Exception as e:
                self._show_error(str(e))
                return

        self.pb.set(0)
        self._set_status("Rotating...", "orange")
        self._action_btn.configure(state="disabled")

        def work():
            return pdf_ops.rotate_pages(input_path, out, page_rots)

        def done(result):
            self.pb.set(1)
            self._action_btn.configure(state="normal")
            self._set_status("Done!", "green")
            self._show_success(f"Saved to:\n{result}")

        def error(e):
            self.pb.set(0)
            self._action_btn.configure(state="normal")
            self._set_status("Error!", "red")
            self._show_error(e)

        self._run_in_thread(work, done, error)
