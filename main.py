#!/usr/bin/env python3
# Bedtime Story Maker — iD01t Productions (Premium Pro Edition)
# v2.0.0 — Refined UI, full production ready, polished dark theme
# This script implements a story generator for bedtime tailored stories.
# Features:
#   * Bilingual interface (English & French)
#   * Adjustable tone and length
#   * Breathing and moral guidance toggles
#   * Save generated stories into an in-app library
#   * Export stories as plain text, HTML, and PDF
#   * Copy to clipboard
#   * Auto-scaling dreamy background with crisp cover fit
#   * Clear and professional interface with readable inputs and dark glass-like cards
# License: MIT
# --- Tk data fix for PyInstaller onefile on Windows ---
import os, sys
if hasattr(sys, "_MEIPASS"):  # exe PyInstaller
    base = sys._MEIPASS
    os.environ["TCL_LIBRARY"] = os.path.join(base, "tcl", "tcl8.6")
    os.environ["TK_LIBRARY"]  = os.path.join(base, "tcl", "tk8.6")
# ------------------------------------------------------
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import random
import html
import datetime
import json
import zlib, base64
import os
import sys
import textwrap

APP_NAME = "Bedtime Story Maker"
APP_VERSION = "2.5.0"
DATA_FILE = "stories.json"
# Location of optional templates file used for story generation.
# For version 2.5.0 and beyond we support multiple thematic
# "content creators" (themes).  This file contains a list of 25
# themes for both English and French along with story openings,
# middle segments, closings, breathing guidance and moral lines.  If
# the file is missing the application falls back to built‑in
# defaults.  See load_story_templates() for details.
TEMPLATES_FILE = "content_creators.json"
BG_CANDIDATES = ["background.png", "background.jpg"]

# Embedded story templates (compressed and base64 encoded).
# The JSON contents of ``content_creators.json`` have been compressed
# using zlib and encoded with base64 to embed them directly into
# this script.  Use ``get_embedded_templates()`` to decode and
# parse the data when an external file is not available.
EMBEDDED_TEMPLATES_B64 = """
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
"""

def get_embedded_templates():
    """
    Decode and decompress the embedded story templates into a Python dict.
    Returns an empty dict on failure.
    """
    try:
        raw = zlib.decompress(base64.b64decode(EMBEDDED_TEMPLATES_B64.strip()))
        return json.loads(raw.decode('utf-8'))
    except Exception:
        return {}

# Optional dependency for image scaling (Pillow)
try:
    from PIL import Image, ImageTk
    PIL_OK = True
except Exception:
    PIL_OK = False

# Optional dependency for PDF export (reportlab)
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas as pdf_canvas
    REPORTLAB_OK = True
except Exception:
    REPORTLAB_OK = False

# Determine application directory (handles PyInstaller bundle)
def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

# Load saved stories from disk
def load_library():
    path = os.path.join(app_dir(), DATA_FILE)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

# Save stories to disk
def save_library(items):
    path = os.path.join(app_dir(), DATA_FILE)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Failed saving library:", e)

# Load story generation templates from JSON file. If the file doesn't exist or
# cannot be parsed, returns an empty dictionary. The expected structure is
# documented in story_templates.json and allows per-language customization of
# openings, segments, closings, breathing lines, and tone mappings.
def load_story_templates():
    """
    Load story generation templates from JSON.  Beginning with
    version 2.5.0 the templates file contains multiple thematic sets
    ("content creators").  The top‑level structure is expected to be
    either a dictionary keyed by language (backwards compatibility) or
    a dictionary where each language key maps to a list of creator
    dictionaries.  Each creator dictionary should include keys
    "name", "opening", "segments", "closing", "breathing",
    "moral", "tone_map", "title_label", "default_name",
    "default_age" and "default_topic".  If the file cannot be read
    or parsed, an empty dict is returned.
    """
    path = os.path.join(app_dir(), TEMPLATES_FILE)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Accept any JSON structure – return as loaded.  Caller must
            # handle list vs dict.
            return data
    except Exception:
        # On error (file missing or malformed) return the embedded templates.
        return get_embedded_templates()

# Wrap paragraphs to a certain width for the preview text
def wrap_paragraphs(text, width=86):
    lines = []
    for para in text.split("\n"):
        if para.strip():
            lines.extend(textwrap.wrap(para.strip(), width=width))
            lines.append("")
        else:
            lines.append("")
    return "\n".join(lines).strip()

# Story generation constants
EN_TONES = ["Gentle", "Adventurous", "Funny", "Magical", "Soothing"]
FR_TONES = ["Doux", "Aventurier", "Drôle", "Magique", "Apaisant"]
LANGS = ["English", "Français"]

# Generate a bedtime story based on parameters
def generate_story(topic, child_name, age, tone, length, language,
                   include_breathing, include_moral,
                   templates=None, creator_index=None):
    """
    Generate a bedtime story based on the provided parameters.

    Parameters
    ----------
    topic : str
        The theme or subject that the child is thinking about.
    child_name : str
        Name of the child in the story.
    age : str
        Age of the child (string to allow flexible input like "6" or "six").
    tone : str
        Tone selection (e.g., Gentle, Adventurous).  Used to pick a phrase
        describing how the story proceeds.
    length : str
        Desired length of the story (Short, Medium, Long).
    language : str
        Language for the story (English or Français).
    include_breathing : bool
        Whether to include a breathing exercise instruction in the story.
    include_moral : bool
        Whether to include a moral at the end of the story.
    templates : dict or list, optional
        Templates loaded from JSON.  May be a dictionary keyed by
        language or a dictionary where each language key maps to a list
        of thematic creator dictionaries.
    creator_index : int, optional
        Index into the list of creators for the given language.  If
        None or invalid, a random creator will be chosen when multiple
        are available.  Ignored when only a single template exists for
        the chosen language.

    Notes
    -----
    The middle segments are selected without repetition (using
    ``random.sample``) to maximise variety.  If there are
    insufficient unique segments for the desired length, sampling
    with replacement is used as a fallback.  Unlike previous
    versions, the story generator no longer seeds the random module
    based on the inputs.  This means that generating a story with
    the same parameters will yield different results, ensuring
    originality and variety.
    """
    # Determine how many paragraphs are desired based on length
    target_paras = {"Short": 4, "Medium": 7, "Long": 10}.get(length, 7)

    # Decide which template to use from supplied templates
    tpl = None
    if templates:
        # When templates is a dict keyed by language
        lang_tpls = templates.get(language)
        if isinstance(lang_tpls, list):
            # Multiple creator options.  Pick by index if valid, else random.
            if isinstance(creator_index, int) and 0 <= creator_index < len(lang_tpls):
                tpl = lang_tpls[creator_index]
            elif lang_tpls:
                tpl = random.choice(lang_tpls)
        elif isinstance(lang_tpls, dict):
            tpl = lang_tpls

    if tpl:
        # Extract from JSON
        opening_templates = tpl.get("opening", []) or []
        seg_templates = tpl.get("segments", []) or []
        closing_templates = tpl.get("closing", []) or []
        breathing_line = tpl.get("breathing", "")
        moral_line = tpl.get("moral", "")
        tone_map = tpl.get("tone_map", {}) or {}
        title_label = tpl.get("title_label", "Bedtime Story")
        default_name = tpl.get("default_name", "the child")
        default_age = tpl.get("default_age", "6")
        default_topic = tpl.get("default_topic", "a gentle idea")
    else:
        # Fallback built‑in defaults depending on language
        if language == "Français":
            opening_templates = [
                "Il était une fois, {name}, {age} ans, qui adorait penser à {topic}.",
                "Ce soir-là, {name}, âgé(e) de {age} ans, ne cessait d'imaginer {topic}.",
                "Dans une petite chambre baignée de lune, {name}, {age} ans, rêvait à {topic}.",
            ]
            tone_map = {
                "Doux": "tout doucement, comme une brise tiède",
                "Aventurier": "avec courage et curiosité",
                "Drôle": "en riant de petites surprises",
                "Magique": "dans un monde scintillant de surprises",
                "Apaisant": "avec un calme profond et rassurant",
            }
            seg_templates = [
                "Alors que {name} fermait les yeux, une petite lueur apparut près du lit. Elle murmurait des histoires de {topic}.",
                "{name} suivit un sentier de lumière, {tone}, et découvrit un secret sur {topic} que seul un cœur ouvert pouvait entendre.",
                "Un ami inattendu se présenta, parlant doucement de {topic} et partageant une sagesse ancienne.",
                "Le monde autour de {name} respirait lentement, et chaque inspiration rendait {topic} plus clair et plus bienveillant.",
                "Une étoile guida {name} vers un endroit où {topic} brillait de mille feux, révélant une petite leçon du cœur.",
            ]
            closing_templates = [
                "Quand {name} revint dans son lit, tout paraissait plus simple. {topic} devenait un doux souvenir pour faire de beaux rêves.",
                "Rassuré(e), {name} se laissa bercer par la nuit. {topic} était devenu un ami tranquille, prêt à veiller jusqu'au matin.",
                "La lune sourit à {name}, et {topic} s'endormit aussi, pour que le silence soigne le cœur et le corps.",
            ]
            breathing_line = "Inspire par le nez pendant 3, bloque 2, expire lentement pendant 4. Répète trois fois, très doucement."
            moral_line = "Moralité : Même les grands sujets deviennent légers lorsque l'on respire calmement et que l'on écoute son cœur."
            title_label = "Histoire du soir"
            default_name = "le enfant"
            default_age = "6"
            default_topic = "une douce idée"
        else:
            opening_templates = [
                "Once upon a time, {name}, age {age}, loved thinking about {topic}.",
                "That night, {name}, a {age}-year-old dreamer, couldn't stop imagining {topic}.",
                "In a moonlit room, {name}, age {age}, drifted into thoughts of {topic}.",
            ]
            tone_map = {
                "Gentle": "very gently, like a warm breeze",
                "Adventurous": "with courage and curiosity",
                "Funny": "with small surprises and giggles",
                "Magical": "in a world full of sparkling wonders",
                "Soothing": "with deep comfort and calm",
            }
            seg_templates = [
                "As {name} closed their eyes, a tiny light appeared by the bed, whispering stories of {topic}.",
                "{name} followed a ribbon of starlight, {tone}, and discovered a secret about {topic} that only an open heart could hear.",
                "An unexpected friend arrived, speaking softly about {topic} and sharing a gentle wisdom.",
                "The world around {name} breathed slowly, and with each breath, {topic} felt kinder and clearer.",
                "A guiding star led {name} somewhere {topic} glowed, revealing a small lesson for the heart.",
            ]
            closing_templates = [
                "When {name} returned to their bed, everything felt simpler. {topic} became a soft memory to dream about.",
                "Feeling safe, {name} let the night rock them to sleep. {topic} had become a quiet friend, watching until morning.",
                "The moon smiled at {name}, and {topic} fell asleep too, so silence could gently mend heart and body.",
            ]
            breathing_line = "Breathe in through the nose for 3, hold for 2, breathe out slowly for 4. Repeat softly three times."
            moral_line = "Moral: Even big ideas feel light when we breathe calmly and listen to our heart."
            title_label = "Bedtime Story"
            default_name = "the child"
            default_age = "6"
            default_topic = "a gentle idea"

    paragraphs = []
    # Opening paragraph
    opening = random.choice(opening_templates).format(
        name=child_name or default_name,
        age=age or default_age,
        topic=topic or default_topic,
    )
    paragraphs.append(opening)

    # Determine how many middle segments are needed
    needed = max(0, target_paras - 2)
    # Select segments without repetition when possible. If there are not enough
    # unique templates, fall back to random choices with replacement.
    if seg_templates:
        if needed <= len(seg_templates):
            # Choose unique indices and sort them to preserve narrative ordering
            indices = random.sample(range(len(seg_templates)), needed)
            indices.sort()
            chosen = [seg_templates[i] for i in indices]
        else:
            # Not enough unique segments; allow repeats
            chosen = [random.choice(seg_templates) for _ in range(needed)]
        for seg in chosen:
            paragraphs.append(seg.format(
                name=child_name or default_name,
                topic=topic or default_topic,
                tone=tone_map.get(tone, ""),
            ))

    # Optional breathing and moral
    if include_breathing and breathing_line:
        paragraphs.append(breathing_line)
    if include_moral and moral_line:
        paragraphs.append(moral_line)

    # Closing paragraph
    closing = random.choice(closing_templates).format(
        name=child_name or default_name,
        topic=topic or default_topic,
    )
    paragraphs.append(closing)

    # Join paragraphs and wrap for preview
    body = "\n\n".join(paragraphs)
    body = wrap_paragraphs(body, width=86)

    # Compose title block
    topic_title = (topic or ("Rêve" if language == "Français" else "Dream")).strip().title()
    name_title = (child_name or "").strip().title()
    meta_line = f"{title_label} • {topic_title}" if not name_title else f"{title_label} • {topic_title} • {name_title}"
    title_block = f"{meta_line}\n" + ("—" * len(meta_line)) + "\n"
    return f"{title_block}\n{body}\n"

# Generate an HTML document for story export
def to_html(title, body_text, language):
    safe_body = html.escape(body_text).replace("\n", "<br>")
    font = "system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif"
    subtitle = "Une douce histoire du soir" if language == "Français" else "A calm bedtime story"
    style = """
:root {
  --bg:#0b0f1f;
  --panel:#151a33;
  --text:#eaf0ff;
  --muted:#b8c0ec;
  --border:#232a49;
}
body { background:var(--bg); color:var(--text); font-family:%s; line-height:1.7; padding:24px; max-width:900px; margin:auto; }
h1 { margin:0 0 6px 0; font-size:28px; }
h2 { margin:0 0 18px 0; color:var(--muted); font-size:16px; font-weight:500; }
.article { background:var(--panel); padding:20px; border:1px solid var(--border); border-radius:14px; }
.footer { color:var(--muted); font-size:12px; margin-top:24px; }
""" % font
    lang = "fr" if language == "Français" else "en"
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>{style}</style>
</head>
<body>
  <h1>{html.escape(title)}</h1>
  <h2>{subtitle}</h2>
  <div class="article">{safe_body}</div>
  <div class="footer">Generated by {APP_NAME} v{APP_VERSION} — {datetime.date.today().isoformat()}</div>
</body>
</html>"""

# Export story to PDF using reportlab
def to_pdf(filepath, title, body_text, language):
    if not REPORTLAB_OK:
        raise RuntimeError("reportlab not available: install reportlab to enable PDF export")
    c = pdf_canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    margin = 50
    y = height - margin
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin, y, title)
    y -= 24
    sub_title = "Une douce histoire du soir" if language == "Français" else "A calm bedtime story"
    c.setFont("Helvetica", 12)
    c.drawString(margin, y, sub_title)
    y -= 32
    c.setFont("Helvetica", 11)
    lines = body_text.split("\n")
    for line in lines:
        if y < margin:
            c.showPage()
            y = height - margin
            c.setFont("Helvetica", 11)
        c.drawString(margin, y, line)
        y -= 14
    c.showPage()
    c.save()

# Main application class
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        # Window configuration
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("980x640")
        self.minsize(900, 580)

        # Attempt to set custom icon
        try:
            ico_path = os.path.join(app_dir(), "icon.ico")
            if os.path.exists(ico_path):
                self.iconbitmap(ico_path)
        except Exception:
            pass

        # Updated colour palette for a softer, more inviting look.  These
        # hues are inspired by modern "pastel UI" trends: very light
        # backgrounds with gentle lavender and berry accents.  The
        # darker text colours ensure readability against the light
        # backgrounds, while the button colours provide a friendly
        # contrast for actionable elements.
        self.colors = {
            "bg": "#fffbfd",          # window background (pale pinkish white)
            "panel": "#ffffff",       # cards/panels (pure white)
            "text": "#46344e",        # primary text (deep plum)
            "muted": "#8e819a",       # secondary text (muted lavender)
            "border": "#f3e5f5",      # panel border (light lavender)
            "entry_bg": "#fffafc",    # entry widgets (hint of blush)
            "entry_fg": "#46344e",    # entry text (deep plum)
            "sel": "#eadbf2",         # listbox/text selection (pale lavender)
            "button_bg": "#c084fc",   # buttons (light purple)
            "button_hover": "#a855f7",# button hover (medium purple)
        }
        # Apply page background
        self.configure(bg=self.colors["bg"])

        # Build the top menu bar.  A modern application benefits from
        # a simple menu for global actions.  This menu consolidates
        # library operations (save, load, delete), provides access to
        # settings, and exposes an “About” dialog.  The menu bar is
        # created before the rest of the UI so that it appears at
        # the top of the window immediately.
        self._build_menu()

        # Style customizations for ttk
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        # Use slightly larger font sizes on labels for improved
        # readability on modern high‑DPI displays.
        style.configure("TLabel", background=self.colors["panel"], foreground=self.colors["text"], font=("Segoe UI", 13))
        # Buttons: pastel backgrounds with white text for contrast
        style.configure("TButton", background=self.colors["button_bg"], foreground="#ffffff", font=("Segoe UI", 13), borderwidth=0)
        style.map("TButton",
                  background=[("active", self.colors["button_hover"]), ("!active", self.colors["button_bg"])],
                  foreground=[("active", "#ffffff"), ("!active", "#ffffff")]
                  )
        style.configure("TCheckbutton", background=self.colors["panel"], foreground=self.colors["text"], font=("Segoe UI", 13))
        style.configure("Clean.TCombobox",
                        fieldbackground=self.colors["entry_bg"],
                        background=self.colors["entry_bg"],
                        foreground=self.colors["entry_fg"],
                        bordercolor=self.colors["border"],
                        relief="flat",
                        )
        style.map("Clean.TCombobox",
                  fieldbackground=[("readonly", self.colors["entry_bg"])],
                  foreground=[("readonly", self.colors["entry_fg"])]
                  )

        # Background canvas
        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0, bg=self.colors["bg"])
        self.canvas.pack(fill="both", expand=True)
        self.bind("<Configure>", self._on_resize)
        self.bg_original, self.bg_photo = self._load_background()

        # Data variables
        # Load optional story templates.  If the JSON is missing or
        # empty, this will be an empty dict and the built‑in
        # defaults will be used.  Templates may be a dictionary
        # keyed by language or a dictionary where each language maps
        # to a list of thematic creator dictionaries.
        self.story_templates = load_story_templates()
        self.topic_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.age_var = tk.StringVar(value="6")
        self.length_var = tk.StringVar(value="Medium")
        self.lang_var = tk.StringVar(value=LANGS[0])
        self.tone_var = tk.StringVar(value=EN_TONES[0])
        self.include_breathing = tk.BooleanVar(value=True)
        self.include_moral = tk.BooleanVar(value=True)
        # Variable for selecting a content creator (theme).  This will
        # be populated based on the loaded templates for the current
        # language.  If no templates are available, a single default
        # option is provided.
        self.creator_var = tk.StringVar()
        # Holds the list of available creator names for the current language.
        self.creator_names = []
        # Variable to store an optional Gemini API key.  This field is
        # purely for user input; it is not utilised in this version
        # because external API calls are disabled.  It lays the
        # groundwork for future functionality.
        self.gemini_key_var = tk.StringVar()
        self.library = load_library()

        # Layout containers: sidebar (left) & content (right)
        self.sidebar = tk.Frame(self, bg=self.colors["panel"], highlightbackground=self.colors["border"], highlightthickness=1)
        self.content = tk.Frame(self, bg=self.colors["panel"], highlightbackground=self.colors["border"], highlightthickness=1)
        # Place the sidebar and content with updated widths for modern layout
        self.sidebar.place(x=14, y=14, width=260, height=self.winfo_height() - 28)
        # Compute content x-offset: sidebar (260) + gap (14) + left padding (14)
        self.content.place(x=14 + 260 + 14, y=14,
                           width=self.winfo_width() - ((14) + 260 + 14 + 14),
                           height=self.winfo_height() - 28)

        # Sidebar content
        self._build_sidebar()
        # Content area (form + preview)
        self._build_content()
        # Populate library list
        self.refresh_library_list()
        # Adjust tone list based on initial language
        self._on_lang_change()

    # ----------------------- UI Building -----------------------
    def _build_sidebar(self):
        # Header
        header = tk.Label(self.sidebar, text="Saved Stories", bg=self.colors["panel"], fg=self.colors["text"], font=("Segoe UI", 12, "bold"))
        header.pack(anchor="w", padx=12, pady=(12,6))
        # Listbox with scrollbar
        list_frame = tk.Frame(self.sidebar, bg=self.colors["panel"])
        list_frame.pack(fill="both", expand=True, padx=12, pady=(0,8))
        self.listbox = tk.Listbox(list_frame, bg=self.colors["entry_bg"], fg=self.colors["entry_fg"],
                                  selectbackground=self.colors["sel"], selectforeground=self.colors["entry_fg"],
                                  highlightbackground=self.colors["border"], highlightthickness=1, relief="flat",
                                  font=("Segoe UI", 10))
        yscroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=yscroll.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")
        self.listbox.bind("<<ListboxSelect>>", self.on_load_saved)
        # Footer area previously contained load/delete buttons.  These
        # actions are now available via the top menu bar (Library → Save
        # Story, Load Story, Delete Story).  Leaving this space empty
        # provides a cleaner sidebar.  Additional widgets (e.g.
        # indicators or a future quick action) could be added here.
        spacer = tk.Frame(self.sidebar, bg=self.colors["panel"])
        spacer.pack(fill="x", padx=12, pady=(0,12))

    def _build_content(self):
        # Top header inside content area
        title_lbl = tk.Label(self.content, text=f"{APP_NAME}", bg=self.colors["panel"], fg=self.colors["text"], font=("Segoe UI", 22, "bold"))
        subtitle_lbl = tk.Label(self.content, text="Craft magical bedtime stories", bg=self.colors["panel"], fg=self.colors["muted"], font=("Segoe UI", 13))
        title_lbl.grid(row=0, column=0, columnspan=6, sticky="w", padx=14, pady=(14,0))
        subtitle_lbl.grid(row=1, column=0, columnspan=6, sticky="w", padx=14, pady=(0,14))

        # Form fields (topic/name/age) on row2
        row2_y = 2
        # Topic
        self._mk_label(self.content, "Topic / Sujet").grid(row=row2_y, column=0, sticky="w", padx=(14,2))
        self.topic_entry = self._entry(self.content, textvariable=self.topic_var, width=24)
        self.topic_entry.grid(row=row2_y, column=1, sticky="we", padx=(0,10))
        # Child Name
        self._mk_label(self.content, "Child Name / Prénom").grid(row=row2_y, column=2, sticky="w")
        self.name_entry = self._entry(self.content, textvariable=self.name_var, width=18)
        self.name_entry.grid(row=row2_y, column=3, sticky="we", padx=(0,10))
        # Age
        self._mk_label(self.content, "Age / Âge").grid(row=row2_y, column=4, sticky="w")
        self.age_entry = self._entry(self.content, textvariable=self.age_var, width=6)
        self.age_entry.grid(row=row2_y, column=5, sticky="w")

        # Row3: language, tone and length selectors
        row3_y = row2_y + 1
        self._mk_label(self.content, "Language / Langue").grid(row=row3_y, column=0, sticky="w", padx=(14,2), pady=(10,0))
        self.lang_menu = ttk.Combobox(self.content, values=LANGS, textvariable=self.lang_var, width=14, state="readonly", style="Clean.TCombobox")
        self.lang_menu.grid(row=row3_y, column=1, sticky="w", padx=(0,10), pady=(10,0))
        self.lang_menu.bind("<<ComboboxSelected>>", self._on_lang_change)
        # Tone
        self._mk_label(self.content, "Tone / Ton").grid(row=row3_y, column=2, sticky="w", pady=(10,0))
        self.tone_menu = ttk.Combobox(self.content, values=EN_TONES, textvariable=self.tone_var, width=14, state="readonly", style="Clean.TCombobox")
        self.tone_menu.grid(row=row3_y, column=3, sticky="w", padx=(0,10), pady=(10,0))
        # Length
        self._mk_label(self.content, "Length / Longueur").grid(row=row3_y, column=4, sticky="w", pady=(10,0))
        self.length_menu = ttk.Combobox(self.content, values=["Short", "Medium", "Long"], textvariable=self.length_var, width=10, state="readonly", style="Clean.TCombobox")
        self.length_menu.grid(row=row3_y, column=5, sticky="w", pady=(10,0))

        # Row4: options (breathing, moral)
        row4_y = row3_y + 1
        chk_frame = tk.Frame(self.content, bg=self.colors["panel"])
        chk_frame.grid(row=row4_y, column=0, columnspan=6, sticky="w", padx=14, pady=(8,0))
        ttk.Checkbutton(chk_frame, text="Include Breathing / Respiration", variable=self.include_breathing).pack(side="left")
        ttk.Checkbutton(chk_frame, text="Include Moral / Moralité", variable=self.include_moral).pack(side="left", padx=12)

        # Row5: theme (content creator) selection
        row5_y = row4_y + 1
        self._mk_label(self.content, "Theme / Thème").grid(row=row5_y, column=0, sticky="w", padx=(14,2), pady=(10,0))
        # Populate creator names for current language
        # creator_names will be set by _load_creators invoked via _on_lang_change
        self.creator_menu = ttk.Combobox(self.content, values=self.creator_names, textvariable=self.creator_var, width=18, state="readonly", style="Clean.TCombobox")
        self.creator_menu.grid(row=row5_y, column=1, sticky="w", padx=(0,10), pady=(10,0))
        # If there are names, set default
        if self.creator_names:
            self.creator_var.set(self.creator_names[0])

        # Row6: Gemini API Key input
        # Row6: first action row (generate/save/copy)
        row6_y = row5_y + 1
        btn_row1 = tk.Frame(self.content, bg=self.colors["panel"])
        btn_row1.grid(row=row6_y, column=0, columnspan=6, sticky="w", padx=14, pady=(10,2))
        ttk.Button(btn_row1, text="Generate / Générer", command=self.on_generate).pack(side="left")
        ttk.Button(btn_row1, text="Save in App", command=self.on_save_in_app).pack(side="left", padx=6)
        ttk.Button(btn_row1, text="Copy", command=self.on_copy).pack(side="left", padx=6)

        # Row7: second action row (exports)
        row7_y = row6_y + 1
        btn_row2 = tk.Frame(self.content, bg=self.colors["panel"])
        btn_row2.grid(row=row7_y, column=0, columnspan=6, sticky="w", padx=14, pady=(0,6))
        ttk.Button(btn_row2, text="TXT", command=self.on_save_txt).pack(side="left")
        ttk.Button(btn_row2, text="HTML", command=self.on_save_html).pack(side="left", padx=6)
        if REPORTLAB_OK:
            ttk.Button(btn_row2, text="PDF", command=self.on_save_pdf).pack(side="left", padx=6)

        # Row8: preview area with scroll
        row8_y = row7_y + 1
        preview_frame = tk.Frame(self.content, bg=self.colors["panel"])
        preview_frame.grid(row=row8_y, column=0, columnspan=6, sticky="nsew", padx=14, pady=(0,14))
        # Configure row weight for expanding preview
        self.content.grid_rowconfigure(row8_y, weight=1)
        self.content.grid_columnconfigure(1, weight=1)
        self.content.grid_columnconfigure(3, weight=1)
        # Text widget
        self.preview = tk.Text(preview_frame, wrap="word", font=("Segoe UI", 13),
                               bg=self.colors["entry_bg"], fg=self.colors["entry_fg"],
                               insertbackground=self.colors["entry_fg"], relief="flat",
                               highlightbackground=self.colors["border"], highlightthickness=1,
                               padx=14, pady=14)
        yscroll = ttk.Scrollbar(preview_frame, orient="vertical", command=self.preview.yview)
        self.preview.configure(yscrollcommand=yscroll.set)
        self.preview.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")

    # ----------------------- Menu Bar -----------------------
    def _build_menu(self):
        """
        Construct the top menu bar.  This method sets up a persistent
        menubar for the application with library actions, a settings
        placeholder, and an about dialog.  The menu is created once
        during initialization and assigned to the root window via
        ``config(menu=...)``.  Menu callbacks reuse existing
        methods (e.g., ``on_save_in_app``) or call simple dialog
        functions defined below.
        """
        menu_bar = tk.Menu(self)
        # Library menu: save, load, delete, settings
        lib_menu = tk.Menu(menu_bar, tearoff=0)
        lib_menu.add_command(label="Save Story", command=self.on_save_in_app)
        lib_menu.add_command(label="Load Story", command=self.load_selected)
        lib_menu.add_command(label="Delete Story", command=self.delete_selected)
        lib_menu.add_separator()
        lib_menu.add_command(label="Settings…", command=self.on_settings)
        menu_bar.add_cascade(label="Library", menu=lib_menu)
        # Help menu: about
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self.on_about)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        # Attach the menu bar to the window
        self.config(menu=menu_bar)

    # ----------------------- Dialog Callbacks -----------------------
    def on_about(self):
        """
        Display an informational message about the application.  This
        provides credit and contact details for iD01t Productions and
        the developer Guillaume Lessard.  It uses a standard info
        dialog for simplicity.
        """
        message = (
            f"{APP_NAME} v{APP_VERSION}\n"
            "\n"
            "iD01t Productions\n"
            "Guillaume Lessard\n"
            "admin@id01t.store\n"
            "2025"
        )
        messagebox.showinfo("About", message)

    def on_settings(self):
        """
        Open the settings dialog.  This toplevel window allows the
        user to configure application preferences.  Currently it
        contains a field for the Gemini API key, which was removed
        from the main interface.  If the window is already open, it
        will be brought to the front.  Future settings may include
        theme selection and export defaults.
        """
        # If the settings window already exists and is visible, bring it forward
        if hasattr(self, "_settings_win") and self._settings_win.winfo_exists():
            self._settings_win.lift()
            self._settings_win.focus_force()
            return
        # Create a new settings window
        win = tk.Toplevel(self)
        win.title("Settings")
        win.geometry("360x180")
        win.resizable(False, False)
        # Colours consistent with main UI
        win.configure(bg=self.colors["panel"])
        # Gemini API key field
        lbl = tk.Label(win, text="Gemini API Key", bg=self.colors["panel"], fg=self.colors["text"], font=("Segoe UI", 12))
        lbl.pack(anchor="w", padx=16, pady=(16,4))
        entry = tk.Entry(win, textvariable=self.gemini_key_var,
                         bg=self.colors["entry_bg"], fg=self.colors["entry_fg"],
                         insertbackground=self.colors["entry_fg"], relief="flat",
                         highlightbackground=self.colors["border"], highlightcolor=self.colors["sel"],
                         font=("Segoe UI", 12))
        entry.pack(fill="x", padx=16, pady=(0,12))
        # Buttons frame
        btn_frame = tk.Frame(win, bg=self.colors["panel"])
        btn_frame.pack(fill="x", padx=16, pady=(8,16))
        def save_and_close():
            # Simply close after saving; variable is already bound
            win.destroy()
        ttk.Button(btn_frame, text="Save", command=save_and_close).pack(side="right")
        ttk.Button(btn_frame, text="Cancel", command=win.destroy).pack(side="right", padx=8)
        # Keep reference
        self._settings_win = win

    # ----------------------- Creator Management -----------------------
    def _load_creators(self):
        """
        Populate the list of content creator names (themes) for the
        current language based on loaded story_templates.  This
        method should be called whenever the language selection
        changes or when story templates are loaded.  It updates
        self.creator_names and sets the first available name on
        self.creator_var.  If no templates are available for the
        selected language, a single default option will be provided.
        """
        lang = self.lang_var.get()
        names = []
        # Determine names from the loaded templates
        if isinstance(self.story_templates, dict):
            lang_data = self.story_templates.get(lang)
            if isinstance(lang_data, list):
                for item in lang_data:
                    # Each creator dict may supply a human‑readable name
                    names.append(item.get("name", "Theme"))
            elif isinstance(lang_data, dict):
                # Single dictionary: treat as one default theme
                names.append(lang_data.get("name", "Default"))
        # Fallback if no names found
        if not names:
            names = ["Default"]
        self.creator_names = names
        # Update the combobox options if it exists
        if hasattr(self, 'creator_menu') and isinstance(self.creator_menu, ttk.Combobox):
            self.creator_menu["values"] = names
        # Set the variable to the first name
        self.creator_var.set(names[0])

    # Label factory
    def _mk_label(self, parent, text):
        # Use a slightly larger base font for better readability
        return tk.Label(parent, text=text, bg=self.colors["panel"], fg=self.colors["text"], font=("Segoe UI", 14))

    # Entry factory
    def _entry(self, parent, **kwargs):
        e = tk.Entry(parent,
                     bg=self.colors["entry_bg"], fg=self.colors["entry_fg"], insertbackground=self.colors["entry_fg"],
                     relief="flat", highlightthickness=1,
                     highlightbackground=self.colors["border"], highlightcolor=self.colors["sel"],
                     # Larger font for better legibility
                     font=("Segoe UI", 12), **kwargs)
        return e

    # Background loading
    def _load_background(self):
        base = app_dir()
        path = None
        for f in BG_CANDIDATES:
            p = os.path.join(base, f)
            if os.path.exists(p):
                path = p
                break
        if not path:
            return None, None
        try:
            if PIL_OK:
                return Image.open(path).convert("RGBA"), None
            else:
                return None, tk.PhotoImage(file=path)
        except Exception as e:
            print("Background load error:", e)
            return None, None

    # Resize image to cover area without distortion
    def _cover_resize(self, image, target_size):
        tw, th = target_size
        iw, ih = image.size
        scale = max(tw/iw, th/ih)
        nw, nh = int(iw*scale), int(ih*scale)
        img = image.resize((nw, nh), Image.LANCZOS)
        x0 = (nw - tw)//2
        y0 = (nh - th)//2
        return img.crop((x0, y0, x0+tw, y0+th))

    # Update layout on window resize
    def _on_resize(self, event=None):
        # Draw background image
        self.canvas.delete("BG")
        w, h = self.winfo_width(), self.winfo_height()
        if PIL_OK and self.bg_original is not None:
            img = self._cover_resize(self.bg_original, (w, h))
            self.bg_photo = ImageTk.PhotoImage(img)
            self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw", tags="BG")
        elif self.bg_photo is not None:
            self.canvas.create_image((w - self.bg_photo.width())//2, (h - self.bg_photo.height())//2,
                                     image=self.bg_photo, anchor="nw", tags="BG")
        # Position main panels
        sidebar_width = 260
        pad = 14
        gap = 14
        self.sidebar.place(x=pad, y=pad, width=sidebar_width, height=h - 2*pad)
        # Compute content placement based on sidebar width and padding
        content_x = pad + sidebar_width + gap
        content_w = w - (pad + sidebar_width + gap + pad)
        self.content.place(x=content_x, y=pad, width=content_w, height=h - 2*pad)

    # Update tone list based on language selection
    def _on_lang_change(self, *_):
        # Update the tone menu based on selected language
        if self.lang_var.get() == "Français":
            self.tone_menu["values"] = FR_TONES
            if self.tone_var.get() not in FR_TONES:
                self.tone_var.set(FR_TONES[0])
        else:
            self.tone_menu["values"] = EN_TONES
            if self.tone_var.get() not in EN_TONES:
                self.tone_var.set(EN_TONES[0])
        # Reload creators for the selected language
        self._load_creators()

    # Refresh library list from data
    def refresh_library_list(self):
        self.listbox.delete(0, "end")
        for i, item in enumerate(self.library):
            ts = item.get("created_at", "")
            title = item.get("title", "Untitled")
            self.listbox.insert("end", f"{i+1:02d} • {title} • {ts}")

    # Helper to get selected listbox index
    def _selected_index(self):
        sel = self.listbox.curselection()
        if not sel:
            return None
        return sel[0]

    # Listbox selection event: display story
    def on_load_saved(self, *_):
        idx = self._selected_index()
        if idx is None:
            return
        self._set_preview(self.library[idx]["content"])

    # Load selected story into preview
    def load_selected(self):
        idx = self._selected_index()
        if idx is None:
            messagebox.showinfo("Info", "Select a saved story first.")
            return
        self._set_preview(self.library[idx]["content"])

    # Delete selected story from library
    def delete_selected(self):
        idx = self._selected_index()
        if idx is None:
            messagebox.showinfo("Info", "Select a saved story first.")
            return
        if messagebox.askyesno("Delete", "Are you sure you want to delete this story?"):
            del self.library[idx]
            save_library(self.library)
            self.refresh_library_list()

    # Generate new story and display in preview
    def on_generate(self):
        # Determine which creator index corresponds to the selected name
        creator_index = None
        selected_name = self.creator_var.get()
        try:
            creator_index = self.creator_names.index(selected_name)
        except Exception:
            creator_index = None
        story = generate_story(
            topic=self.topic_var.get().strip(),
            child_name=self.name_var.get().strip(),
            age=self.age_var.get().strip(),
            tone=self.tone_var.get(),
            length=self.length_var.get(),
            language=self.lang_var.get(),
            include_breathing=self.include_breathing.get(),
            include_moral=self.include_moral.get(),
            templates=self.story_templates,
            creator_index=creator_index,
        )
        self._set_preview(story)

    # Set preview text
    def _set_preview(self, text):
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", text)

    # Copy preview text to clipboard
    def on_copy(self):
        content = self.preview.get("1.0", "end").strip()
        if not content:
            messagebox.showinfo("Info", "Nothing to copy.")
            return
        self.clipboard_clear()
        self.clipboard_append(content)
        messagebox.showinfo("Copied", "Story copied to clipboard.")

    # Save preview in application library
    def on_save_in_app(self):
        content = self.preview.get("1.0", "end").strip()
        if not content:
            messagebox.showinfo("Info", "Generate a story first.")
            return
        topic = self.topic_var.get().strip() or ("Rêve" if self.lang_var.get() == "Français" else "Dream")
        child = self.name_var.get().strip()
        lang = self.lang_var.get()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        title = f"{('Histoire du soir' if lang == 'Français' else 'Bedtime Story')} — {topic}" + (f" — {child}" if child else "")
        record = {"title": title, "topic": topic, "language": lang, "content": content, "created_at": now}
        self.library.append(record)
        save_library(self.library)
        self.refresh_library_list()
        messagebox.showinfo("Saved", "Story saved in the in-app library.")

    # Save preview to plain text file
    def on_save_txt(self):
        content = self.preview.get("1.0", "end").strip()
        if not content:
            messagebox.showinfo("Info", "Generate a story first.")
            return
        default_name = f"bedtime_story_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=default_name, filetypes=[("Text", "*.txt")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        messagebox.showinfo("Saved", f"Saved: {path}")

    # Save preview to HTML file
    def on_save_html(self):
        content = self.preview.get("1.0", "end").strip()
        if not content:
            messagebox.showinfo("Info", "Generate a story first.")
            return
        topic = self.topic_var.get().strip() or ("Rêve" if self.lang_var.get() == "Français" else "Dream")
        title = f"{'Histoire du soir' if self.lang_var.get() == 'Français' else 'Bedtime Story'} — {topic}"
        html_doc = to_html(title, content, self.lang_var.get())
        default_name = f"bedtime_story_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        path = filedialog.asksaveasfilename(defaultextension=".html", initialfile=default_name, filetypes=[("HTML", "*.html")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(html_doc)
        messagebox.showinfo("Saved", f"Saved: {path}")

    # Save preview to PDF (if reportlab available)
    def on_save_pdf(self):
        if not REPORTLAB_OK:
            messagebox.showerror("Error", "PDF export requires reportlab. Please install reportlab.")
            return
        content = self.preview.get("1.0", "end").strip()
        if not content:
            messagebox.showinfo("Info", "Generate a story first.")
            return
        topic = self.topic_var.get().strip() or ("Rêve" if self.lang_var.get() == "Français" else "Dream")
        title = f"{'Histoire du soir' if self.lang_var.get() == 'Français' else 'Bedtime Story'} — {topic}"
        default_name = f"bedtime_story_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=default_name, filetypes=[("PDF", "*.pdf")])
        if not path:
            return
        try:
            to_pdf(path, title, content, self.lang_var.get())
            messagebox.showinfo("Saved", f"Saved: {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save PDF: {e}")

# Run application
if __name__ == "__main__":
    app = App()
    app.mainloop()