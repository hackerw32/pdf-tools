import os
from tkinter import filedialog
import customtkinter as ctk
from src.ui.base_tool import BaseTool
from src.core import pdf_ops


class TextToPdfTool(BaseTool):
    TITLE = "Text → PDF"
    DESCRIPTION = "Convert plain text or .txt files to a formatted PDF"

    def build_ui(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24)

        # Source choice
        src_frame = ctk.CTkFrame(scroll, corner_radius=10, fg_color=("gray92", "gray18"))
        src_frame.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(src_frame, text="Source",
                     font=("Arial", 13, "bold")).pack(anchor="w", padx=16, pady=(12, 6))

        self.src_var = ctk.StringVar(value="type")
        ctk.CTkRadioButton(src_frame, text="Type or paste text below",
                           variable=self.src_var, value="type",
                           command=self._update_source).pack(anchor="w", padx=20, pady=3)
        ctk.CTkRadioButton(src_frame, text="Load from .txt file",
                           variable=self.src_var, value="file",
                           command=self._update_source).pack(anchor="w", padx=20, pady=3)

        self.file_row = ctk.CTkFrame(src_frame, fg_color="transparent")
        self.file_path_var = ctk.StringVar()
        ctk.CTkEntry(self.file_row, textvariable=self.file_path_var, width=300).pack(side="left", padx=20)
        ctk.CTkButton(self.file_row, text="Browse", width=80,
                       command=self._pick_file).pack(side="left", padx=4)

        # Text input
        self.text_area_frame = ctk.CTkFrame(scroll, corner_radius=10, fg_color=("gray92", "gray18"))
        self.text_area_frame.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(self.text_area_frame, text="Text Content",
                     font=("Arial", 13, "bold")).pack(anchor="w", padx=16, pady=(12, 6))
        self.text_box = ctk.CTkTextbox(self.text_area_frame, height=220, font=("Arial", 12))
        self.text_box.pack(fill="x", padx=12, pady=(0, 12))

        # Options
        opts = ctk.CTkFrame(scroll, corner_radius=10, fg_color=("gray92", "gray18"))
        opts.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(opts, text="Formatting Options",
                     font=("Arial", 13, "bold")).pack(anchor="w", padx=16, pady=(12, 6))

        row1 = ctk.CTkFrame(opts, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(0, 6))
        ctk.CTkLabel(row1, text="Title (optional):", font=("Arial", 12)).pack(side="left")
        self.title_var = ctk.StringVar()
        ctk.CTkEntry(row1, textvariable=self.title_var, width=250,
                     placeholder_text="Document title").pack(side="left", padx=8)

        row2 = ctk.CTkFrame(opts, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkLabel(row2, text="Font size:", font=("Arial", 12)).pack(side="left")
        self.font_size_var = ctk.StringVar(value="11")
        ctk.CTkOptionMenu(row2, variable=self.font_size_var,
                           values=["9", "10", "11", "12", "14", "16"],
                           width=80).pack(side="left", padx=8)

        out_row = ctk.CTkFrame(scroll, fg_color="transparent")
        out_row.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(out_row, text="Output file:", font=("Arial", 12)).pack(side="left")
        self.out_var = ctk.StringVar(value="output.pdf")
        ctk.CTkEntry(out_row, textvariable=self.out_var, width=300).pack(side="left", padx=8)
        ctk.CTkButton(out_row, text="Browse", width=80, command=self._pick_out).pack(side="left")

        self._action_btn = self._make_action_row(scroll, "📄  Create PDF", self._run)
        self.pb = self._make_progress(scroll)

        self._update_source()

    def _update_source(self):
        if self.src_var.get() == "file":
            self.file_row.pack(fill="x", pady=(0, 10))
            self.text_area_frame.pack_forget()
        else:
            self.file_row.pack_forget()
            self.text_area_frame.pack(fill="x", pady=(0, 12))

    def _pick_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if path:
            self.file_path_var.set(path)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.text_box.delete("1.0", "end")
                self.text_box.insert("1.0", content)
            except Exception:
                pass
            self.src_var.set("file")

    def _pick_out(self):
        path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                             filetypes=[("PDF files", "*.pdf")])
        if path:
            self.out_var.set(path)

    def _run(self):
        if self.src_var.get() == "file":
            src = self.file_path_var.get()
            if not src:
                self._show_error("Please select a text file.")
                return
            try:
                with open(src, "r", encoding="utf-8") as f:
                    text = f.read()
            except Exception as e:
                self._show_error(str(e))
                return
        else:
            text = self.text_box.get("1.0", "end-1c")
            if not text.strip():
                self._show_error("Please enter some text.")
                return

        out = self.out_var.get()
        if not out:
            self._show_error("Please specify an output file.")
            return
        if not os.path.isabs(out):
            out = os.path.join(os.path.expanduser("~"), "Desktop", out) if os.path.exists(os.path.expanduser("~") + "/Desktop") else os.path.abspath(out)

        title = self.title_var.get()
        font_size = int(self.font_size_var.get())

        self.pb.set(0)
        self._set_status("Creating PDF...", "orange")
        self._action_btn.configure(state="disabled")

        def work():
            return pdf_ops.text_to_pdf(text, out, font_size, title)

        def done(result):
            self.pb.set(1)
            self._action_btn.configure(state="normal")
            self._set_status("Done!", "green")
            self._show_success(f"PDF created:\n{result}")

        def error(e):
            self.pb.set(0)
            self._action_btn.configure(state="normal")
            self._set_status("Error!", "red")
            self._show_error(e)

        self._run_in_thread(work, done, error)
