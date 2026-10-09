"""Floaty - Floating note bubble with tabs & Home Dashboard view (Windows).

- Round glowing bubble that stays on top of every app. Drag it anywhere.
- Click it (without dragging) to open the notes panel with smooth ease animations.
- Home Screen Grid: Thumbnail cards for all saved notes + "+" blank note card.
- Editor View: Tabbed text editing with line snippet previews & word count.
- In-App Modal Dialogs: Rename & Delete dialogs rendered directly inside the panel (100% bug-free).
- Double-click any tab OR right-click -> "Rename tab" to rename it cleanly.

Shortcuts (inside the panel):
  Ctrl+N  new tab         Ctrl+W  delete tab (asks first)
  Ctrl+S  save all        Ctrl+Shift+S  Save As... (export this tab anywhere)
  Ctrl+T  insert timestamp (time since you launched the app)
  Double-click tab        rename tab
Right-click the bubble, header or a tab for the full menu.

Run:  python floaty.py
"""
import math
import re
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

# ---------------- CONFIGURATION & THEME ----------------
NOTES_DIR = Path(__file__).with_name("notes")
NOTES_DIR.mkdir(exist_ok=True)
START = time.time()

BUBBLE = 68
TRANSPARENT = "#010101"      # Windows see-through color key
BG = "#0f172a"               # Deep obsidian dark background
HEADER_BG = "#1e293b"        # Slate dark header bar
CARD_BG = "#1e293b"          # Card background
CARD_HOVER = "#334155"       # Card hover background
ACCENT = "#8b5cf6"           # Electric purple accent
ACCENT_HOVER = "#a78bfa"     # Light purple hover
ACCENT_CYAN = "#06b6d4"      # Cyan secondary accent
TEXT_MAIN = "#f8fafc"        # Bright text
TEXT_MUTED = "#94a3b8"       # Muted text
BORDER_COLOR = "#334155"     # Border divider

size = {"w": 460, "h": 520}  # Panel target size
tabs = []                    # List of dicts: {"frame": Frame, "text": Text, "path": Path}
animating = False            # Animation lock flag
current_view = "editor"      # "home" or "editor"

root = tk.Tk()
root.title("Floaty")
root.overrideredirect(True)
root.attributes("-topmost", True)
root.configure(bg=TRANSPARENT)
root.attributes("-transparentcolor", TRANSPARENT)
root.geometry(f"{BUBBLE}x{BUBBLE}+120+120")

# ---------------- BUBBLE WIDGET ----------------
bubble = tk.Canvas(root, width=BUBBLE, height=BUBBLE, bg=TRANSPARENT,
                   highlightthickness=0, cursor="hand2")

def draw_bubble(badge_count=0):
    bubble.delete("all")
    # Outer glow ring
    bubble.create_oval(2, 2, BUBBLE - 2, BUBBLE - 2, fill=HEADER_BG, outline=ACCENT_HOVER, width=2)
    # Inner gradient fill
    bubble.create_oval(6, 6, BUBBLE - 6, BUBBLE - 6, fill=ACCENT, outline="#ffffff", width=1.5)
    # Center note icon
    bubble.create_text(BUBBLE // 2, BUBBLE // 2, text="\u270e", fill="white",
                       font=("Segoe UI Symbol", 24, "bold"))
    # Badge count overlay
    if badge_count > 0:
        bubble.create_oval(BUBBLE - 22, 2, BUBBLE - 2, 22, fill="#ec4899", outline="#ffffff", width=1.5)
        bubble.create_text(BUBBLE - 12, 12, text=str(badge_count), fill="white",
                           font=("Segoe UI", 9, "bold"))

draw_bubble(0)
bubble.pack()

# ---------------- MAIN PANEL ----------------
panel = tk.Frame(root, bg=BG, highlightthickness=1, highlightbackground=ACCENT)

# --- Header Bar ---
header = tk.Frame(panel, bg=HEADER_BG, height=38, cursor="fleur")
header.pack(fill="x")

title_icon = tk.Label(header, text="✦", bg=HEADER_BG, fg=ACCENT_CYAN, font=("Segoe UI Symbol", 12))
title_icon.pack(side="left", padx=(10, 2))

title = tk.Label(header, text="Floaty", bg=HEADER_BG, fg=TEXT_MAIN,
                 font=("Segoe UI", 10, "bold"))
title.pack(side="left")

# --- View Switcher Buttons (Home vs Editor) ---
view_frame = tk.Frame(header, bg=HEADER_BG)
view_frame.pack(side="left", padx=12)

btn_view_home = tk.Label(view_frame, text=" 🏠 Home ", bg=HEADER_BG, fg=TEXT_MUTED,
                         font=("Segoe UI", 9, "bold"), cursor="hand2", padx=6, pady=2)
btn_view_home.pack(side="left")

btn_view_editor = tk.Label(view_frame, text=" ✎ Editor ", bg=ACCENT, fg="#ffffff",
                           font=("Segoe UI", 9, "bold"), cursor="hand2", padx=6, pady=2)
btn_view_editor.pack(side="left", padx=4)

# Window action buttons
def make_header_btn(text, fg_color, bg_hover, cmd):
    btn = tk.Label(header, text=text, bg=HEADER_BG, fg=fg_color,
                   font=("Segoe UI", 11, "bold"), cursor="hand2", padx=10, pady=4)
    btn.bind("<Enter>", lambda e: btn.configure(bg=bg_hover))
    btn.bind("<Leave>", lambda e: btn.configure(bg=HEADER_BG))
    btn.bind("<Button-1>", lambda e: cmd())
    btn.pack(side="right")
    return btn

btn_close = make_header_btn(" ✕ ", "#ef4444", "#450a0a", lambda: quit_app())
btn_collapse = make_header_btn("  –  ", TEXT_MAIN, "#334155", lambda: collapse())
btn_new = make_header_btn("  +  ", ACCENT_HOVER, "#334155", lambda: new_tab())

# --- Content Container ---
content_container = tk.Frame(panel, bg=BG)
content_container.pack(fill="both", expand=True)

# ---------------- HOME DASHBOARD VIEW ----------------
home_frame = tk.Frame(content_container, bg=BG)

home_canvas = tk.Canvas(home_frame, bg=BG, highlightthickness=0)
home_scrollbar = ttk.Scrollbar(home_frame, orient="vertical", command=home_canvas.yview)
home_grid = tk.Frame(home_canvas, bg=BG)

home_grid.bind("<Configure>", lambda e: home_canvas.configure(scrollregion=home_canvas.bbox("all")))
home_canvas.create_window((0, 0), window=home_grid, anchor="nw")
home_canvas.configure(yscrollcommand=home_scrollbar.set)

home_canvas.pack(side="left", fill="both", expand=True, padx=12, pady=12)
home_scrollbar.pack(side="right", fill="y")


def render_home_screen():
    for child in home_grid.winfo_children():
        child.destroy()

    cols = 2
    row = 0
    col = 0

    # 1. Blank Notebook / New Note Card
    card_new = tk.Frame(home_grid, bg="#1e293b", highlightthickness=1.5,
                        highlightbackground=ACCENT, width=195, height=130, cursor="hand2")
    card_new.pack_propagate(False)
    card_new.grid(row=row, column=col, padx=8, pady=8)

    lbl_plus = tk.Label(card_new, text="+", bg="#1e293b", fg=ACCENT_HOVER, font=("Segoe UI", 32, "bold"))
    lbl_plus.pack(expand=True)
    lbl_new_txt = tk.Label(card_new, text="New Notebook Note", bg="#1e293b", fg=TEXT_MAIN, font=("Segoe UI", 9, "bold"))
    lbl_new_txt.pack(pady=(0, 14))

    def on_click_new(_e=None):
        new_tab()
        switch_view("editor")

    for w in (card_new, lbl_plus, lbl_new_txt):
        w.bind("<Button-1>", on_click_new)
        w.bind("<Enter>", lambda e: card_new.configure(bg="#334155", highlightbackground=ACCENT_HOVER))
        w.bind("<Leave>", lambda e: card_new.configure(bg="#1e293b", highlightbackground=ACCENT))

    col += 1

    # 2. Existing Saved Notes Cards
    for tab_info in tabs:
        path = tab_info["path"]
        title_text = path.stem
        content_text = tab_info["text"].get("1.0", "end-1c").strip()
        snippet = (content_text[:60] + "...") if len(content_text) > 60 else (content_text or "Empty note...")
        words_count = len(content_text.split()) if content_text else 0

        card = tk.Frame(home_grid, bg="#1e293b", highlightthickness=1,
                        highlightbackground=BORDER_COLOR, width=195, height=130, cursor="hand2")
        card.pack_propagate(False)
        card.grid(row=row, column=col, padx=8, pady=8)

        c_head = tk.Frame(card, bg="#1e293b")
        c_head.pack(fill="x", padx=10, pady=(10, 4))

        icon_lbl = tk.Label(c_head, text="📄", bg="#1e293b", fg=ACCENT_CYAN, font=("Segoe UI Symbol", 11))
        icon_lbl.pack(side="left")

        t_lbl = tk.Label(c_head, text=title_text, bg="#1e293b", fg=TEXT_MAIN,
                         font=("Segoe UI", 9, "bold"), anchor="w")
        t_lbl.pack(side="left", fill="x", expand=True, padx=4)

        snip_lbl = tk.Label(card, text=snippet, bg="#1e293b", fg=TEXT_MUTED,
                            font=("Segoe UI", 8), justify="left", wraplength=170, anchor="nw")
        snip_lbl.pack(fill="both", expand=True, padx=10)

        c_foot = tk.Frame(card, bg="#1e293b")
        c_foot.pack(fill="x", padx=10, pady=(0, 8))

        w_lbl = tk.Label(c_foot, text=f"{words_count} words", bg="#1e293b", fg="#64748b", font=("Segoe UI", 7, "bold"))
        w_lbl.pack(side="right")

        def make_open_handler(t_info):
            def handler(_e=None):
                nb.select(t_info["frame"])
                switch_view("editor")
            return handler

        h_func = make_open_handler(tab_info)

        def make_hover_handlers(c_elem):
            def on_e(_e): c_elem.configure(bg="#334155", highlightbackground=ACCENT)
            def on_l(_e): c_elem.configure(bg="#1e293b", highlightbackground=BORDER_COLOR)
            return on_e, on_l

        h_enter, h_leave = make_hover_handlers(card)

        for w in (card, c_head, icon_lbl, t_lbl, snip_lbl, c_foot, w_lbl):
            w.bind("<Button-1>", h_func)
            w.bind("<Enter>", h_enter)
            w.bind("<Leave>", h_leave)

        col += 1
        if col >= cols:
            col = 0
            row += 1


# ---------------- EDITOR VIEW ----------------
editor_frame = tk.Frame(content_container, bg=BG)

style = ttk.Style()
style.theme_use("clam")
style.configure("TNotebook", background=HEADER_BG, borderwidth=0)
style.configure("TNotebook.Tab", background="#1e293b", foreground=TEXT_MUTED,
                padding=(12, 6), borderwidth=0, font=("Segoe UI", 9, "bold"))
style.map("TNotebook.Tab",
          background=[("selected", ACCENT)], foreground=[("selected", "#ffffff")])

nb = ttk.Notebook(editor_frame)
nb.pack(fill="both", expand=True)

# Footer Status Bar
footer = tk.Frame(editor_frame, bg="#090d16", height=28)
footer.pack(fill="x", side="bottom")

lbl_stats = tk.Label(footer, text="0 words • 0 chars", bg="#090d16", fg=TEXT_MUTED,
                     font=("Segoe UI", 8))
lbl_stats.pack(side="left", padx=10)

btn_stamp_footer = tk.Label(footer, text="⏱ Timestamp (Ctrl+T)", bg="#090d16", fg=ACCENT_CYAN,
                            font=("Segoe UI", 8, "bold"), cursor="hand2")
btn_stamp_footer.pack(side="left", padx=10)
btn_stamp_footer.bind("<Button-1>", lambda e: insert_stamp())

grip = tk.Label(footer, text="\u25e2", bg="#090d16", fg=TEXT_MUTED, cursor="size_nw_se")
grip.pack(side="right", padx=4)

editor_frame.pack(fill="both", expand=True)


def hide_all_overlays():
    hide_custom_menu()
    hide_rename_overlay()
    hide_delete_overlay()


def switch_view(target_view):
    global current_view
    current_view = target_view
    hide_all_overlays()
    if target_view == "home":
        editor_frame.pack_forget()
        render_home_screen()
        home_frame.pack(fill="both", expand=True)
        btn_view_home.configure(bg=ACCENT, fg="#ffffff")
        btn_view_editor.configure(bg=HEADER_BG, fg=TEXT_MUTED)
    else:
        home_frame.pack_forget()
        editor_frame.pack(fill="both", expand=True)
        btn_view_editor.configure(bg=ACCENT, fg="#ffffff")
        btn_view_home.configure(bg=HEADER_BG, fg=TEXT_MUTED)
        update_stats()


btn_view_home.bind("<Button-1>", lambda e: switch_view("home"))
btn_view_editor.bind("<Button-1>", lambda e: switch_view("editor"))


# ---------------- CUSTOM IN-APP CONTEXT MENU OVERLAY ----------------
custom_menu = tk.Frame(panel, bg="#1e293b", highlightthickness=1, highlightbackground=ACCENT)

def show_custom_menu(e):
    try:
        clicked_idx = nb.index(f"@{e.x},{e.y}")
        nb.select(clicked_idx)
    except Exception:
        pass

    hide_rename_overlay()
    hide_delete_overlay()

    panel_w = panel.winfo_width()
    panel_h = panel.winfo_height()
    mx = max(10, min(e.x_root - panel.winfo_rootx(), panel_w - 210))
    my = max(36, min(e.y_root - panel.winfo_rooty(), panel_h - 250))

    custom_menu.place(x=mx, y=my, width=205, height=240)
    custom_menu.lift()

def hide_custom_menu(_e=None):
    custom_menu.place_forget()


# ---------------- IN-APP RENAME OVERLAY ----------------
rename_overlay = tk.Frame(panel, bg="#0f172a", highlightthickness=1.5, highlightbackground=ACCENT)

lbl_rename_title = tk.Label(rename_overlay, text="✏️ Rename Tab", bg="#0f172a", fg=TEXT_MAIN, font=("Segoe UI", 10, "bold"))
lbl_rename_title.pack(anchor="w", padx=16, pady=(12, 4))

entry_rename = tk.Entry(rename_overlay, bg="#1e293b", fg="#ffffff", insertbackground="#ffffff",
                        font=("Segoe UI", 10), relief="flat", highlightthickness=1,
                        highlightbackground="#8b5cf6", highlightcolor="#a78bfa")
entry_rename.pack(fill="x", padx=16, pady=6)

btn_rename_frame = tk.Frame(rename_overlay, bg="#0f172a")
btn_rename_frame.pack(fill="x", padx=16, pady=(8, 12))

def hide_rename_overlay(_e=None):
    rename_overlay.place_forget()

def do_apply_rename():
    cur = current()
    name = entry_rename.get().strip()
    hide_rename_overlay()
    if not cur or not name or safe_name(name) == cur["path"].stem:
        return
    save_all()
    new = unique_path(name)
    cur["path"].rename(new)
    cur["path"] = new
    nb.tab(cur["frame"], text=f"  {new.stem}  ")
    if current_view == "home":
        render_home_screen()

btn_rename_cancel = tk.Button(btn_rename_frame, text="Cancel", bg="#334155", fg=TEXT_MAIN,
                              font=("Segoe UI", 9), relief="flat", activebackground="#475569",
                              activeforeground="#ffffff", command=hide_rename_overlay, cursor="hand2", padx=10)
btn_rename_cancel.pack(side="right", padx=(6, 0))

btn_rename_save = tk.Button(btn_rename_frame, text="Rename", bg=ACCENT, fg="#ffffff",
                            font=("Segoe UI", 9, "bold"), relief="flat", activebackground=ACCENT_HOVER,
                            activeforeground="#ffffff", command=do_apply_rename, cursor="hand2", padx=12)
btn_rename_save.pack(side="right")

entry_rename.bind("<Return>", lambda e: do_apply_rename())
entry_rename.bind("<Escape>", lambda e: hide_rename_overlay())

def rename_tab(_e=None):
    ensure_open()
    cur = current()
    if not cur:
        return
    hide_custom_menu()
    hide_delete_overlay()
    entry_rename.delete(0, tk.END)
    entry_rename.insert(0, cur["path"].stem)
    entry_rename.select_range(0, tk.END)
    
    rename_overlay.place(relx=0.5, rely=0.45, anchor="center", width=340, height=135)
    rename_overlay.lift()
    entry_rename.focus_set()


# ---------------- IN-APP DELETE OVERLAY ----------------
delete_overlay = tk.Frame(panel, bg="#0f172a", highlightthickness=1.5, highlightbackground="#ef4444")

lbl_delete_title = tk.Label(delete_overlay, text="🗑️ Delete Tab?", bg="#0f172a", fg="#ef4444", font=("Segoe UI", 10, "bold"))
lbl_delete_title.pack(anchor="w", padx=16, pady=(12, 4))

lbl_delete_msg = tk.Label(delete_overlay, text="Are you sure you want to delete this tab?", bg="#0f172a", fg=TEXT_MUTED, font=("Segoe UI", 9), wraplength=300, justify="left")
lbl_delete_msg.pack(anchor="w", padx=16, pady=4)

btn_delete_frame = tk.Frame(delete_overlay, bg="#0f172a")
btn_delete_frame.pack(fill="x", padx=16, pady=(8, 12))

def hide_delete_overlay(_e=None):
    delete_overlay.place_forget()

def do_apply_delete():
    hide_delete_overlay()
    cur = current()
    if not cur:
        return
    cur["path"].unlink(missing_ok=True)
    nb.forget(cur["frame"])
    cur["frame"].destroy()
    tabs.remove(cur)
    draw_bubble(len(tabs))
    if not tabs:
        add_tab(unique_path("Note"))
    if current_view == "home":
        render_home_screen()
    update_stats()

btn_delete_cancel = tk.Button(btn_delete_frame, text="Cancel", bg="#334155", fg=TEXT_MAIN,
                              font=("Segoe UI", 9), relief="flat", activebackground="#475569",
                              activeforeground="#ffffff", command=hide_delete_overlay, cursor="hand2", padx=10)
btn_delete_cancel.pack(side="right", padx=(6, 0))

btn_delete_confirm = tk.Button(btn_delete_frame, text="Delete", bg="#ef4444", fg="#ffffff",
                               font=("Segoe UI", 9, "bold"), relief="flat", activebackground="#dc2626",
                               activeforeground="#ffffff", command=do_apply_delete, cursor="hand2", padx=12)
btn_delete_confirm.pack(side="right")

def delete_tab(_e=None):
    ensure_open()
    cur = current()
    if not cur:
        return
    hide_custom_menu()
    hide_rename_overlay()
    lbl_delete_msg.configure(text=f'Delete "{cur["path"].stem}" and its file?')
    delete_overlay.place(relx=0.5, rely=0.45, anchor="center", width=340, height=135)
    delete_overlay.lift()


# ---------------- HELPERS ----------------
def safe_name(name):
    return re.sub(r'[\\/:*?"<>|]', "_", name).strip()


def unique_path(stem):
    stem = safe_name(stem) or "Note"
    p = NOTES_DIR / f"{stem}.txt"
    i = 2
    while p.exists() or any(t["path"] == p for t in tabs):
        p = NOTES_DIR / f"{stem} {i}.txt"
        i += 1
    return p


def stamp():
    s = int(time.time() - START)
    return f"[{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}] "


def current():
    if not tabs:
        return None
    try:
        idx = nb.index(nb.select())
        return tabs[idx] if idx < len(tabs) else None
    except Exception:
        return None


def update_stats(_e=None):
    cur = current()
    if not cur:
        lbl_stats.configure(text="0 words • 0 chars")
        return
    text_val = cur["text"].get("1.0", "end-1c")
    words = len(text_val.strip().split()) if text_val.strip() else 0
    chars = len(text_val)
    lbl_stats.configure(text=f"{words} words • {chars} chars")


def add_tab(path, content=""):
    frame = tk.Frame(nb, bg=BG)
    t = tk.Text(frame, wrap="word", bg=BG, fg=TEXT_MAIN, insertbackground="#ffffff",
                font=("Segoe UI", 11), padx=12, pady=12, undo=True, borderwidth=0,
                selectbackground="#475569")
    t.pack(fill="both", expand=True)
    t.insert("1.0", content)
    t.bind("<Control-t>", insert_stamp)
    t.bind("<KeyRelease>", update_stats)

    t.bind("<Button-1>", lambda e: hide_all_overlays())

    nb.add(frame, text=f"  {path.stem}  ")
    tabs.append({"frame": frame, "text": t, "path": path})
    nb.select(frame)
    t.focus_set()
    draw_bubble(len(tabs))
    update_stats()


def save_all(_e=None):
    for t in tabs:
        t["path"].write_text(t["text"].get("1.0", "end-1c"), encoding="utf-8")


def ensure_open():
    if not panel.winfo_ismapped():
        expand()


# ---------------- TAB ACTIONS ----------------
def new_tab(_e=None):
    ensure_open()
    add_tab(unique_path("Note"))


def save_as(_e=None):
    ensure_open()
    cur = current()
    if not cur:
        return
    hide_all_overlays()
    root.attributes("-topmost", False)
    f = filedialog.asksaveasfilename(
        parent=root, defaultextension=".txt", initialfile=cur["path"].stem + ".txt",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    root.attributes("-topmost", True)
    root.lift()
    if f:
        Path(f).write_text(cur["text"].get("1.0", "end-1c"), encoding="utf-8")


def open_txt(_e=None):
    ensure_open()
    hide_all_overlays()
    root.attributes("-topmost", False)
    f = filedialog.askopenfilename(
        parent=root, filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    root.attributes("-topmost", True)
    root.lift()
    if f:
        content = Path(f).read_text(encoding="utf-8", errors="replace")
        add_tab(unique_path(Path(f).stem), content)
        if current_view == "home":
            render_home_screen()


def insert_stamp(_e=None):
    ensure_open()
    cur = current()
    if cur:
        cur["text"].insert("insert", stamp())
        update_stats()
    return "break"


# ---------------- POPULATE CUSTOM MENU ITEMS ----------------
menu_items = [
    ("➕  New tab", lambda: (hide_all_overlays(), new_tab())),
    ("✏️  Rename tab", lambda: rename_tab()),
    ("🗑️  Delete tab", lambda: delete_tab()),
    ("💾  Save As...", lambda: save_as()),
    ("📁  Open .txt File", lambda: open_txt()),
    ("⏱️  Insert Timestamp", lambda: (hide_all_overlays(), insert_stamp())),
    ("💾  Save All", lambda: (hide_all_overlays(), save_all())),
    ("✕  Quit", lambda: (hide_all_overlays(), quit_app())),
]

for label_str, cmd_func in menu_items:
    item_lbl = tk.Label(custom_menu, text=label_str, bg="#1e293b", fg=TEXT_MAIN, anchor="w",
                        font=("Segoe UI", 9), padx=14, pady=5, cursor="hand2")
    
    def make_item_handlers(l_elem, c_func):
        def on_enter(_e): l_elem.configure(bg=ACCENT, fg="#ffffff")
        def on_leave(_e): l_elem.configure(bg="#1e293b", fg=TEXT_MAIN)
        def on_click(_e): c_func()
        return on_enter, on_leave, on_click

    h_e, h_l, h_c = make_item_handlers(item_lbl, cmd_func)
    item_lbl.bind("<Enter>", h_e)
    item_lbl.bind("<Leave>", h_l)
    item_lbl.bind("<Button-1>", h_c)
    item_lbl.pack(fill="x")


# ---------------- SMOOTH ANIMATIONS (EXPAND & COLLAPSE) ----------------
def animate_geometry(start_w, start_h, target_w, target_h, start_x, start_y, target_x, target_y, steps=14, current_step=0, on_complete=None):
    global animating
    if current_step > steps:
        animating = False
        root.geometry(f"{target_w}x{target_h}+{target_x}+{target_y}")
        if on_complete:
            on_complete()
        return

    progress = current_step / steps
    ease = 1 - math.pow(1 - progress, 3)

    cur_w = int(start_w + (target_w - start_w) * ease)
    cur_h = int(start_h + (target_h - start_h) * ease)
    cur_x = int(start_x + (target_x - start_x) * ease)
    cur_y = int(start_y + (target_y - start_y) * ease)

    root.geometry(f"{cur_w}x{cur_h}+{cur_x}+{cur_y}")
    root.after(14, lambda: animate_geometry(start_w, start_h, target_w, target_h, start_x, start_y, target_x, target_y, steps, current_step + 1, on_complete))


def expand():
    global animating
    if animating:
        return
    animating = True

    target_w, target_h = size["w"], size["h"]
    start_x, start_y = root.winfo_x(), root.winfo_y()

    target_x = max(0, min(start_x, root.winfo_screenwidth() - target_w))
    target_y = max(0, min(start_y, root.winfo_screenheight() - target_h - 40))

    bubble.pack_forget()
    panel.pack(fill="both", expand=True)

    def on_expand_done():
        root.focus_force()
        if current_view == "home":
            render_home_screen()
        else:
            cur = current()
            if cur:
                cur["text"].focus_set()
                update_stats()

    animate_geometry(BUBBLE, BUBBLE, target_w, target_h, start_x, start_y, target_x, target_y, steps=14, on_complete=on_expand_done)


def collapse(_e=None):
    global animating
    if animating:
        return
    animating = True
    hide_all_overlays()
    save_all()

    start_w, start_h = root.winfo_width(), root.winfo_height()
    start_x, start_y = root.winfo_x(), root.winfo_y()

    def on_collapse_done():
        panel.pack_forget()
        bubble.pack()
        root.geometry(f"{BUBBLE}x{BUBBLE}+{start_x}+{start_y}")

    animate_geometry(start_w, start_h, BUBBLE, BUBBLE, start_x, start_y, start_x, start_y, steps=14, on_complete=on_collapse_done)


def quit_app():
    save_all()
    root.destroy()


# ---------------- DRAGGING & RESIZING ----------------
drag = {"dx": 0, "dy": 0, "sx": 0, "sy": 0, "moved": False}
rs = {"x": 0, "y": 0, "w": 0, "h": 0}


def start_drag(e):
    hide_all_overlays()
    drag.update(dx=e.x_root - root.winfo_x(), dy=e.y_root - root.winfo_y(),
                sx=e.x_root, sy=e.y_root, moved=False)


def do_drag(e):
    if abs(e.x_root - drag["sx"]) > 3 or abs(e.y_root - drag["sy"]) > 3:
        drag["moved"] = True
    root.geometry(f"+{e.x_root - drag['dx']}+{e.y_root - drag['dy']}")


def bubble_release(_e):
    if not drag["moved"]:
        expand()


def start_resize(e):
    hide_all_overlays()
    rs.update(x=e.x_root, y=e.y_root, w=root.winfo_width(), h=root.winfo_height())


def do_resize(e):
    w = max(340, rs["w"] + e.x_root - rs["x"])
    h = max(280, rs["h"] + e.y_root - rs["y"])
    size.update(w=w, h=h)
    root.geometry(f"{w}x{h}")


for w in (bubble, header, title, title_icon):
    w.bind("<ButtonPress-1>", start_drag)
    w.bind("<B1-Motion>", do_drag)
bubble.bind("<ButtonRelease-1>", bubble_release)
grip.bind("<ButtonPress-1>", start_resize)
grip.bind("<B1-Motion>", do_resize)

# ---------------- TAB BINDINGS ----------------
def on_double_click(e):
    hide_all_overlays()
    try:
        clicked_idx = nb.index(f"@{e.x},{e.y}")
        nb.select(clicked_idx)
        rename_tab()
    except Exception:
        pass


for w in (header, title, title_icon):
    w.bind("<Button-3>", show_custom_menu)

nb.bind("<Button-3>", show_custom_menu)
nb.bind("<Double-Button-1>", on_double_click)

header.bind("<Button-1>", lambda e: hide_all_overlays())
content_container.bind("<Button-1>", lambda e: hide_all_overlays())

root.bind("<Control-n>", new_tab)
root.bind("<Control-w>", delete_tab)
root.bind("<Control-s>", save_all)
root.bind("<Control-S>", save_as)
root.bind("<Escape>", collapse)
nb.bind("<<NotebookTabChanged>>",
        lambda e: (tabs and current() and current()["text"].focus_set(), update_stats()))

# ---------------- LOAD EXISTING NOTES ----------------
for p in sorted(NOTES_DIR.glob("*.txt"), key=lambda p: p.stat().st_ctime):
    add_tab(p, p.read_text(encoding="utf-8", errors="replace"))
if not tabs:
    add_tab(unique_path("Note"))
nb.select(0)
update_stats()


# ---------------- KEEP ON TOP & AUTOSAVE ----------------
def keep_on_top():
    root.attributes("-topmost", True)
    root.after(2000, keep_on_top)


def autosave():
    save_all()
    root.after(5000, autosave)


keep_on_top()
autosave()
root.mainloop()
