"""Sign PDF with drawn or image signature."""
import os
import tempfile
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw
from src.ui.base_tool import BaseTool, DropZone
from src.core import pdf_ops


class SignaturePad(ctk.CTkFrame):
    """Canvas for drawing a signature."""

    def __init__(self, master, pen_color="#000000", pen_size=2, **kwargs):
        super().__init__(master, **kwargs)
        self.pen_color = pen_color
        self.pen_size = pen_size

        self._canvas = tk.Canvas(self, bg="white", cursor="crosshair",
                                  highlightthickness=1, highlightbackground="gray")
        self._canvas.pack(fill="both", expand=True, padx=4, pady=4)

        self._last_x = None
        self._last_y = None
        self._lines = []

        self._canvas.bind("<ButtonPress-1>", self._start)
        self._canvas.bind("<B1-Motion>", self._draw)
        self._canvas.bind("<ButtonRelease-1>", self._stop)

    def _start(self, event):
        self._last_x = event.x
        self._last_y = event.y

    def _draw(self, event):
        if self._last_x is not None:
            line_id = self._canvas.create_line(
                self._last_x, self._last_y, event.x, event.y,
                fill=self.pen_color, width=self.pen_size,
                capstyle=tk.ROUND, smooth=True
            )
            self._lines.append((self._last_x, self._last_y, event.x, event.y))
        self._last_x = event.x
        self._last_y = event.y

    def _stop(self, event):
        self._last_x = None
        self._last_y = None

    def clear(self):
        self._canvas.delete("all")
        self._lines = []

    def is_empty(self):
        return len(self._lines) == 0

    def export_image(self, path: str, bg="white"):
        """Export the signature to a PNG with transparent background."""
        w = self._canvas.winfo_width()
        h = self._canvas.winfo_height()
        img = Image.new("RGBA", (w, h), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)

        r, g, b = int(self.pen_color[1:3], 16), int(self.pen_color[3:5], 16), int(self.pen_color[5:7], 16)
        for x1, y1, x2, y2 in self._lines:
            draw.line([(x1, y1), (x2, y2)], fill=(r, g, b, 255), width=self.pen_size * 2)
        img.save(path, "PNG")
        return path


class SignPdfTool(BaseTool):
    TITLE = "Sign PDF"
    DESCRIPTION = "Add a handwritten or image signature to a PDF page"

    def build_ui(self):
        self._sig_image_path = None

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24)

        # PDF input
        self.drop = DropZone(scroll, label="Drop a PDF file here\nor click to browse",
                             multiple=False, filetypes=[("PDF files", "*.pdf")])
        self.drop.configure(height=140)
        self.drop.pack(fill="x", pady=(0, 12))
        self.drop.on_files_changed = self._on_pdf_selected

        # Signature source
        sig_frame = ctk.CTkFrame(scroll, corner_radius=10, fg_color=("gray92", "gray18"))
        sig_frame.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(sig_frame, text="Signature",
                     font=("Arial", 13, "bold")).pack(anchor="w", padx=16, pady=(12, 6))

        self.sig_mode = ctk.StringVar(value="draw")
        mode_row = ctk.CTkFrame(sig_frame, fg_color="transparent")
        mode_row.pack(fill="x", padx=16, pady=(0, 8))
        ctk.CTkRadioButton(mode_row, text="Draw signature",
                           variable=self.sig_mode, value="draw",
                           command=self._update_sig_mode).pack(side="left", padx=(0, 20))
        ctk.CTkRadioButton(mode_row, text="Upload signature image",
                           variable=self.sig_mode, value="image",
                           command=self._update_sig_mode).pack(side="left")

        # Draw pad
        self.draw_frame = ctk.CTkFrame(sig_frame, fg_color="transparent")
        self.draw_frame.pack(fill="x", padx=16)

        pad_opts = ctk.CTkFrame(self.draw_frame, fg_color="transparent")
        pad_opts.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(pad_opts, text="Pen size:", font=("Arial", 11)).pack(side="left")
        self.pen_size_var = ctk.StringVar(value="2")
        ctk.CTkOptionMenu(pad_opts, variable=self.pen_size_var,
                           values=["1", "2", "3", "4", "5"], width=70,
                           command=self._update_pen).pack(side="left", padx=6)

        ctk.CTkLabel(pad_opts, text="Color:", font=("Arial", 11)).pack(side="left", padx=(12, 4))
        self.color_var = ctk.StringVar(value="#000000")
        self.color_btn = ctk.CTkButton(pad_opts, text="  ■  ", width=50, height=28,
                                        fg_color="#000000",
                                        command=self._pick_color)
        self.color_btn.pack(side="left")

        self.sig_pad = SignaturePad(self.draw_frame, pen_color="#000000", pen_size=2)
        self.sig_pad.configure(height=160)
        self.sig_pad.pack(fill="x", pady=(0, 6))

        clear_btn = ctk.CTkButton(self.draw_frame, text="🗑 Clear",
                                   height=30, width=80,
                                   fg_color=("gray80", "gray30"),
                                   hover_color=("gray70", "gray40"),
                                   text_color=("gray10", "gray90"),
                                   command=self.sig_pad.clear)
        clear_btn.pack(anchor="w", pady=(0, 10))

        # Image upload
        self.image_frame = ctk.CTkFrame(sig_frame, fg_color="transparent")
        img_row = ctk.CTkFrame(self.image_frame, fg_color="transparent")
        img_row.pack(fill="x", padx=16, pady=(0, 8))
        self.img_path_var = ctk.StringVar(value="No image selected")
        ctk.CTkLabel(img_row, textvariable=self.img_path_var, font=("Arial", 11),
                     width=280, anchor="w").pack(side="left")
        ctk.CTkButton(img_row, text="Browse", width=80,
                       command=self._pick_sig_image).pack(side="left", padx=8)

        self.sig_preview_label = ctk.CTkLabel(self.image_frame, text="",
                                               font=("Arial", 11))
        self.sig_preview_label.pack(pady=(0, 10))

        # Placement options
        place_frame = ctk.CTkFrame(scroll, corner_radius=10, fg_color=("gray92", "gray18"))
        place_frame.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(place_frame, text="Placement",
                     font=("Arial", 13, "bold")).pack(anchor="w", padx=16, pady=(12, 6))

        # Page selection
        page_row = ctk.CTkFrame(place_frame, fg_color="transparent")
        page_row.pack(fill="x", padx=16, pady=(0, 6))
        ctk.CTkLabel(page_row, text="Page:", font=("Arial", 12)).pack(side="left")
        self.page_var = ctk.StringVar(value="1")
        self.page_entry = ctk.CTkEntry(page_row, textvariable=self.page_var, width=60)
        self.page_entry.pack(side="left", padx=8)
        self.page_info = ctk.CTkLabel(page_row, text="", font=("Arial", 11),
                                       text_color=("gray40", "gray60"))
        self.page_info.pack(side="left")

        # Quick position
        pos_row = ctk.CTkFrame(place_frame, fg_color="transparent")
        pos_row.pack(fill="x", padx=16, pady=(0, 6))
        ctk.CTkLabel(pos_row, text="Quick position:", font=("Arial", 12)).pack(side="left")
        for label, cmd in [
            ("Bottom Left", lambda: self._set_pos(50, 680)),
            ("Bottom Center", lambda: self._set_pos(200, 680)),
            ("Bottom Right", lambda: self._set_pos(380, 680)),
        ]:
            ctk.CTkButton(pos_row, text=label, height=28, font=("Arial", 10),
                           fg_color=("gray80", "gray30"),
                           hover_color=("gray70", "gray40"),
                           text_color=("gray10", "gray90"),
                           command=cmd).pack(side="left", padx=4)

        # Manual position
        xy_row = ctk.CTkFrame(place_frame, fg_color="transparent")
        xy_row.pack(fill="x", padx=16, pady=(0, 6))
        for label, attr, default in [("X:", "x_var", "50"), ("Y:", "y_var", "680"),
                                      ("W:", "w_var", "200"), ("H:", "h_var", "80")]:
            ctk.CTkLabel(xy_row, text=label, font=("Arial", 11), width=20).pack(side="left")
            var = ctk.StringVar(value=default)
            setattr(self, attr, var)
            ctk.CTkEntry(xy_row, textvariable=var, width=55).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(place_frame, text="(coordinates in PDF points from bottom-left; 1pt ≈ 0.35mm)",
                     font=("Arial", 10),
                     text_color=("gray50", "gray60")).pack(anchor="w", padx=16, pady=(0, 12))

        # Output
        out_row = ctk.CTkFrame(scroll, fg_color="transparent")
        out_row.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(out_row, text="Output file:", font=("Arial", 12)).pack(side="left")
        self.out_var = ctk.StringVar()
        ctk.CTkEntry(out_row, textvariable=self.out_var, width=300).pack(side="left", padx=8)
        ctk.CTkButton(out_row, text="Browse", width=80, command=self._pick_out).pack(side="left")

        self._action_btn = self._make_action_row(scroll, "✍  Apply Signature", self._run)
        self.pb = self._make_progress(scroll)

        self._update_sig_mode()

    def _on_pdf_selected(self, files):
        if files:
            try:
                info = pdf_ops.get_pdf_info(files[0])
                self.page_info.configure(text=f"(1–{info['pages']})")
                self.out_var.set(self._make_output_path(files[0], "_signed"))
            except Exception:
                pass

    def _update_sig_mode(self):
        if self.sig_mode.get() == "draw":
            self.draw_frame.pack(fill="x", padx=16)
            self.image_frame.pack_forget()
        else:
            self.draw_frame.pack_forget()
            self.image_frame.pack(fill="x")

    def _update_pen(self, val):
        self.sig_pad.pen_size = int(val)

    def _pick_color(self):
        try:
            from tkinter import colorchooser
            color = colorchooser.askcolor(color=self.color_var.get())[1]
            if color:
                self.color_var.set(color)
                self.sig_pad.pen_color = color
                self.color_btn.configure(fg_color=color)
        except Exception:
            pass

    def _pick_sig_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff")])
        if path:
            self._sig_image_path = path
            self.img_path_var.set(os.path.basename(path))
            try:
                img = Image.open(path)
                img.thumbnail((200, 80))
                self._preview_tk = ImageTk.PhotoImage(img)
                self.sig_preview_label.configure(image=self._preview_tk, text="")
            except Exception:
                pass

    def _set_pos(self, x, y):
        self.x_var.set(str(x))
        self.y_var.set(str(y))

    def _pick_out(self):
        path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                             filetypes=[("PDF files", "*.pdf")])
        if path:
            self.out_var.set(path)

    def _run(self):
        if not self.drop.files:
            self._show_error("Please select a PDF file.")
            return

        out = self.out_var.get()
        if not out:
            self._show_error("Please specify an output file.")
            return

        try:
            page_idx = int(self.page_var.get()) - 1
            x = float(self.x_var.get())
            y = float(self.y_var.get())
            w = float(self.w_var.get())
            h = float(self.h_var.get())
        except ValueError:
            self._show_error("Invalid position values.")
            return

        input_path = self.drop.files[0]

        if self.sig_mode.get() == "draw":
            if self.sig_pad.is_empty():
                self._show_error("Please draw your signature.")
                return
            tmp_sig = tempfile.mktemp(suffix=".png")
            self.sig_pad.export_image(tmp_sig)
            sig_path = tmp_sig
            cleanup = True
        else:
            if not self._sig_image_path:
                self._show_error("Please select a signature image.")
                return
            sig_path = self._sig_image_path
            cleanup = False

        self.pb.set(0)
        self._set_status("Signing...", "orange")
        self._action_btn.configure(state="disabled")

        def work():
            result = pdf_ops.sign_pdf(input_path, out, sig_path, page_idx, x, y, w, h)
            if cleanup:
                try:
                    os.remove(sig_path)
                except Exception:
                    pass
            return result

        def done(result):
            self.pb.set(1)
            self._action_btn.configure(state="normal")
            self._set_status("Done!", "green")
            self._show_success(f"Signed PDF saved to:\n{result}")

        def error(e):
            self.pb.set(0)
            self._action_btn.configure(state="normal")
            self._set_status("Error!", "red")
            self._show_error(e)

        self._run_in_thread(work, done, error)
