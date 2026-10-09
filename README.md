# ✦ Floaty - Floating Desktop Note Bubble with Tabs

> A lightweight, glowing floating desktop note-taking app for Windows built with Python & Tkinter. Features smooth easing animations, a modern glassmorphic dark theme, multi-tab editing, a Home Dashboard grid, and a standard Windows Setup installer wizard (`FloatySetup.exe`).

---

## ⬇️ Installation for Windows Users

### 🌟 Recommended: Download Installer (`FloatySetup.exe`)

1. Download **[FloatySetup.exe](FloatySetup.exe)** from this repository or Releases.
2. Double-click `FloatySetup.exe` and click **YES** on the Windows permission prompt.
3. Follow the installation wizard. It will automatically:
   - Install Floaty on your PC
   - Create a **Start Menu Shortcut**
   - Create a **Desktop Shortcut** (optional)
   - Allow pinning directly to your **Windows Taskbar**

---

## ✨ Features

- **Floating Overlay Bubble**: Stays on top of every app window (`-topmost`). Drag it anywhere on your desktop.
- **Smooth Ease Animations**: Window expands and collapses smoothly from the bubble's exact screen position using cubic ease-out interpolation.
- **Home Dashboard View (`🏠 Home`)**: Visual grid layout showing note thumbnail cards with live text snippet previews, word counts, plus a **New Notebook Note (`+`)** card.
- **Multi-Tab Editor (`✎ Editor`)**: Clean tabbed text notebook supporting instant tab switching, live word/character counts, and relative timestamping (`[HH:MM:SS]`).
- **In-App Modal Dialogs**: Custom dark overlay dialogs for tab renaming and tab deletion (100% bug-free, zero window focus loss).
- **Persistent Text Files**: Every tab corresponds to an actual `.txt` file automatically saved inside a local `notes/` directory. Auto-saved every 5 seconds.

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Description |
| :--- | :--- |
| <kbd>Ctrl</kbd> + <kbd>N</kbd> | Create a new note tab |
| <kbd>Ctrl</kbd> + <kbd>W</kbd> | Delete current note tab (with prompt) |
| <kbd>Ctrl</kbd> + <kbd>S</kbd> | Save all notes |
| <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>S</kbd> | Export current tab as `.txt` file |
| <kbd>Ctrl</kbd> + <kbd>T</kbd> | Insert relative timestamp `[HH:MM:SS]` |
| <kbd>Double-Click Tab</kbd> | Rename active tab |
| <kbd>Esc</kbd> | Collapse window back to floating bubble |

---

## 🛠️ How to Build from Source

### 1. Build Single Executable with PyInstaller
```powershell
pip install pyinstaller
python -m PyInstaller --onefile --noconsole floaty.py
```

### 2. Compile Windows Installer Wizard with Inno Setup
```powershell
& "C:\Users\sunny\AppData\Local\Programs\Inno Setup 6\ISCC.exe" setup.iss
```

---

## 📄 Documentation

For full architecture details, design principles, step-by-step creation breakdown, system diagrams, and user flow charts, see [notes.md](notes.md).

---

## 📜 License

MIT License. Feel free to use, modify, and distribute.
