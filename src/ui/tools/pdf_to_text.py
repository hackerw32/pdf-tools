import os
from tkinter import filedialog
import customtkinter as ctk
from src.ui.base_tool import BaseTool, DropZone
from src.core import pdf_ops


class PdfToTextTool(BaseTool):
    TITLE = "PDF → Text"
    DESCRIPTION = "Extract all text content from a PDF document"

    def build_ui(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24)

        self.drop = DropZone(scroll, label="Drop a PDF file here\nor click to browse",
                             multiple=False, filetypes=[("PDF files", "*.pdf")])
        self.drop.configure(height=150)
        self.drop.pack(fill="x", pady=(0, 16))
        self.drop.on_files_changed = self._on_file_selected

        # Preview
        preview_frame = ctk.CTkFrame(scroll, corner_radius=10, fg_color=("gray92", "gray18"))
        preview_frame.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(preview_frame, text="Text Preview",
                     font=("Arial", 13, "bold")).pack(anchor="w", padx=16, pady=(12, 6))

        self.text_box = ctk.CTkTextbox(preview_frame, height=200, font=("Courier", 11))
        self.text_box.pack(fill="x", padx=12, pady=(0, 12))

        # Options
        opts = ctk.CTkFrame(scroll, corner_radius=10, fg_color=("gray92", "gray18"))
        opts.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(opts, text="Output Options",
                     font=("Arial", 13, "bold")).pack(anchor="w", padx=16, pady=(12, 6))

        self.save_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(opts, text="Save to .txt file",
                         variable=self.save_var).pack(anchor="w", padx=16, pady=(0, 8))

        out_row = ctk.CTkFrame(opts, fg_color="transparent")
        out_row.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkLabel(out_row, text="Output file:", font=("Arial", 12)).pack(side="left")
        self.out_var = ctk.StringVar()
        ctk.CTkEntry(out_row, textvariable=self.out_var, width=280).pack(side="left", padx=8)
        ctk.CTkButton(out_row, text="Browse", width=80, command=self._pick_out).pack(side="left")

        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 8))

        self._action_btn = ctk.CTkButton(btn_row, text="📄  Extract Text",
                                          font=("Arial", 13, "bold"), height=40,
                                          command=self._run)
        self._action_btn.pack(side="left", padx=(0, 8))

        self._copy_btn = ctk.CTkButton(btn_row, text="📋 Copy to Clipboard",
                                        height=40, width=160,
                                        fg_color=("gray80", "gray30"),
                                        hover_color=("gray70", "gray40"),
                                        text_color=("gray10", "gray90"),
                                        command=self._copy_text)
        self._copy_btn.pack(side="left")

        self._status_label = ctk.CTkLabel(btn_row, text="", font=("Arial", 12),
                                           text_color=("gray40", "gray60"))
        self._status_label.pack(side="left", padx=8)
        self.pb = self._make_progress(scroll)

        self._extracted_text = ""

    def _on_file_selected(self, files):
        if files:
            self.out_var.set(self._make_output_path(files[0], "", ".txt"))

    def _pick_out(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt",
                                             filetypes=[("Text files", "*.txt")])
        if path:
            self.out_var.set(path)

    def _copy_text(self):
        if self._extracted_text:
            self.clipboard_clear()
            self.clipboard_append(self._extracted_text)
            self._set_status("Copied to clipboard!", "green")

    def _run(self):
        if not self.drop.files:
            self._show_error("Please select a PDF file.")
            return

        input_path = self.drop.files[0]
        out = self.out_var.get() if self.save_var.get() else None

        self.pb.set(0)
        self._set_status("Extracting...", "orange")
        self._action_btn.configure(state="disabled")

        def work():
            return pdf_ops.pdf_to_text(input_path, out)

        def done(text):
            self.pb.set(1)
            self._action_btn.configure(state="normal")
            self._extracted_text = text
            self.text_box.delete("1.0", "end")
            self.text_box.insert("1.0", text[:5000] + ("..." if len(text) > 5000 else ""))
            self._set_status(f"Done! {len(text)} characters extracted.", "green")
            if out:
                self._show_success(f"Saved to:\n{out}")

        def error(e):
            self.pb.set(0)
            self._action_btn.configure(state="normal")
            self._set_status("Error!", "red")
            self._show_error(e)

        self._run_in_thread(work, done, error)
