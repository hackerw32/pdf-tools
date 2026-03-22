"""Page rearrange tool with thumbnail drag & drop."""
import os
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from PIL import ImageTk
from src.ui.base_tool import BaseTool, DropZone
from src.core import pdf_ops


class PageThumb(ctk.CTkFrame):
    """A draggable page thumbnail widget."""

    def __init__(self, master, page_idx, img, original_idx, on_drag_start, on_drag_end, **kwargs):
        super().__init__(master, corner_radius=8,
                         fg_color=("gray88", "gray25"),
                         border_width=2, border_color=("gray70", "gray40"),
                         width=110, height=160, **kwargs)
        self.pack_propagate(False)
        self.page_idx = page_idx
        self.original_idx = original_idx
        self._on_drag_start = on_drag_start
        self._on_drag_end = on_drag_end

        self._img = ImageTk.PhotoImage(img)
        img_label = tk.Label(self, image=self._img, bg=self._fg_color[1] if ctk.get_appearance_mode() == "Dark" else self._fg_color[0])
        img_label.pack(pady=(8, 2))

        self.num_label = ctk.CTkLabel(self, text=f"Page {page_idx + 1}",
                                       font=("Arial", 10))
        self.num_label.pack(pady=(0, 6))

        for w in (self, img_label, self.num_label):
            w.bind("<ButtonPress-1>", self._drag_start)
            w.bind("<B1-Motion>", self._drag_motion)
            w.bind("<ButtonRelease-1>", self._drag_release)

        self._drag_x = 0
        self._drag_y = 0

    def _drag_start(self, event):
        self._drag_x = event.x_root
        self._drag_y = event.y_root
        self.configure(border_color=("#3498db", "#2980b9"))
        self._on_drag_start(self)

    def _drag_motion(self, event):
        pass  # Visual handled by parent

    def _drag_release(self, event):
        self.configure(border_color=("gray70", "gray40"))
        self._on_drag_end(self, event.x_root, event.y_root)

    def set_selected(self, selected: bool):
        if selected:
            self.configure(border_color=("#3498db", "#2980b9"))
        else:
            self.configure(border_color=("gray70", "gray40"))


class RearrangeTool(BaseTool):
    TITLE = "Rearrange Pages"
    DESCRIPTION = "Reorder, delete or duplicate pages with drag & drop"

    def build_ui(self):
        self._thumbs = []
        self._order = []
        self._dragging = None

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(0, 8))

        self.drop = DropZone(top, label="Drop a PDF here\nor click to browse",
                             multiple=False, filetypes=[("PDF files", "*.pdf")])
        self.drop.configure(height=140)
        self.drop.pack(fill="x")
        self.drop.on_files_changed = self._load_pdf

        self.info_label = ctk.CTkLabel(self, text="Load a PDF to see page thumbnails",
                                        font=("Arial", 12),
                                        text_color=("gray40", "gray60"))
        self.info_label.pack(pady=(4, 0))

        # Toolbar
        toolbar = ctk.CTkFrame(self, fg_color=("gray92", "gray18"), corner_radius=8)
        toolbar.pack(fill="x", padx=24, pady=8)

        for text, cmd in [
            ("↑ Move Left", self._move_selected_left),
            ("↓ Move Right", self._move_selected_right),
            ("🗑 Remove", self._remove_selected),
            ("↻ Rotate 90°", self._rotate_selected),
        ]:
            ctk.CTkButton(toolbar, text=text, height=32, width=120,
                           fg_color=("gray80", "gray30"),
                           hover_color=("gray70", "gray40"),
                           text_color=("gray10", "gray90"),
                           font=("Arial", 11),
                           command=cmd).pack(side="left", padx=6, pady=6)

        ctk.CTkButton(toolbar, text="Select All", height=32, width=90,
                       fg_color=("gray80", "gray30"),
                       hover_color=("gray70", "gray40"),
                       text_color=("gray10", "gray90"),
                       font=("Arial", 11),
                       command=self._select_all).pack(side="left", padx=6, pady=6)

        ctk.CTkButton(toolbar, text="Clear Selection", height=32, width=110,
                       fg_color=("gray80", "gray30"),
                       hover_color=("gray70", "gray40"),
                       text_color=("gray10", "gray90"),
                       font=("Arial", 11),
                       command=self._clear_selection).pack(side="left", padx=6, pady=6)

        # Page grid
        self.canvas_container = ctk.CTkScrollableFrame(self, fg_color=("gray90", "gray20"),
                                                        corner_radius=8, orientation="horizontal")
        self.canvas_container.pack(fill="both", expand=True, padx=24, pady=(0, 8))

        # Output + action
        out_row = ctk.CTkFrame(self, fg_color="transparent")
        out_row.pack(fill="x", padx=24, pady=(0, 4))
        ctk.CTkLabel(out_row, text="Output file:", font=("Arial", 12)).pack(side="left")
        self.out_var = ctk.StringVar(value="")
        ctk.CTkEntry(out_row, textvariable=self.out_var, width=300).pack(side="left", padx=8)
        ctk.CTkButton(out_row, text="Browse", width=80,
                       command=self._pick_out).pack(side="left")

        self._action_btn = self._make_action_row(self, "💾  Save Rearranged PDF", self._run)
        self._action_btn.pack_configure(padx=24)
        self.pb = self._make_progress(self)
        self.pb.pack_configure(padx=24)

        self._selected = set()

    def _pick_out(self):
        path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                             filetypes=[("PDF files", "*.pdf")])
        if path:
            self.out_var.set(path)

    def _load_pdf(self, files):
        if not files:
            return
        self._input_path = files[0]
        self.out_var.set(self._make_output_path(self._input_path, "_rearranged"))
        self.info_label.configure(text="Loading thumbnails...")

        def work():
            thumbs = pdf_ops.get_pdf_page_thumbnails(self._input_path, dpi=72)
            return thumbs

        def done(thumbs):
            self._raw_thumbs = thumbs
            self._order = list(range(len(thumbs)))
            self._rotations = [0] * len(thumbs)
            self._render_thumbs()
            info = pdf_ops.get_pdf_info(self._input_path)
            self.info_label.configure(text=f"📄 {info['pages']} pages  |  Click to select, drag to reorder")

        self._run_in_thread(work, done)

    def _thumb_size(self, img):
        w, h = img.size
        scale = 100 / max(w, h)
        return img.resize((int(w * scale), int(h * scale)))

    def _render_thumbs(self):
        for w in self.canvas_container.winfo_children():
            w.destroy()
        self._thumbs = []
        self._selected = set()

        for display_pos, orig_idx in enumerate(self._order):
            img = self._thumb_size(self._raw_thumbs[orig_idx])
            rot = self._rotations[orig_idx]
            if rot:
                img = img.rotate(-rot, expand=True)
                img = self._thumb_size(img)

            thumb = PageThumb(
                self.canvas_container,
                page_idx=display_pos,
                img=img,
                original_idx=orig_idx,
                on_drag_start=self._on_drag_start,
                on_drag_end=self._on_drag_end,
            )
            thumb.pack(side="left", padx=6, pady=8)
            thumb.bind("<Button-1>", lambda e, pos=display_pos: self._toggle_select(pos), add="+")
            self._thumbs.append(thumb)

    def _toggle_select(self, pos):
        if pos in self._selected:
            self._selected.discard(pos)
            self._thumbs[pos].set_selected(False)
        else:
            self._selected.add(pos)
            self._thumbs[pos].set_selected(True)

    def _select_all(self):
        self._selected = set(range(len(self._order)))
        for t in self._thumbs:
            t.set_selected(True)

    def _clear_selection(self):
        self._selected = set()
        for t in self._thumbs:
            t.set_selected(False)

    def _on_drag_start(self, thumb):
        self._dragging = thumb.page_idx

    def _on_drag_end(self, thumb, x_root, y_root):
        if self._dragging is None:
            return
        # Find target position based on cursor x
        target = self._dragging
        container = self.canvas_container
        rel_x = x_root - container.winfo_rootx()

        for i, t in enumerate(self._thumbs):
            tx = t.winfo_x() + t.winfo_width() // 2
            if rel_x < tx:
                target = i
                break
        else:
            target = len(self._thumbs) - 1

        src = self._dragging
        if src != target:
            item = self._order.pop(src)
            self._order.insert(target, item)
            self._render_thumbs()
        self._dragging = None

    def _move_selected_left(self):
        for pos in sorted(self._selected):
            if pos > 0:
                self._order[pos], self._order[pos - 1] = self._order[pos - 1], self._order[pos]
        self._render_thumbs()

    def _move_selected_right(self):
        for pos in sorted(self._selected, reverse=True):
            if pos < len(self._order) - 1:
                self._order[pos], self._order[pos + 1] = self._order[pos + 1], self._order[pos]
        self._render_thumbs()

    def _remove_selected(self):
        self._order = [o for i, o in enumerate(self._order) if i not in self._selected]
        self._selected = set()
        self._render_thumbs()

    def _rotate_selected(self):
        for pos in self._selected:
            orig = self._order[pos]
            self._rotations[orig] = (self._rotations[orig] + 90) % 360
        self._render_thumbs()

    def _run(self):
        if not hasattr(self, "_input_path") or not self._order:
            self._show_error("Please load a PDF first.")
            return

        out = self.out_var.get()
        if not out:
            self._show_error("Please specify an output file path.")
            return

        self.pb.set(0)
        self._set_status("Saving...", "orange")
        self._action_btn.configure(state="disabled")

        order = list(self._order)
        rotations = dict(self._rotations)
        input_path = self._input_path

        def work():
            # First rearrange
            temp = out + ".tmp.pdf"
            pdf_ops.rearrange_pages(input_path, temp, order)
            # Apply rotations (rotation indices are now positional in new order)
            page_rots = {}
            for new_pos, orig in enumerate(order):
                rot = rotations.get(orig, 0)
                if rot:
                    page_rots[new_pos] = rot
            if page_rots:
                pdf_ops.rotate_pages(temp, out, page_rots)
                os.remove(temp)
            else:
                os.rename(temp, out)
            return out

        def done(result):
            self.pb.set(1)
            self._action_btn.configure(state="normal")
            self._set_status("Done!", "green")
            self._show_success(f"Saved to:\n{result}")

        def error(e):
            self.pb.set(0)
            self._action_btn.configure(state="normal")
            self._set_status("Error!", "red")
            self._show_error(e)

        self._run_in_thread(work, done, error)
