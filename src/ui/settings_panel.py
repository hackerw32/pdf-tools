"""Settings panel."""
import os
from tkinter import filedialog
import customtkinter as ctk
from src.core.config import save_settings


class SettingsPanel(ctk.CTkFrame):

    def __init__(self, master, settings: dict, on_settings_changed=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.settings = settings
        self._on_changed = on_settings_changed
        self._build()

    def _build(self):
        # Header
        ctk.CTkLabel(self, text="Settings", font=("Arial", 22, "bold")).pack(anchor="w", padx=24, pady=(20, 4))
        ctk.CTkFrame(self, height=1, fg_color=("gray80", "gray30")).pack(fill="x", padx=24, pady=(0, 12))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24)

        # Appearance
        self._section(scroll, "Appearance")

        theme_row = self._row(scroll, "Theme")
        self.theme_var = ctk.StringVar(value=self.settings.get("theme", "dark").capitalize())
        ctk.CTkOptionMenu(theme_row, variable=self.theme_var,
                           values=["Dark", "Light", "System"],
                           width=130,
                           command=self._apply_theme).pack(side="right")

        color_row = self._row(scroll, "Accent color")
        self.color_var = ctk.StringVar(value=self.settings.get("color_theme", "blue").capitalize())
        ctk.CTkOptionMenu(color_row, variable=self.color_var,
                           values=["Blue", "Green", "Dark-blue"],
                           width=130,
                           command=self._apply_color).pack(side="right")

        self._section(scroll, "Default Output")

        out_row = self._row(scroll, "Default output folder")
        self.out_dir_var = ctk.StringVar(value=self.settings.get("default_output_dir", "") or "Same as input")
        ctk.CTkEntry(out_row, textvariable=self.out_dir_var, width=200).pack(side="right", padx=(0, 6))
        ctk.CTkButton(out_row, text="Browse", width=70,
                       command=self._pick_outdir).pack(side="right")

        self._section(scroll, "Compression Defaults")

        q_row = self._row(scroll, "Default image quality")
        self.quality_val = ctk.CTkLabel(q_row, text=f"{self.settings.get('compression_quality', 75)}%",
                                         font=("Arial", 12, "bold"), width=45)
        self.quality_val.pack(side="right")
        self.quality_slider = ctk.CTkSlider(scroll, from_=10, to=95, number_of_steps=17,
                                             command=self._update_quality)
        self.quality_slider.set(self.settings.get("compression_quality", 75))
        self.quality_slider.pack(fill="x", pady=(0, 12))

        self._section(scroll, "PDF to Images")

        dpi_row = self._row(scroll, "Default DPI for image export")
        self.dpi_val = ctk.CTkLabel(dpi_row, text=f"{self.settings.get('image_dpi', 150)} DPI",
                                     font=("Arial", 12, "bold"), width=65)
        self.dpi_val.pack(side="right")
        self.dpi_slider = ctk.CTkSlider(scroll, from_=72, to=300, number_of_steps=15,
                                         command=self._update_dpi)
        self.dpi_slider.set(self.settings.get("image_dpi", 150))
        self.dpi_slider.pack(fill="x", pady=(0, 12))

        self._section(scroll, "Signature")

        color_sig_row = self._row(scroll, "Default pen color")
        self.sig_color_var = ctk.StringVar(value=self.settings.get("signature_color", "#000000"))
        self.sig_color_btn = ctk.CTkButton(color_sig_row, text="  ■  ", width=50, height=28,
                                            fg_color=self.sig_color_var.get(),
                                            command=self._pick_sig_color)
        self.sig_color_btn.pack(side="right")

        pen_row = self._row(scroll, "Default pen size")
        self.pen_size_var = ctk.StringVar(value=str(self.settings.get("signature_pen_size", 2)))
        ctk.CTkOptionMenu(pen_row, variable=self.pen_size_var,
                           values=["1", "2", "3", "4", "5"], width=80).pack(side="right")

        self._section(scroll, "Recent Files")

        max_row = self._row(scroll, "Max recent files")
        self.max_recent_var = ctk.StringVar(value=str(self.settings.get("max_recent_files", 10)))
        ctk.CTkOptionMenu(max_row, variable=self.max_recent_var,
                           values=["5", "10", "15", "20"], width=80).pack(side="right")

        ctk.CTkButton(scroll, text="Clear Recent Files", height=32, width=160,
                       fg_color=("gray80", "gray30"),
                       hover_color=("#c0392b", "#e74c3c"),
                       text_color=("gray10", "gray90"),
                       command=self._clear_recent).pack(anchor="w", pady=8)

        # Save button
        ctk.CTkFrame(scroll, height=1, fg_color=("gray80", "gray30")).pack(fill="x", pady=16)
        ctk.CTkButton(scroll, text="💾  Save Settings", height=42,
                       font=("Arial", 13, "bold"),
                       command=self._save).pack(fill="x")

    def _section(self, parent, title):
        ctk.CTkLabel(parent, text=title, font=("Arial", 13, "bold"),
                     text_color=("gray30", "gray80")).pack(anchor="w", pady=(12, 4))

    def _row(self, parent, label):
        row = ctk.CTkFrame(parent, fg_color=("gray92", "gray18"), corner_radius=8, height=44)
        row.pack(fill="x", pady=3)
        row.pack_propagate(False)
        ctk.CTkLabel(row, text=label, font=("Arial", 12)).pack(side="left", padx=14)
        return row

    def _update_quality(self, val):
        self.quality_val.configure(text=f"{int(val)}%")

    def _update_dpi(self, val):
        self.dpi_val.configure(text=f"{int(val)} DPI")

    def _pick_outdir(self):
        d = filedialog.askdirectory()
        if d:
            self.out_dir_var.set(d)

    def _pick_sig_color(self):
        try:
            from tkinter import colorchooser
            color = colorchooser.askcolor(color=self.sig_color_var.get())[1]
            if color:
                self.sig_color_var.set(color)
                self.sig_color_btn.configure(fg_color=color)
        except Exception:
            pass

    def _apply_theme(self, val):
        ctk.set_appearance_mode(val.lower())

    def _apply_color(self, val):
        # customtkinter needs restart for color theme changes; inform user
        pass

    def _clear_recent(self):
        self.settings["recent_files"] = []
        save_settings(self.settings)
        if self._on_changed:
            self._on_changed(self.settings)

    def _save(self):
        out_dir = self.out_dir_var.get()
        self.settings.update({
            "theme": self.theme_var.get().lower(),
            "color_theme": self.color_var.get().lower(),
            "compression_quality": int(self.quality_slider.get()),
            "image_dpi": int(self.dpi_slider.get()),
            "default_output_dir": "" if out_dir == "Same as input" else out_dir,
            "signature_color": self.sig_color_var.get(),
            "signature_pen_size": int(self.pen_size_var.get()),
            "max_recent_files": int(self.max_recent_var.get()),
        })
        save_settings(self.settings)
        if self._on_changed:
            self._on_changed(self.settings)
        from tkinter import messagebox
        messagebox.showinfo("Settings", "Settings saved successfully!")
