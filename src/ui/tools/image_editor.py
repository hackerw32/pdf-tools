"""Image editor - edit images before adding to PDF."""
import os
import tempfile
from tkinter import filedialog
import customtkinter as ctk
from PIL import Image, ImageTk
from src.ui.base_tool import BaseTool, DropZone
from src.core import pdf_ops


class ImageEditorTool(BaseTool):
    TITLE = "Image Editor"
    DESCRIPTION = "Edit images (brightness, contrast, rotate) before converting to PDF"

    SUPPORTED = [("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.webp")]

    def build_ui(self):
        self._current_image = None
        self._edited_images = {}
        self._preview_tk = None

        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=24)

        left = ctk.CTkScrollableFrame(main, width=320, fg_color="transparent")
        left.pack(side="left", fill="y", padx=(0, 12))

        self.drop = DropZone(left, label="Drop images here\nor click to browse",
                             multiple=True, filetypes=self.SUPPORTED)
        self.drop.configure(height=140)
        self.drop.pack(fill="x", pady=(0, 10))
        self.drop.on_files_changed = self._load_images

        # File list
        list_frame = ctk.CTkFrame(left, corner_radius=10, fg_color=("gray92", "gray18"))
        list_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(list_frame, text="Images:", font=("Arial", 12, "bold")).pack(anchor="w", padx=12, pady=(8, 4))
        self.file_list = ctk.CTkScrollableFrame(list_frame, height=130, fg_color=("gray88", "gray22"))
        self.file_list.pack(fill="x", padx=8, pady=(0, 8))

        # Controls
        ctrl = ctk.CTkFrame(left, corner_radius=10, fg_color=("gray92", "gray18"))
        ctrl.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(ctrl, text="Adjustments", font=("Arial", 12, "bold")).pack(anchor="w", padx=12, pady=(8, 4))

        for label, attr, default in [
            ("Brightness", "brightness", 1.0),
            ("Contrast", "contrast", 1.0),
            ("Sharpness", "sharpness", 1.0),
        ]:
            row = ctk.CTkFrame(ctrl, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=2)
            ctk.CTkLabel(row, text=label, width=80, font=("Arial", 11)).pack(side="left")
            val_label = ctk.CTkLabel(row, text=f"{default:.1f}", width=35, font=("Arial", 11, "bold"))
            val_label.pack(side="right")
            slider = ctk.CTkSlider(row, from_=0.2, to=3.0, number_of_steps=28)
            slider.set(default)
            slider.pack(side="left", fill="x", expand=True, padx=4)
            slider.configure(command=lambda v, lbl=val_label, a=attr: self._slider_changed(v, lbl, a))
            setattr(self, f"slider_{attr}", slider)

        # Rotation
        rot_row = ctk.CTkFrame(ctrl, fg_color="transparent")
        rot_row.pack(fill="x", padx=12, pady=(4, 2))
        ctk.CTkLabel(rot_row, text="Rotate:", width=80, font=("Arial", 11)).pack(side="left")
        self.rotation_var = ctk.StringVar(value="0")
        for angle in ["0", "90", "180", "270"]:
            ctk.CTkRadioButton(rot_row, text=f"{angle}°", variable=self.rotation_var,
                               value=angle, width=50, font=("Arial", 10)).pack(side="left")

        # Grayscale
        self.grayscale_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(ctrl, text="Convert to Grayscale",
                         variable=self.grayscale_var).pack(anchor="w", padx=12, pady=(4, 8))

        btn_row = ctk.CTkFrame(left, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 6))
        ctk.CTkButton(btn_row, text="👁 Preview", height=36,
                       command=self._preview).pack(side="left", padx=(0, 6), fill="x", expand=True)
        ctk.CTkButton(btn_row, text="✓ Apply to Selected", height=36,
                       command=self._apply_to_selected).pack(side="left", fill="x", expand=True)

        out_row = ctk.CTkFrame(left, fg_color="transparent")
        out_row.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(out_row, text="Output dir:", font=("Arial", 11)).pack(side="left")
        self.out_dir_var = ctk.StringVar(value="Same as input")
        ctk.CTkEntry(out_row, textvariable=self.out_dir_var, width=160).pack(side="left", padx=6)
        ctk.CTkButton(out_row, text="...", width=36,
                       command=self._pick_outdir).pack(side="left")

        ctk.CTkButton(left, text="💾  Save Edited Images", height=38,
                       command=self._save_all).pack(fill="x", pady=(4, 0))

        # Preview pane
        right = ctk.CTkFrame(main, corner_radius=10, fg_color=("gray90", "gray20"))
        right.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(right, text="Preview", font=("Arial", 12, "bold")).pack(pady=(12, 4))
        self.preview_canvas = ctk.CTkLabel(right, text="Select an image to preview",
                                            font=("Arial", 12),
                                            text_color=("gray50", "gray60"))
        self.preview_canvas.pack(expand=True)

        self._file_list_items = []
        self._selected_file = None

    def _slider_changed(self, val, label, attr):
        label.configure(text=f"{float(val):.1f}")

    def _load_images(self, files):
        self._file_list_items = list(files)
        self._render_file_list()

    def _render_file_list(self):
        for w in self.file_list.winfo_children():
            w.destroy()
        for f in self._file_list_items:
            name = os.path.basename(f)
            edited = f in self._edited_images
            row = ctk.CTkFrame(self.file_list, corner_radius=5,
                               fg_color=("gray83", "gray28"), height=30)
            row.pack(fill="x", pady=2, padx=2)
            row.pack_propagate(False)
            indicator = "✓ " if edited else "  "
            lbl = ctk.CTkLabel(row, text=f"{indicator}{name}", font=("Arial", 10), anchor="w")
            lbl.pack(side="left", padx=6, fill="x", expand=True)
            row.bind("<Button-1>", lambda e, path=f: self._select_file(path))
            lbl.bind("<Button-1>", lambda e, path=f: self._select_file(path))

    def _select_file(self, path):
        self._selected_file = path

    def _get_params(self):
        return {
            "brightness": float(self.slider_brightness.get()),
            "contrast": float(self.slider_contrast.get()),
            "sharpness": float(self.slider_sharpness.get()),
            "rotation": int(self.rotation_var.get()),
            "grayscale": self.grayscale_var.get(),
        }

    def _preview(self):
        path = self._selected_file or (self._file_list_items[0] if self._file_list_items else None)
        if not path:
            return
        params = self._get_params()

        def work():
            tmp = tempfile.mktemp(suffix=".png")
            pdf_ops.edit_image(path, tmp, **params)
            img = Image.open(tmp)
            # Fit to preview area
            img.thumbnail((420, 420))
            return img, tmp

        def done(res):
            img, tmp = res
            self._preview_tk = ImageTk.PhotoImage(img)
            self.preview_canvas.configure(image=self._preview_tk, text="")
            try:
                os.remove(tmp)
            except Exception:
                pass

        self._run_in_thread(work, done)

    def _apply_to_selected(self):
        if not self._selected_file:
            self._show_error("Select a file from the list first.")
            return
        params = self._get_params()
        self._edited_images[self._selected_file] = params
        self._render_file_list()

    def _pick_outdir(self):
        d = filedialog.askdirectory()
        if d:
            self.out_dir_var.set(d)

    def _save_all(self):
        if not self._file_list_items:
            self._show_error("No images loaded.")
            return

        out_base = self.out_dir_var.get()

        def work():
            outputs = []
            for f in self._file_list_items:
                params = self._edited_images.get(f, {
                    "brightness": 1.0, "contrast": 1.0,
                    "sharpness": 1.0, "rotation": 0, "grayscale": False
                })
                out_dir = out_base if out_base != "Same as input" else os.path.dirname(f)
                stem, ext = os.path.splitext(os.path.basename(f))
                out_path = os.path.join(out_dir, f"{stem}_edited{ext}")
                pdf_ops.edit_image(f, out_path, **params)
                outputs.append(out_path)
            return outputs

        def done(outputs):
            self._show_success(f"Saved {len(outputs)} edited image(s).")

        self._run_in_thread(work, done)
