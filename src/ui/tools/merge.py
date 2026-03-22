import os
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from src.ui.base_tool import BaseTool, DropZone
from src.core import pdf_ops


class MergeTool(BaseTool):
    TITLE = "Merge PDFs"
    DESCRIPTION = "Combine multiple PDF files into one document"

    def build_ui(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24)

        self.drop = DropZone(scroll, label="Drop PDF files here (order matters)\nor click to browse",
                             multiple=True, filetypes=[("PDF files", "*.pdf")])
        self.drop.configure(height=180)
        self.drop.pack(fill="x", pady=(0, 12))
        self.drop.on_files_changed = self._refresh_list

        # Reorder list
        list_frame = ctk.CTkFrame(scroll, corner_radius=10, fg_color=("gray92", "gray18"))
        list_frame.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(list_frame, text="File order (drag to reorder):",
                     font=("Arial", 13, "bold")).pack(anchor="w", padx=16, pady=(12, 6))

        self.list_container = ctk.CTkScrollableFrame(list_frame, height=160,
                                                      fg_color=("gray88", "gray22"))
        self.list_container.pack(fill="x", padx=12, pady=(0, 12))
        self.file_rows = []

        out_row = ctk.CTkFrame(scroll, fg_color="transparent")
        out_row.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(out_row, text="Output file:", font=("Arial", 12)).pack(side="left")
        self.out_var = ctk.StringVar(value="merged_output.pdf")
        ctk.CTkEntry(out_row, textvariable=self.out_var, width=280).pack(side="left", padx=8)
        ctk.CTkButton(out_row, text="Browse", width=80, command=self._pick_out).pack(side="left")

        self._action_btn = self._make_action_row(scroll, "🔗  Merge PDFs", self._run)
        self.pb = self._make_progress(scroll)

    def _pick_out(self):
        path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                             filetypes=[("PDF files", "*.pdf")])
        if path:
            self.out_var.set(path)

    def _refresh_list(self, files):
        for w in self.list_container.winfo_children():
            w.destroy()
        self.file_rows = list(files)
        self._render_list()

    def _render_list(self):
        for w in self.list_container.winfo_children():
            w.destroy()
        for i, f in enumerate(self.file_rows):
            row = ctk.CTkFrame(self.list_container, corner_radius=6,
                               fg_color=("gray83", "gray28"), height=36)
            row.pack(fill="x", pady=2, padx=4)
            row.pack_propagate(False)

            ctk.CTkLabel(row, text=f"{i+1}.", width=24,
                         font=("Arial", 11, "bold")).pack(side="left", padx=(6, 0))
            ctk.CTkLabel(row, text=os.path.basename(f),
                         font=("Arial", 11), anchor="w").pack(side="left", padx=6, fill="x", expand=True)

            btn_up = ctk.CTkButton(row, text="↑", width=28, height=24,
                                    fg_color=("gray70", "gray40"),
                                    hover_color=("gray60", "gray50"),
                                    command=lambda idx=i: self._move(idx, -1))
            btn_up.pack(side="right", padx=2)
            btn_dn = ctk.CTkButton(row, text="↓", width=28, height=24,
                                    fg_color=("gray70", "gray40"),
                                    hover_color=("gray60", "gray50"),
                                    command=lambda idx=i: self._move(idx, 1))
            btn_dn.pack(side="right", padx=2)
            btn_del = ctk.CTkButton(row, text="✕", width=28, height=24,
                                     fg_color=("gray70", "gray40"),
                                     hover_color=("#c0392b", "#e74c3c"),
                                     command=lambda idx=i: self._remove(idx))
            btn_del.pack(side="right", padx=(2, 6))

    def _move(self, idx, direction):
        new_idx = idx + direction
        if 0 <= new_idx < len(self.file_rows):
            self.file_rows[idx], self.file_rows[new_idx] = self.file_rows[new_idx], self.file_rows[idx]
            self._render_list()

    def _remove(self, idx):
        self.file_rows.pop(idx)
        self._render_list()

    def _run(self):
        if len(self.file_rows) < 2:
            self._show_error("Please select at least 2 PDF files to merge.")
            return

        out = self.out_var.get()
        if not out:
            self._show_error("Please specify an output file path.")
            return

        if not os.path.isabs(out):
            out = os.path.join(os.path.dirname(self.file_rows[0]), out)

        self.pb.set(0)
        self._set_status("Merging...", "orange")
        self._action_btn.configure(state="disabled")

        files = list(self.file_rows)

        def work():
            return pdf_ops.merge_pdfs(files, out)

        def done(result):
            self.pb.set(1)
            self._action_btn.configure(state="normal")
            self._set_status("Done!", "green")
            self._show_success(f"Merged {len(files)} PDFs into:\n{result}")

        def error(e):
            self.pb.set(0)
            self._action_btn.configure(state="normal")
            self._set_status("Error!", "red")
            self._show_error(e)

        self._run_in_thread(work, done, error)
