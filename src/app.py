"""Main application window."""
import customtkinter as ctk
from src.core.config import load_settings, save_settings
from src.ui.sidebar import Sidebar
from src.ui.settings_panel import SettingsPanel

# Lazy imports - load tool panels on demand
_TOOL_MAP = {
    "compress":      ("src.ui.tools.compress",        "CompressTool"),
    "merge":         ("src.ui.tools.merge",           "MergeTool"),
    "split":         ("src.ui.tools.split",           "SplitTool"),
    "rearrange":     ("src.ui.tools.rearrange",       "RearrangeTool"),
    "rotate":        ("src.ui.tools.rotate",          "RotateTool"),
    "remove_dups":   ("src.ui.tools.remove_duplicates", "RemoveDuplicatesTool"),
    "images_to_pdf": ("src.ui.tools.images_to_pdf",   "ImagesToPdfTool"),
    "text_to_pdf":   ("src.ui.tools.text_to_pdf",     "TextToPdfTool"),
    "word_to_pdf":   ("src.ui.tools.word_to_pdf",     "WordToPdfTool"),
    "pdf_to_images": ("src.ui.tools.pdf_to_images",   "PdfToImagesTool"),
    "pdf_to_text":   ("src.ui.tools.pdf_to_text",     "PdfToTextTool"),
    "image_editor":  ("src.ui.tools.image_editor",    "ImageEditorTool"),
    "sign_pdf":      ("src.ui.tools.sign_pdf",        "SignPdfTool"),
}


def _load_tool_class(module_path: str, class_name: str):
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, class_name)


class PDFToolsApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.settings = load_settings()

        ctk.set_appearance_mode(self.settings.get("theme", "dark"))
        ctk.set_default_color_theme(self.settings.get("color_theme", "blue"))

        self.title("PDF Tools")
        self.geometry("1100x720")
        self.minsize(800, 560)

        self._panel_cache = {}
        self._current_panel = None

        self._build_layout()
        # Select first tool by default
        self.sidebar.select("compress")

    def _build_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(self, on_select=self._show_panel)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.content = ctk.CTkFrame(self, fg_color=("gray96", "gray13"), corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

    def _show_panel(self, tool_id: str):
        if self._current_panel:
            self._current_panel.grid_remove()

        if tool_id not in self._panel_cache:
            panel = self._build_panel(tool_id)
            if panel is None:
                return
            panel.grid(row=0, column=0, sticky="nsew", in_=self.content)
            self._panel_cache[tool_id] = panel
        else:
            self._panel_cache[tool_id].grid()

        self._current_panel = self._panel_cache[tool_id]

    def _build_panel(self, tool_id: str):
        if tool_id == "settings":
            return SettingsPanel(self.content, self.settings,
                                  on_settings_changed=self._on_settings_changed)

        if tool_id not in _TOOL_MAP:
            return None

        module_path, class_name = _TOOL_MAP[tool_id]
        try:
            cls = _load_tool_class(module_path, class_name)
            return cls(self.content, self.settings)
        except Exception as e:
            frame = ctk.CTkFrame(self.content, fg_color="transparent")
            ctk.CTkLabel(frame, text=f"Error loading tool:\n{e}",
                         font=("Arial", 13),
                         text_color="red").pack(expand=True)
            return frame

    def _on_settings_changed(self, new_settings):
        self.settings = new_settings
        save_settings(new_settings)
        # Clear panel cache so tools pick up new settings
        self._panel_cache.clear()
        self._current_panel = None
        self.sidebar.select("settings")
