import os
from tkinter import filedialog
import customtkinter as ctk
from src.ui.base_tool import BaseTool, DropZone
from src.core import pdf_ops


class RemoveDuplicatesTool(BaseTool):
    TITLE = "Remove Duplicate Pages"
    DESCRIPTION = "Detect and remove visually identical pages from a PDF"

    def build_ui(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24)

        self.drop = DropZone(scroll, label="Drop a PDF file here\nor click to browse",
                             multiple=False, filetypes=[("PDF files", "*.pdf")])
        self.drop.configure(height=160)
        self.drop.pack(fill="x", pady=(0, 16))
        self.drop.on_files_changed = self._on_file_selected

        info_box = ctk.CTkFrame(scroll, corner_radius=8,
                                fg_color=("#fff8e1", "#3a2f00"))
        info_box.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(info_box,
                     text="ℹ  Pages are compared visually (pixel hash). Two pages that look\n"
                          "   identical will be detected even if their internal data differs.",
                     font=("Arial", 11),
                     text_color=("#7d5a00", "#f0d080"),
                     justify="left").pack(anchor="w", padx=14, pady=10)

        self.info_label = ctk.CTkLabel(scroll, text="", font=("Arial", 12),
                                        text_color=("gray40", "gray60"))
        self.info_label.pack(anchor="w", pady=(0, 8))

        out_row = ctk.CTkFrame(scroll, fg_color="transparent")
        out_row.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(out_row, text="Output file:", font=("Arial", 12)).pack(side="left")
        self.out_var = ctk.StringVar()
        ctk.CTkEntry(out_row, textvariable=self.out_var, width=300).pack(side="left", padx=8)
        ctk.CTkButton(out_row, text="Browse", width=80, command=self._pick_out).pack(side="left")

        self._action_btn = self._make_action_row(scroll, "🔍  Remove Duplicates", self._run)
        self.pb = self._make_progress(scroll)

        self.result_label = ctk.CTkLabel(scroll, text="", font=("Arial", 12),
                                          text_color=("gray30", "gray70"))
        self.result_label.pack(anchor="w", pady=8)

    def _on_file_selected(self, files):
        if files:
            try:
                info = pdf_ops.get_pdf_info(files[0])
                self.info_label.configure(text=f"📄 {info['pages']} pages  |  {info['size_bytes']//1024} KB")
                self.out_var.set(self._make_output_path(files[0], "_deduped"))
            except Exception:
                pass

    def _pick_out(self):
        path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                             filetypes=[("PDF files", "*.pdf")])
        if path:
            self.out_var.set(path)

    def _run(self):
        if not self.drop.files:
            self._show_error("Please select a PDF file.")
            return

        input_path = self.drop.files[0]
        out = self.out_var.get()
        if not out:
            self._show_error("Please specify an output file.")
            return

        self.pb.set(0)
        self._set_status("Scanning pages...", "orange")
        self._action_btn.configure(state="disabled")
        self.result_label.configure(text="")

        def work():
            return pdf_ops.remove_duplicate_pages(input_path, out)

        def done(result):
            self.pb.set(1)
            self._action_btn.configure(state="normal")
            removed = result["removed"]
            if removed:
                self._set_status(f"Removed {len(removed)} duplicate page(s).", "green")
                self.result_label.configure(
                    text=f"Removed pages: {', '.join(str(p) for p in removed)}\n"
                         f"Kept {result['kept']} unique pages.")
                self._show_success(f"Done! Removed {len(removed)} duplicate page(s).\nSaved to:\n{out}")
            else:
                self._set_status("No duplicates found.", "blue")
                self.result_label.configure(text="No duplicate pages were found.")

        def error(e):
            self.pb.set(0)
            self._action_btn.configure(state="normal")
            self._set_status("Error!", "red")
            self._show_error(e)

        self._run_in_thread(work, done, error)
