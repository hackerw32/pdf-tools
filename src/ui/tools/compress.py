import os
from tkinter import filedialog
import customtkinter as ctk
from src.ui.base_tool import BaseTool, DropZone
from src.core import pdf_ops


class CompressTool(BaseTool):
    TITLE = "Compress PDF"
    DESCRIPTION = "Reduce PDF file size by compressing images and streams"

    def build_ui(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24)

        self.drop = DropZone(scroll, label="Drop PDF files here\nor click to browse",
                             multiple=True, filetypes=[("PDF files", "*.pdf")])
        self.drop.pack(fill="x", pady=(0, 16))
        self.drop.configure(height=180)

        opts = ctk.CTkFrame(scroll, corner_radius=10, fg_color=("gray92", "gray18"))
        opts.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(opts, text="Quality / Compression Settings",
                     font=("Arial", 13, "bold")).pack(anchor="w", padx=16, pady=(12, 6))

        q_row = ctk.CTkFrame(opts, fg_color="transparent")
        q_row.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkLabel(q_row, text="Image quality:", font=("Arial", 12)).pack(side="left")
        self.quality_val = ctk.CTkLabel(q_row, text=f"{self.settings.get('compression_quality', 75)}%",
                                         font=("Arial", 12, "bold"), width=40)
        self.quality_val.pack(side="right", padx=(0, 8))

        self.quality_slider = ctk.CTkSlider(opts, from_=10, to=95, number_of_steps=17,
                                             command=self._update_quality)
        self.quality_slider.set(self.settings.get("compression_quality", 75))
        self.quality_slider.pack(fill="x", padx=16, pady=(0, 8))

        hints = ctk.CTkFrame(opts, fg_color="transparent")
        hints.pack(fill="x", padx=16, pady=(0, 12))
        for label, val in [("Max compression (10%)", 10), ("Balanced (75%)", 75), ("High quality (95%)", 95)]:
            btn = ctk.CTkButton(hints, text=label, height=28, font=("Arial", 11),
                                 fg_color=("gray80", "gray30"),
                                 hover_color=("gray70", "gray40"),
                                 text_color=("gray10", "gray90"),
                                 command=lambda v=val: self._set_quality(v))
            btn.pack(side="left", padx=4)

        out_row = ctk.CTkFrame(scroll, fg_color="transparent")
        out_row.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(out_row, text="Output folder:", font=("Arial", 12)).pack(side="left")
        self.out_dir_var = ctk.StringVar(value=self.settings.get("default_output_dir", "Same as input"))
        ctk.CTkEntry(out_row, textvariable=self.out_dir_var, width=280).pack(side="left", padx=8)
        ctk.CTkButton(out_row, text="Browse", width=80, command=self._pick_outdir).pack(side="left")

        self._action_btn = self._make_action_row(scroll, "🗜  Compress PDFs", self._run)
        self.pb = self._make_progress(scroll)

    def _update_quality(self, val):
        self.quality_val.configure(text=f"{int(val)}%")

    def _set_quality(self, val):
        self.quality_slider.set(val)
        self.quality_val.configure(text=f"{val}%")

    def _pick_outdir(self):
        d = filedialog.askdirectory()
        if d:
            self.out_dir_var.set(d)

    def _run(self):
        files = self.drop.files
        if not files:
            self._show_error("Please select at least one PDF file.")
            return

        quality = int(self.quality_slider.get())
        out_dir = self.out_dir_var.get() if self.out_dir_var.get() != "Same as input" else ""

        self.pb.set(0)
        self._set_status("Compressing...", "orange")
        self._action_btn.configure(state="disabled")

        def work():
            results = []
            for i, f in enumerate(files):
                o_dir = out_dir or os.path.dirname(f)
                stem, ext = os.path.splitext(os.path.basename(f))
                out = os.path.join(o_dir, f"{stem}_compressed{ext}")
                r = pdf_ops.compress_pdf(f, out, quality)
                results.append((os.path.basename(f), r))
                self.after(0, lambda v=(i + 1) / len(files): self.pb.set(v))
            return results

        def done(results):
            self.pb.set(1)
            self._action_btn.configure(state="normal")
            lines = []
            for name, r in results:
                lines.append(f"{name}: {r['original_size']//1024}KB → {r['compressed_size']//1024}KB (saved {r['ratio']}%)")
            self._set_status(f"Done! {len(results)} file(s) compressed.", "green")
            self._show_success("\n".join(lines))

        def error(e):
            self.pb.set(0)
            self._action_btn.configure(state="normal")
            self._set_status("Error!", "red")
            self._show_error(e)

        self._run_in_thread(work, done, error)
