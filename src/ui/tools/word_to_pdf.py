import os
from tkinter import filedialog
import customtkinter as ctk
from src.ui.base_tool import BaseTool, DropZone
from src.core import pdf_ops


class WordToPdfTool(BaseTool):
    TITLE = "Word / Excel → PDF"
    DESCRIPTION = "Convert .docx, .doc, .odt, .xlsx, .xls files to PDF (requires LibreOffice)"

    SUPPORTED = [("Office files", "*.docx *.doc *.odt *.xlsx *.xls *.ods *.pptx *.ppt *.odp"),
                 ("All files", "*.*")]

    def build_ui(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24)

        info_box = ctk.CTkFrame(scroll, corner_radius=8,
                                fg_color=("#e8f4fd", "#1a3a4a"))
        info_box.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(info_box,
                     text="ℹ  This tool requires LibreOffice to be installed.\n"
                          "Install: sudo apt install libreoffice  (Ubuntu/Debian)\n"
                          "         or download from libreoffice.org",
                     font=("Arial", 11),
                     text_color=("#1a5276", "#7fc8f0"),
                     justify="left").pack(anchor="w", padx=14, pady=10)

        self.drop = DropZone(scroll, label="Drop Word/Excel files here\nor click to browse",
                             multiple=True, filetypes=self.SUPPORTED)
        self.drop.configure(height=180)
        self.drop.pack(fill="x", pady=(0, 12))

        out_row = ctk.CTkFrame(scroll, fg_color="transparent")
        out_row.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(out_row, text="Output folder:", font=("Arial", 12)).pack(side="left")
        self.out_dir_var = ctk.StringVar(value="Same as input")
        ctk.CTkEntry(out_row, textvariable=self.out_dir_var, width=280).pack(side="left", padx=8)
        ctk.CTkButton(out_row, text="Browse", width=80, command=self._pick_outdir).pack(side="left")

        self._action_btn = self._make_action_row(scroll, "📝→📄  Convert to PDF", self._run)
        self.pb = self._make_progress(scroll)

        # Results log
        log_frame = ctk.CTkFrame(scroll, corner_radius=10, fg_color=("gray92", "gray18"))
        log_frame.pack(fill="x", pady=(12, 0))
        ctk.CTkLabel(log_frame, text="Conversion Log",
                     font=("Arial", 12, "bold")).pack(anchor="w", padx=16, pady=(10, 4))
        self.log_box = ctk.CTkTextbox(log_frame, height=120, font=("Courier", 10))
        self.log_box.pack(fill="x", padx=12, pady=(0, 10))

    def _pick_outdir(self):
        d = filedialog.askdirectory()
        if d:
            self.out_dir_var.set(d)

    def _log(self, msg):
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")

    def _run(self):
        if not self.drop.files:
            self._show_error("Please select at least one file.")
            return

        out_dir_base = self.out_dir_var.get()
        files = list(self.drop.files)

        self.pb.set(0)
        self.log_box.delete("1.0", "end")
        self._set_status("Converting...", "orange")
        self._action_btn.configure(state="disabled")

        def work():
            results = []
            for i, f in enumerate(files):
                out_dir = out_dir_base if out_dir_base != "Same as input" else os.path.dirname(f)
                out_path = os.path.join(out_dir, os.path.splitext(os.path.basename(f))[0] + ".pdf")
                try:
                    pdf_ops.word_to_pdf(f, out_path)
                    results.append(("ok", os.path.basename(f), out_path))
                    self.after(0, lambda name=os.path.basename(f), p=out_path:
                               self._log(f"✓ {name} → {os.path.basename(p)}"))
                except Exception as e:
                    results.append(("error", os.path.basename(f), str(e)))
                    self.after(0, lambda name=os.path.basename(f), err=str(e):
                               self._log(f"✗ {name}: {err}"))
                self.after(0, lambda v=(i + 1) / len(files): self.pb.set(v))
            return results

        def done(results):
            ok = sum(1 for r in results if r[0] == "ok")
            fail = len(results) - ok
            self.pb.set(1)
            self._action_btn.configure(state="normal")
            self._set_status(f"Done! {ok} ok, {fail} failed.", "green" if fail == 0 else "orange")

        def error(e):
            self.pb.set(0)
            self._action_btn.configure(state="normal")
            self._set_status("Error!", "red")
            self._show_error(e)

        self._run_in_thread(work, done, error)
