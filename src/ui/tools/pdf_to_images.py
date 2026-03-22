import os
from tkinter import filedialog
import customtkinter as ctk
from src.ui.base_tool import BaseTool, DropZone
from src.core import pdf_ops


class PdfToImagesTool(BaseTool):
    TITLE = "PDF → Images"
    DESCRIPTION = "Convert each PDF page to an image file"

    def build_ui(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24)

        self.drop = DropZone(scroll, label="Drop PDF files here\nor click to browse",
                             multiple=True, filetypes=[("PDF files", "*.pdf")])
        self.drop.configure(height=160)
        self.drop.pack(fill="x", pady=(0, 16))

        opts = ctk.CTkFrame(scroll, corner_radius=10, fg_color=("gray92", "gray18"))
        opts.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(opts, text="Options", font=("Arial", 13, "bold")).pack(anchor="w", padx=16, pady=(12, 6))

        # Format
        fmt_row = ctk.CTkFrame(opts, fg_color="transparent")
        fmt_row.pack(fill="x", padx=16, pady=(0, 6))
        ctk.CTkLabel(fmt_row, text="Format:", font=("Arial", 12)).pack(side="left")
        self.fmt_var = ctk.StringVar(value="png")
        ctk.CTkOptionMenu(fmt_row, variable=self.fmt_var,
                           values=["png", "jpg", "tiff", "bmp"],
                           width=100).pack(side="left", padx=8)

        # DPI
        dpi_row = ctk.CTkFrame(opts, fg_color="transparent")
        dpi_row.pack(fill="x", padx=16, pady=(0, 6))
        ctk.CTkLabel(dpi_row, text="DPI (resolution):", font=("Arial", 12)).pack(side="left")
        self.dpi_val = ctk.CTkLabel(dpi_row, text=f"{self.settings.get('image_dpi', 150)} DPI",
                                     font=("Arial", 12, "bold"), width=60)
        self.dpi_val.pack(side="right", padx=8)

        self.dpi_slider = ctk.CTkSlider(opts, from_=72, to=300, number_of_steps=15,
                                         command=self._update_dpi)
        self.dpi_slider.set(self.settings.get("image_dpi", 150))
        self.dpi_slider.pack(fill="x", padx=16, pady=(0, 4))

        dpi_hints = ctk.CTkFrame(opts, fg_color="transparent")
        dpi_hints.pack(fill="x", padx=16, pady=(0, 12))
        for label, val in [("Screen (72)", 72), ("Web (96)", 96), ("Print (150)", 150), ("HD (300)", 300)]:
            ctk.CTkButton(dpi_hints, text=label, height=26, font=("Arial", 10),
                           fg_color=("gray80", "gray30"), hover_color=("gray70", "gray40"),
                           text_color=("gray10", "gray90"),
                           command=lambda v=val: self._set_dpi(v)).pack(side="left", padx=3)

        out_row = ctk.CTkFrame(scroll, fg_color="transparent")
        out_row.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(out_row, text="Output folder:", font=("Arial", 12)).pack(side="left")
        self.out_dir_var = ctk.StringVar(value="Same as input")
        ctk.CTkEntry(out_row, textvariable=self.out_dir_var, width=280).pack(side="left", padx=8)
        ctk.CTkButton(out_row, text="Browse", width=80, command=self._pick_outdir).pack(side="left")

        self._action_btn = self._make_action_row(scroll, "🖼  Convert to Images", self._run)
        self.pb = self._make_progress(scroll)

    def _update_dpi(self, val):
        self.dpi_val.configure(text=f"{int(val)} DPI")

    def _set_dpi(self, val):
        self.dpi_slider.set(val)
        self.dpi_val.configure(text=f"{val} DPI")

    def _pick_outdir(self):
        d = filedialog.askdirectory()
        if d:
            self.out_dir_var.set(d)

    def _run(self):
        if not self.drop.files:
            self._show_error("Please select at least one PDF file.")
            return

        dpi = int(self.dpi_slider.get())
        fmt = self.fmt_var.get()
        out_dir_base = self.out_dir_var.get()

        self.pb.set(0)
        self._set_status("Converting...", "orange")
        self._action_btn.configure(state="disabled")

        files = list(self.drop.files)

        def work():
            all_outputs = []
            for i, f in enumerate(files):
                out_dir = out_dir_base if out_dir_base != "Same as input" else os.path.dirname(f)
                outputs = pdf_ops.pdf_to_images(f, out_dir, dpi, fmt)
                all_outputs.extend(outputs)
                self.after(0, lambda v=(i + 1) / len(files): self.pb.set(v))
            return all_outputs

        def done(outputs):
            self.pb.set(1)
            self._action_btn.configure(state="normal")
            self._set_status(f"Done! {len(outputs)} image(s) created.", "green")
            self._show_success(f"Created {len(outputs)} image file(s).")

        def error(e):
            self.pb.set(0)
            self._action_btn.configure(state="normal")
            self._set_status("Error!", "red")
            self._show_error(e)

        self._run_in_thread(work, done, error)
