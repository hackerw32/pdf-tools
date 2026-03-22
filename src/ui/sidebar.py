"""Navigation sidebar."""
import customtkinter as ctk


TOOLS = [
    {
        "category": "Transform",
        "items": [
            {"id": "compress",         "icon": "🗜", "label": "Compress PDF"},
            {"id": "merge",            "icon": "🔗", "label": "Merge PDFs"},
            {"id": "split",            "icon": "✂", "label": "Split PDF"},
            {"id": "rearrange",        "icon": "↕", "label": "Rearrange Pages"},
            {"id": "rotate",           "icon": "↻", "label": "Rotate Pages"},
            {"id": "remove_dups",      "icon": "🔍", "label": "Remove Duplicates"},
        ],
    },
    {
        "category": "Convert",
        "items": [
            {"id": "images_to_pdf",    "icon": "🖼", "label": "Images → PDF"},
            {"id": "text_to_pdf",      "icon": "📝", "label": "Text → PDF"},
            {"id": "word_to_pdf",      "icon": "📄", "label": "Word/Excel → PDF"},
            {"id": "pdf_to_images",    "icon": "🖼", "label": "PDF → Images"},
            {"id": "pdf_to_text",      "icon": "📋", "label": "PDF → Text"},
        ],
    },
    {
        "category": "Edit",
        "items": [
            {"id": "image_editor",     "icon": "✏", "label": "Image Editor"},
            {"id": "sign_pdf",         "icon": "✍", "label": "Sign PDF"},
        ],
    },
]


class Sidebar(ctk.CTkFrame):

    def __init__(self, master, on_select, **kwargs):
        super().__init__(master, width=220, corner_radius=0,
                         fg_color=("gray88", "gray15"), **kwargs)
        self.pack_propagate(False)
        self._on_select = on_select
        self._buttons = {}
        self._active_id = None
        self._build()

    def _build(self):
        # App title
        title_frame = ctk.CTkFrame(self, fg_color="transparent", height=60)
        title_frame.pack(fill="x")
        title_frame.pack_propagate(False)
        ctk.CTkLabel(title_frame, text="PDF Tools",
                     font=("Arial", 18, "bold")).pack(side="left", padx=18, pady=16)

        ctk.CTkFrame(self, height=1, fg_color=("gray75", "gray30")).pack(fill="x", padx=10)

        # Scrollable nav
        nav = ctk.CTkScrollableFrame(self, fg_color="transparent")
        nav.pack(fill="both", expand=True, padx=6, pady=8)

        for section in TOOLS:
            ctk.CTkLabel(nav, text=section["category"].upper(),
                         font=("Arial", 9, "bold"),
                         text_color=("gray50", "gray55")).pack(anchor="w", padx=12, pady=(10, 2))

            for item in section["items"]:
                btn = ctk.CTkButton(
                    nav,
                    text=f'  {item["icon"]}  {item["label"]}',
                    anchor="w",
                    height=36,
                    corner_radius=8,
                    font=("Arial", 12),
                    fg_color="transparent",
                    hover_color=("gray78", "gray28"),
                    text_color=("gray15", "gray90"),
                    command=lambda i=item["id"]: self._select(i),
                )
                btn.pack(fill="x", pady=1)
                self._buttons[item["id"]] = btn

        # Divider + Settings at bottom
        ctk.CTkFrame(self, height=1, fg_color=("gray75", "gray30")).pack(fill="x", padx=10, pady=4)
        settings_btn = ctk.CTkButton(
            self,
            text="  ⚙  Settings",
            anchor="w",
            height=38,
            corner_radius=0,
            font=("Arial", 12),
            fg_color="transparent",
            hover_color=("gray78", "gray28"),
            text_color=("gray15", "gray90"),
            command=lambda: self._select("settings"),
        )
        settings_btn.pack(fill="x", padx=6, pady=(0, 8))
        self._buttons["settings"] = settings_btn

    def _select(self, tool_id: str):
        # Reset previous
        if self._active_id and self._active_id in self._buttons:
            self._buttons[self._active_id].configure(fg_color="transparent")
        # Highlight new
        self._active_id = tool_id
        if tool_id in self._buttons:
            self._buttons[tool_id].configure(
                fg_color=("gray75", "gray32")
            )
        self._on_select(tool_id)

    def select(self, tool_id: str):
        self._select(tool_id)
