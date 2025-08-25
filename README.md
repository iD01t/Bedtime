# Bedtime Story Maker

*iD01t Productions — Premium Pro Edition*

## Overview

**Bedtime Story Maker** is a polished desktop application that instantly creates unique, beautifully written bedtime stories for children. Simply enter a topic, the child’s name and age, and choose tone and length — the app generates an original story every time.

This final version is **self-contained**: the JSON templates (25 English + 25 French themes) are embedded in the script backend. The app is production-ready, styled with a modern dark glass-like UI, and supports saving, exporting, and customizing stories.

---

## Features

✨ **Story Generation**

* 25 unique story themes in English
* 25 unique story themes in French
* Adjustable **tone** (Gentle, Adventurous, Funny, Magical, Soothing / Doux, Aventurier, Drôle, Magique, Apaisant)
* Adjustable **length** (Short, Medium, Long)
* Optional **breathing exercise**
* Optional **moral lesson**

📝 **Library & Export**

* Save stories to an in-app library (`stories.json`)
* Export to **TXT, HTML, and PDF** (PDF requires `reportlab`)
* Copy stories directly to clipboard

🎨 **Polished Interface**

* Auto-scaling **dreamy background** (PNG/JPG supported)
* Dark theme with glass-like panels and rounded elements
* Professional typography with system font stack
* Bilingual UI (English / Français)
* **About dialog** credits iD01t Productions, Guillaume Lessard

⚙️ **Extensibility**

* Embedded JSON templates guarantee offline functionality
* Optional external `content_creators.json` overrides the built-in set
* Gemini API key placeholder included in **Settings** for future AI integrations

---

## Installation

1. **Dependencies**

   * Python 3.9+
   * Tkinter (bundled with Python)
   * [Pillow](https://pypi.org/project/Pillow/) (optional, for image scaling)
   * [reportlab](https://pypi.org/project/reportlab/) (optional, for PDF export)

   Install extras with:

   ```bash
   pip install pillow reportlab
   ```

2. **Run the app**

   ```bash
   python main.py
   ```

3. **Windows EXE (optional)**
   Build a distributable with PyInstaller:

   ```bash
   pyinstaller --noconfirm --onefile --windowed --icon=icon.ico main.py
   ```

   Place `background.png` and `icon.ico` in the same folder as the executable.

---

## Usage

1. Enter a **topic** (e.g., “dragons”).
2. Add the child’s **name** and **age** (optional).
3. Select **tone**, **length**, and language (**English** or **Français**).
4. Toggle breathing/moral guidance.
5. Click **Generate** → a brand-new story appears instantly.
6. Save it, export it, or replay another one!

---

## File Structure

```
main.py              # Main application (self-contained with templates)
icon.ico             # Application icon
background.png       # Background image
stories.json         # Auto-saved user library (created at runtime)
```

---

## Credits

* **Created by**: iD01t Productions
* **Author**: Guillaume Lessard ([admin@id01t.store](mailto:admin@id01t.store))
* **License**: MIT

---

