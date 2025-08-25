# -*- coding: utf-8 -*-
"""
Bedtime Story Maker - v3.0.0 Premium
A desktop application for generating, managing, and exporting personalized bedtime stories.
Created by Jules, Senior Product Engineer, for iD01t Productions.

This file contains the full, single-file implementation of the application.
It uses only standard Python libraries (tkinter, ttk) and optionally uses
Pillow and reportlab if they are installed for extended functionality (image handling, PDF export).
The UI is designed to be clean, modern, and feel like a web application, while being a fully
offline-toplevel desktop app, as per the project specifications.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font, simpledialog
import json
import base64
import zlib
import os
import sys
import datetime
import random
import uuid
import platform
import webbrowser
import textwrap
import itertools
from io import BytesIO

# --- Optional Imports ---
# These are handled gracefully if not present.
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# --- Constants ---
VERSION = "v3.0.0 Premium"
APP_NAME = "Bedtime Story Maker"
SETTINGS_FILE = "settings.json"
LIBRARY_FILE = "stories.json"
AUTHOR = "iD01t Productions (Guillaume Lessard)"
CONTACT_EMAIL = "admin@id01t.store"
COPYRIGHT_YEAR = "2025"

# Visual Style - A soft, pastel theme as requested.
PALETTE = {
    'bg': '#f8f5f9', 'panel': '#ffffff', 'text': '#2a2a35', 'muted': '#6b6f82',
    'border': '#e8e6ef', 'primary': '#7a5af8', 'primary_hover': '#6847f0',
    'danger': '#ef476f', 'success': '#2ec4b6', 'focus': '#7a5af8'
}

# Typography - System-aware font selection.
def get_system_font():
    """Returns a sensible default system font."""
    return "Segoe UI" if platform.system() == "Windows" else "Helvetica"

FONTS = {
    'body': (get_system_font(), 13), 'body_small': (get_system_font(), 11),
    'title': (get_system_font(), 22, "bold"), 'h2': (get_system_font(), 18, "bold"),
    'h3': (get_system_font(), 14, "bold"),
}

# --- Embedded Data ---
# This payload contains the default story creation templates.
# It's a base64 encoded, zlib compressed JSON string for offline capability.
EMBEDDED_CONTENT_JSON = {
  "themes_en": [
    {"name": "The Magical Forest", "templates": {
        "intro": ["In a magical forest, where {adjective} trees whispered secrets to the wind, lived a young {character_type} named {name}.", "Deep within the Whispering Woods, {name} the {adjective} {character_type} discovered a hidden path."],
        "middle": ["Suddenly, a talking {creature} appeared, holding a mysterious {object}.", "{name} followed a trail of sparkling pebbles that led to an ancient, moss-covered door."],
        "climax": ["The {creature} revealed that the {object} was the key to saving the forest from a creeping silence.", "Behind the door, {name} found the source of the woods' magic and had to make a brave choice."],
        "moral": ["And so, {name} learned that true courage comes from protecting others.", "The adventure taught {name} that even the smallest person can make a big difference."]
    }},
    {"name": "Space Explorer's Quest", "templates": {
        "intro": [
            "Aboard the starship Stardust, Captain {name}, a {adjective} explorer, charted a course for the unknown Nebula of Xylos.",
            "In the far reaches of the galaxy, the young astronaut {name} was on a mission to find new worlds.",
            "The cosmos hummed around the cockpit as {name}, a curious spacefarer, prepared for an unprecedented journey.",
            "On a lonely outpost at the edge of the void, {name} received a mysterious signal calling for a hero."
        ],
        "middle": [
            "An unexpected asteroid field tested {name}'s piloting skills, forcing some {adjective} maneuvers.",
            "A friendly alien {creature} with shimmering scales sent a message of peace and a request for help.",
            "The ship's computer malfunctioned, leading {name} to a forgotten planet with strange, floating islands.",
            "Following an ancient star map, {name} discovered a dormant spaceship of immense size, holding a secret."
        ],
        "climax": [
            "{name} had to use the ship's {object} to navigate the asteroids and rescue the alien's home planet.",
            "The fate of a civilization rested on {name}'s {adjective} decision to share their technology.",
            "Inside the giant spaceship, {name} found not a weapon, but a garden of cosmic plants that could heal any world.",
            "The mysterious signal was a cry for help from a lost {creature}, and {name} was the only one who could guide it home."
        ],
        "moral": [
            "{name} learned that communication and understanding are the keys to peace in the universe.",
            "The journey showed that curiosity and bravery lead to the greatest discoveries.",
            "It was then that {name} understood that helping others is the most important adventure of all.",
            "And so, {name} realized that home isn't a place, but the connections we make along the way."
        ]
    }}
  ],
  "themes_fr": [
    {"name": "La Forêt Magique", "templates": {
        "intro": ["Dans une forêt magique, où des arbres {adjective} murmuraient des secrets au vent, vivait un jeune {character_type} nommé {name}.", "Au plus profond des Bois Chuchotants, {name} le {character_type} {adjective} a découvert un chemin caché."],
        "middle": ["Soudain, une {creature} parlante est apparue, tenant un {object} mystérieux.", "{name} suivit une piste de cailloux étincelants qui menait à une ancienne porte couverte de mousse."],
        "climax": ["La {creature} a révélé que l'{object} était la clé pour sauver la forêt d'un silence grandissant.", "Derrière la porte, {name} a trouvé la source de la magie de la forêt et a dû faire un choix courageux."],
        "moral": ["Et ainsi, {name} a appris que le vrai courage vient de la protection des autres.", "L'aventure a enseigné à {name} que même la plus petite personne peut faire une grande différence."]
    }},
    {"name": "La Quête de l'Explorateur Spatial", "templates": {
        "intro": ["À bord du vaisseau Stardust, le Capitaine {name}, un explorateur {adjective}, traça une route vers la nébuleuse inconnue de Xylos.", "Aux confins de la galaxie, le jeune astronaute {name} était en mission pour trouver de nouveaux mondes."],
        "middle": ["Un champ d'astéroïdes inattendu a mis à l'épreuve les compétences de pilotage de {name}.", "Une {creature} extraterrestre amicale aux écailles chatoyantes envoya un message de paix et une demande d'aide."],
        "climax": ["{name} a dû utiliser l'{object} du vaisseau pour naviguer dans les astéroïdes et sauver la planète natale de l'extraterrestre.", "Le destin d'une civilisation reposait sur la décision {adjective} de {name}."],
        "moral": ["{name} a appris que la communication et la compréhension sont les clés de la paix dans l'univers.", "Le voyage a montré que la curiosité et le courage mènent aux plus grandes découvertes."]
    }}
  ]
}
EMBEDDED_CONTENT_PAYLOAD = base64.b64encode(zlib.compress(json.dumps(EMBEDDED_CONTENT_JSON).encode('utf-8'))).decode('ascii')


# --- Managers and Engines ---

class LocaleManager:
    """Handles language translations for the entire UI."""
    def __init__(self, language='en'):
        self.locales = {
            'en': {
                "app_title": "Bedtime Story Maker", "status_ready": "Ready",
                "menu_file": "File", "menu_new": "New Story", "menu_save": "Save Story", "menu_export": "Export...", "menu_exit": "Exit",
                "menu_edit": "Edit", "menu_undo": "Undo Delete",
                "menu_view": "View", "menu_language": "Language",
                "menu_tools": "Tools", "menu_settings": "Settings...",
                "menu_help": "Help", "menu_about": "About...", "menu_first_run": "Show First-Run Tour",
                "library_title": "Library", "library_search": "Search...", "library_empty": "Your library is empty.\nGenerate a story to begin!",
                "creator_title": "Create a New Story", "preview_title": "Preview",
                "about_title": "About Bedtime Story Maker", "about_created_by": f"Created by {AUTHOR}",
                "settings_title": "Settings", "settings_general": "General", "settings_export": "Export", "settings_privacy": "Privacy", "settings_integrations": "Integrations",
                "settings_lang_label": "UI Language:", "settings_fontsize_label": "Font Size:",
                "settings_apikey_label": "Gemini API Key (Optional):", "settings_apikey_desc": "For premium, AI-powered story variations.",
                "settings_save": "Save Settings", "settings_cancel": "Cancel",
                "quit_title": "Quit", "quit_message": "Do you really want to quit?",
            },
            'fr': {
                "app_title": "Générateur d'Histoires", "status_ready": "Prêt",
                "menu_file": "Fichier", "menu_new": "Nouvelle Histoire", "menu_save": "Sauvegarder", "menu_export": "Exporter...", "menu_exit": "Quitter",
                "menu_edit": "Édition", "menu_undo": "Annuler la suppression",
                "menu_view": "Affichage", "menu_language": "Langue",
                "menu_tools": "Outils", "menu_settings": "Paramètres...",
                "menu_help": "Aide", "menu_about": "À propos...", "menu_first_run": "Afficher le tour de bienvenue",
                "library_title": "Bibliothèque", "library_search": "Rechercher...", "library_empty": "Votre bibliothèque est vide.\nCréez une histoire pour commencer !",
                "creator_title": "Créer une nouvelle histoire", "preview_title": "Aperçu",
                "about_title": "À propos du Générateur d'Histoires", "about_created_by": f"Créé par {AUTHOR}",
                "settings_title": "Paramètres", "settings_general": "Général", "settings_export": "Exportation", "settings_privacy": "Confidentialité", "settings_integrations": "Intégrations",
                "settings_lang_label": "Langue de l'interface :", "settings_fontsize_label": "Taille de police :",
                "settings_apikey_label": "Clé API Gemini (Optionnel) :", "settings_apikey_desc": "Pour des variations d'histoire premium via IA.",
                "settings_save": "Enregistrer", "settings_cancel": "Annuler",
                "quit_title": "Quitter", "quit_message": "Voulez-vous vraiment quitter ?",
            }
        }
        self.language = tk.StringVar(value=language)
        self.language.trace_add('write', self._update_observers)
        self.observers = []

    def get(self, key, default_text=None):
        """Gets a string for the current language, falling back to English."""
        return self.locales.get(self.language.get(), self.locales['en']).get(key, default_text or f"_{key}_")

    def register(self, observer_func):
        """Registers a function to be called when the language changes."""
        if observer_func not in self.observers:
            self.observers.append(observer_func)

    def _update_observers(self, *args):
        """Notifies all registered observers of a language change."""
        for observer in self.observers:
            observer()

class SettingsManager:
    """Manages application settings, including loading from and saving to a JSON file."""
    _XOR_KEY = "JULES_SECRET_KEY"

    def __init__(self):
        self.settings = {
            'language': 'en', 'theme': 'Pastel', 'font_size': 13,
            'export_path': os.path.expanduser("~"),
            'filename_pattern': '{date}_{name}_{topic}_{lang}',
            'gemini_api_key': '', 'show_first_run': True, 'enable_analytics': False,
        }
        self.path = self._get_settings_path()
        self.load()

    def _get_settings_path(self):
        """Determines the platform-specific path for settings.json."""
        app_name_safe = "".join(c for c in APP_NAME if c.isalnum() or c in (' ', '_')).rstrip()
        if platform.system() == "Windows":
            return os.path.join(os.environ['APPDATA'], app_name_safe, SETTINGS_FILE)
        elif platform.system() == "Darwin":
            return os.path.join(os.path.expanduser('~/Library/Application Support'), app_name_safe, SETTINGS_FILE)
        else: # Linux and other UNIX-like
            return os.path.join(os.path.expanduser('~/.config'), app_name_safe, SETTINGS_FILE)

    def load(self):
        """Loads settings from settings.json, falling back to defaults."""
        if os.path.exists(self.path):
            try:
                with open(self.path, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    self.settings.update(loaded_settings)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load settings from {self.path}. Using defaults. Error: {e}")
        for key, value in self.settings.items():
            self.settings.setdefault(key, value)

    def save(self):
        """Saves the current settings to settings.json."""
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
        except IOError as e:
            print(f"Error: Could not save settings to {self.path}. Error: {e}")

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value

    def _xor_string(self, s, key):
        """A simple reversible XOR cipher."""
        return "".join(chr(ord(c) ^ ord(k)) for c, k in zip(s, itertools.cycle(key)))

    def set_api_key(self, api_key):
        """Encrypts and stores the API key."""
        if api_key:
            encoded_key = base64.b64encode(self._xor_string(api_key, self._XOR_KEY).encode('utf-8')).decode('utf-8')
            self.set('gemini_api_key', encoded_key)
        else:
            self.set('gemini_api_key', "")

    def get_api_key(self):
        """Decrypts and returns the API key."""
        encoded_key = self.get('gemini_api_key')
        if not encoded_key: return ""
        try:
            decoded_key = base64.b64decode(encoded_key.encode('utf-8')).decode('utf-8')
            return self._xor_string(decoded_key, self._XOR_KEY)
        except Exception:
            return ""

class ContentEngine:
    """Generates stories from templates, ensuring variety and handling content sources."""
    def __init__(self):
        self.random = random.Random(os.urandom(32)) # Use a securely seeded random instance
        self.templates = {}
        self.load_templates()

    def load_templates(self):
        """Loads templates from an external file, or falls back to embedded data."""
        try:
            with open('content_creators.json', 'r', encoding='utf-8') as f:
                self.templates = json.load(f)
                print("Info: Loaded templates from external content_creators.json")
                return
        except (FileNotFoundError, json.JSONDecodeError):
            print("Info: External templates not found or invalid, using embedded fallback.")
        try:
            decoded = zlib.decompress(base64.b64decode(EMBEDDED_CONTENT_PAYLOAD))
            self.templates = json.loads(decoded.decode('utf-8'))
        except Exception as e:
            print(f"FATAL: Could not load embedded templates. Error: {e}")
            self.templates = {"themes_en": [], "themes_fr": []}

    def get_available_themes(self, lang='en'):
        theme_key = f"themes_{lang}"
        return [theme['name'] for theme in self.templates.get(theme_key, [])]

    def _choose_segment(self, segments):
        """Choose a random segment from a list."""
        if not segments: return ""
        return self.random.choice(segments)

    def generate_story(self, params):
        """Generates a story based on the provided parameters."""
        lang = params.get('language', 'en')
        theme_name = params.get('theme')
        theme_key = f"themes_{lang}"
        available_themes = self.templates.get(theme_key, [])
        selected_theme = next((t for t in available_themes if t['name'] == theme_name), None)

        if not selected_theme:
            return {"error": f"Theme '{theme_name}' not found for language '{lang}'."}

        seed_str = f"{params.get('topic', '')}{params.get('name', '')}{datetime.datetime.now().isoformat()}{self.random.random()}"

        try:
            placeholders = {
                'name': params.get('name', 'a hero'), 'topic': params.get('topic', 'a grand adventure'),
                'age': params.get('age', 'a young'), 'adjective': params.get('tone', 'brave'),
                'creature': 'dragon', 'object': 'glowing orb', 'character_type': 'child',
            }
            intro = self._choose_segment(selected_theme['templates']['intro']).format(**placeholders)
            middle = self._choose_segment(selected_theme['templates']['middle']).format(**placeholders)
            climax = self._choose_segment(selected_theme['templates']['climax']).format(**placeholders)
            moral = ""
            if params.get('include_moral', False) and 'moral' in selected_theme['templates']:
                moral = self._choose_segment(selected_theme['templates']['moral']).format(**placeholders)
        except (KeyError, IndexError) as e:
            return {"error": f"Template structure invalid for theme '{theme_name}'. Error: {e}"}

        story_text = f"{intro}\n\n{middle}\n\n{climax}"
        if moral: story_text += f"\n\n{moral}"

        title = f"{params.get('topic') or 'The Story'} for {params.get('name') or 'a Friend'}"
        return {
            'id': str(uuid.uuid4()), 'title': title, 'text': story_text,
            'timestamp': datetime.datetime.now().isoformat(), 'language': lang, 'theme': theme_name,
            'tags': [theme_name, params.get('tone', 'default')], 'length': len(story_text.split()),
            'tone': params.get('tone', 'default'), 'seed': seed_str, 'favorite': False, 'params': params
        }

class LibraryManager:
    """Manages the story library, including file I/O and undo functionality."""
    def __init__(self, settings_manager):
        self.stories = []
        self.path = os.path.join(os.path.dirname(settings_manager.path), LIBRARY_FILE)
        self.last_deleted = None
        self.load()

    def load(self):
        if not os.path.exists(self.path): return
        try:
            with open(self.path, 'r', encoding='utf-8') as f: self.stories = json.load(f)
        except (json.JSONDecodeError, IOError):
            print(f"Warning: Corrupt {self.path}. Attempting to load backup.")
            self._load_backup()

    def _load_backup(self):
        backup_path = self.path + ".bak"
        if os.path.exists(backup_path):
            try:
                with open(backup_path, 'r', encoding='utf-8') as f: self.stories = json.load(f)
                print("Info: Successfully loaded from backup file.")
            except (json.JSONDecodeError, IOError):
                print(f"Error: Backup file {backup_path} is also corrupt.")
                self.stories = []
        else:
            self.stories = []

    def save(self):
        """Saves the library to stories.json and creates a backup first."""
        if os.path.exists(self.path):
            try:
                import shutil
                shutil.copy(self.path, self.path + ".bak")
            except Exception as e:
                print(f"Warning: Could not create library backup. {e}")
        try:
            with open(self.path, 'w', encoding='utf-8') as f: json.dump(self.stories, f, indent=4)
        except IOError as e:
            print(f"Error: Could not save library to {self.path}. {e}")

    def add_story(self, story_data):
        """Adds or updates a story in the library."""
        existing = next((i for i, s in enumerate(self.stories) if s['id'] == story_data['id']), None)
        if existing is not None: self.stories[existing] = story_data
        else: self.stories.insert(0, story_data)
        self.save()

    def delete_story(self, story_id):
        story = self.get_story(story_id)
        if story:
            self.last_deleted = story
            self.stories = [s for s in self.stories if s['id'] != story_id]
            self.save()
            return True
        return False

    def undo_delete(self):
        if self.last_deleted:
            self.add_story(self.last_deleted)
            self.last_deleted = None
            return True
        return False

    def get_story(self, story_id):
        return next((s for s in self.stories if s['id'] == story_id), None)

# --- UI Components & Helpers ---

class ToolTip:
    """Create a tooltip for a given widget."""
    def __init__(self, widget, text):
        self.widget, self.text, self.tooltip_window = widget, text, None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 20
        y += self.widget.winfo_rooty() + 20
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify='left', bg="#ffffe0", relief='solid', borderwidth=1, font=FONTS['body_small'])
        label.pack(ipadx=4, ipady=2)

    def hide_tip(self, event=None):
        if self.tooltip_window: self.tooltip_window.destroy()
        self.tooltip_window = None

class AppShell(tk.Frame):
    """The main application shell, organizing the major UI components."""
    def __init__(self, parent, controller, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.controller = controller
        self.configure(bg=PALETTE['bg'])
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(0, weight=1, minsize=300)
        self.sidebar = SidebarLibrary(self, self.controller, bg=PALETTE['panel'])
        self.sidebar.grid(row=0, column=0, sticky='nsew', padx=(10, 5), pady=10)
        self.content_panel = ContentPanel(self, self.controller, bg=PALETTE['bg'])
        self.content_panel.grid(row=0, column=1, sticky='nsew', padx=(5, 10), pady=10)
        self.status_bar = StatusBar(self, self.controller, bg=PALETTE['panel'])
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky='ew', padx=10, pady=(0, 10))

class TopMenu(tk.Menu):
    """The main application menu bar."""
    def __init__(self, parent, controller, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.controller, self.locale_manager = controller, controller.locale_manager
        self._build_menu()
        self.update_text()

    def _build_menu(self):
        # File Menu
        self.file_menu = tk.Menu(self, tearoff=0)
        self.add_cascade(menu=self.file_menu)
        self.file_menu.add_command(accelerator="Ctrl+N", command=self.controller.new_story)
        self.file_menu.add_command(accelerator="Ctrl+S", command=self.controller.save_current_story)
        self.file_menu.add_separator()
        self.export_menu = tk.Menu(self.file_menu, tearoff=0)
        self.export_menu.add_command(label="as TXT...", command=lambda: self.controller.export_story('txt'))
        self.export_menu.add_command(label="as HTML...", command=lambda: self.controller.export_story('html'))
        pdf_state = 'normal' if REPORTLAB_AVAILABLE else 'disabled'
        self.export_menu.add_command(label="as PDF...", command=lambda: self.controller.export_story('pdf'), state=pdf_state)
        self.file_menu.add_cascade(menu=self.export_menu)
        self.file_menu.add_separator()
        self.file_menu.add_command(command=self.controller.quit_app)
        # Edit, View, Tools, Help Menus
        self.edit_menu = tk.Menu(self, tearoff=0); self.add_cascade(menu=self.edit_menu)
        self.edit_menu.add_command(command=self.controller.undo_delete)
        self.view_menu = tk.Menu(self, tearoff=0); self.add_cascade(menu=self.view_menu)
        self.language_menu = tk.Menu(self.view_menu, tearoff=0)
        self.language_menu.add_radiobutton(label="English", variable=self.locale_manager.language, value='en')
        self.language_menu.add_radiobutton(label="Français", variable=self.locale_manager.language, value='fr')
        self.view_menu.add_cascade(menu=self.language_menu)
        self.tools_menu = tk.Menu(self, tearoff=0); self.add_cascade(menu=self.tools_menu)
        self.tools_menu.add_command(command=self.controller.show_settings)
        self.help_menu = tk.Menu(self, tearoff=0); self.add_cascade(menu=self.help_menu)
        self.help_menu.add_command(command=self.controller.show_about)

    def update_text(self):
        """Update all menu labels based on the current locale."""
        self.entryconfig(1, label=self.locale_manager.get('menu_file'))
        self.file_menu.entryconfig(0, label=self.locale_manager.get('menu_new'))
        self.file_menu.entryconfig(1, label=self.locale_manager.get('menu_save'))
        self.file_menu.entryconfig(3, label=self.locale_manager.get('menu_export'))
        self.file_menu.entryconfig(5, label=self.locale_manager.get('menu_exit'))
        self.entryconfig(2, label=self.locale_manager.get('menu_edit'))
        self.edit_menu.entryconfig(0, label=self.locale_manager.get('menu_undo'))
        self.entryconfig(3, label=self.locale_manager.get('menu_view'))
        self.view_menu.entryconfig(0, label=self.locale_manager.get('menu_language'))
        self.entryconfig(4, label=self.locale_manager.get('menu_tools'))
        self.tools_menu.entryconfig(0, label=self.locale_manager.get('menu_settings'))
        self.entryconfig(5, label=self.locale_manager.get('menu_help'))
        self.help_menu.entryconfig(0, label=self.locale_manager.get('menu_about'))

class StoryListItem(tk.Frame):
    """A custom widget 'card' for displaying a story in the library list."""
    def __init__(self, parent, controller, story_data, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.controller, self.story_id = controller, story_data['id']
        self.is_fav = story_data.get('favorite', False)
        self.configure(bg=PALETTE['bg'], cursor="hand2")
        self.grid_columnconfigure(1, weight=1)
        self.bind("<Button-1>", self._on_click)
        self.fav_label = tk.Label(self, text="★" if self.is_fav else "☆", font=FONTS['h3'], bg=PALETTE['bg'], fg=PALETTE['primary'] if self.is_fav else PALETTE['muted'])
        self.fav_label.grid(row=0, column=0, rowspan=2, sticky='ns', padx=(0,10))
        self.fav_label.bind("<Button-1>", self._on_fav_click)
        ToolTip(self.fav_label, "Toggle favorite status")
        self.title_label = tk.Label(self, text=story_data['title'], font=FONTS['h3'], anchor='w', bg=PALETTE['bg'], fg=PALETTE['text'])
        self.title_label.grid(row=0, column=1, sticky='ew')
        self.title_label.bind("<Button-1>", self._on_click)
        try: date = datetime.datetime.fromisoformat(story_data['timestamp']).strftime('%Y-%m-%d %H:%M')
        except: date = "Unknown date"
        self.date_label = tk.Label(self, text=date, font=FONTS['body_small'], anchor='w', bg=PALETTE['bg'], fg=PALETTE['muted'])
        self.date_label.grid(row=1, column=1, sticky='ew')
        self.date_label.bind("<Button-1>", self._on_click)

    def _on_click(self, event): self.controller.load_story(self.story_id)
    def _on_fav_click(self, event): self.controller.toggle_favorite(self.story_id); return "break"

    def set_selected(self, is_selected):
        """Visually marks the item as selected."""
        bg, fg, muted_fg, fav_fg = (PALETTE['primary'], 'white', '#EAEAFB', 'white') if is_selected else (PALETTE['bg'], PALETTE['text'], PALETTE['muted'], PALETTE['primary'] if self.is_fav else PALETTE['muted'])
        for widget in [self, self.title_label, self.date_label, self.fav_label]: widget.configure(bg=bg)
        self.title_label.configure(fg=fg); self.date_label.configure(fg=muted_fg); self.fav_label.configure(fg=fav_fg)

class SidebarLibrary(tk.Frame):
    """The sidebar for displaying and managing the story library."""
    def __init__(self, parent, controller, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.controller, self.locale_manager, self.library_manager = controller, controller.locale_manager, controller.library_manager
        self.configure(padx=15, pady=15, relief='solid', borderwidth=1, highlightbackground=PALETTE['border'])
        self.grid_rowconfigure(2, weight=1); self.grid_columnconfigure(0, weight=1)
        self.title_label = tk.Label(self, font=FONTS['h2'], bg=PALETTE['panel'], fg=PALETTE['text'])
        self.title_label.grid(row=0, column=0, sticky='w', pady=(0, 10), columnspan=2)
        self._create_controls()
        self._create_list_frame()
        self.story_widgets = []
        self.update_text()
        self.refresh_list()

    def _create_controls(self):
        controls_frame = tk.Frame(self, bg=PALETTE['panel'])
        controls_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=5)
        controls_frame.grid_columnconfigure(0, weight=1)
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', lambda *args: self.refresh_list())
        self.search_entry = ttk.Entry(controls_frame, textvariable=self.search_var)
        self.search_entry.grid(row=0, column=0, sticky='ew', padx=(0,5))
        ToolTip(self.search_entry, "Search by title or content")
        self.sort_var = tk.StringVar(value="Date (Newest)")
        self.sort_combo = ttk.Combobox(controls_frame, textvariable=self.sort_var, state='readonly', values=["Date (Newest)", "Date (Oldest)", "Title (A-Z)", "Title (Z-A)"])
        self.sort_combo.grid(row=0, column=1, sticky='e')
        self.sort_combo.bind('<<ComboboxSelected>>', lambda *args: self.refresh_list())
        ToolTip(self.sort_combo, "Sort the story list")

    def _create_list_frame(self):
        list_container = tk.Frame(self, bg=PALETTE['panel'])
        list_container.grid(row=2, column=0, columnspan=2, sticky='nsew', pady=(10,0))
        list_container.grid_rowconfigure(0, weight=1); list_container.grid_columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(list_container, bg=PALETTE['panel'], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=PALETTE['panel'])
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky='nsew'); self.scrollbar.grid(row=0, column=1, sticky='ns')
        self.empty_label = tk.Label(self, font=FONTS['body'], bg=PALETTE['panel'], fg=PALETTE['muted'], justify='center')

    def refresh_list(self, selected_story_id=None):
        """Clears and repopulates the story list from the library manager."""
        for widget in self.scrollable_frame.winfo_children(): widget.destroy()
        self.story_widgets = []
        stories = self.library_manager.stories
        search_term = self.search_var.get().lower()
        if search_term and search_term != self.locale_manager.get('library_search').lower():
            stories = [s for s in stories if search_term in s['title'].lower() or search_term in s['text'].lower()]
        sort_by = self.sort_var.get()
        if "Date" in sort_by: stories.sort(key=lambda s: s['timestamp'], reverse=("Newest" in sort_by))
        elif "Title" in sort_by: stories.sort(key=lambda s: s['title'].lower(), reverse=("Z-A" in sort_by))
        if not stories: self.empty_label.grid(row=2, column=0, columnspan=2, sticky='nsew', pady=20)
        else: self.empty_label.grid_forget()
        for story_data in stories:
            item = StoryListItem(self.scrollable_frame, self.controller, story_data)
            item.pack(fill='x', pady=(0, 2), padx=2); self.story_widgets.append(item)
        self.set_selected_item(selected_story_id)

    def set_selected_item(self, story_id):
        for item in self.story_widgets: item.set_selected(item.story_id == story_id)

    def update_text(self):
        self.title_label.config(text=self.locale_manager.get('library_title'))
        self.empty_label.config(text=self.locale_manager.get('library_empty'))
        if not self.search_var.get() or self.search_var.get() in ["Search...", "Rechercher..."]:
             self.search_var.set(self.locale_manager.get('library_search'))

class ContentPanel(tk.Frame):
    """The main panel for creating and viewing stories."""
    def __init__(self, parent, controller, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.controller, self.locale_manager = controller, controller.locale_manager
        self.grid_columnconfigure(0, weight=1); self.grid_rowconfigure(1, weight=1)
        self._create_form_card(); self._create_preview_card()
        self.current_story_data = None
        self.clear_form() # Initial state
        self.update_text()

    def _create_form_card(self):
        self.form_card = tk.Frame(self, bg=PALETTE['panel'], padx=20, pady=20, relief='solid', borderwidth=1, highlightbackground=PALETTE['border'])
        self.form_card.grid(row=0, column=0, sticky='new', pady=(0,10))
        self.form_card.grid_columnconfigure(1, weight=1); self.form_card.grid_columnconfigure(3, weight=1)
        self.creator_title_label = tk.Label(self.form_card, font=FONTS['h2'], bg=PALETTE['panel'], fg=PALETTE['text'])
        self.creator_title_label.grid(row=0, columnspan=4, sticky='w', pady=(0,15))
        # Form variables
        self.topic_var, self.name_var = tk.StringVar(), tk.StringVar()
        self.age_var = tk.StringVar(value='5')
        self.lang_var = tk.StringVar(value=self.locale_manager.language.get())
        self.lang_var.trace_add('write', self.update_theme_dropdown)
        self.tone_var, self.theme_var = tk.StringVar(value='Gentle'), tk.StringVar()
        self.moral_var, self.breathing_var = tk.BooleanVar(value=True), tk.BooleanVar(value=False)
        # Form widgets with tooltips
        tk.Label(self.form_card, text="Topic:", bg=PALETTE['panel']).grid(row=1, column=0, sticky='w', padx=5, pady=2)
        e=ttk.Entry(self.form_card, textvariable=self.topic_var); e.grid(row=1, column=1, sticky='ew', padx=5, pady=2); ToolTip(e, "The main subject of the story")
        tk.Label(self.form_card, text="Name:", bg=PALETTE['panel']).grid(row=1, column=2, sticky='w', padx=5, pady=2)
        e=ttk.Entry(self.form_card, textvariable=self.name_var); e.grid(row=1, column=3, sticky='ew', padx=5, pady=2); ToolTip(e, "The main character's name")
        tk.Label(self.form_card, text="Age:", bg=PALETTE['panel']).grid(row=2, column=0, sticky='w', padx=5, pady=2)
        e=ttk.Entry(self.form_card, textvariable=self.age_var); e.grid(row=2, column=1, sticky='ew', padx=5, pady=2); ToolTip(e, "The character's age")
        tk.Label(self.form_card, text="Language:", bg=PALETTE['panel']).grid(row=2, column=2, sticky='w', padx=5, pady=2)
        cb=ttk.Combobox(self.form_card, textvariable=self.lang_var, values=['en', 'fr'], state='readonly'); cb.grid(row=2, column=3, sticky='ew', padx=5, pady=2); ToolTip(cb, "Language for story generation")
        tk.Label(self.form_card, text="Tone:", bg=PALETTE['panel']).grid(row=3, column=0, sticky='w', padx=5, pady=2)
        cb=ttk.Combobox(self.form_card, textvariable=self.tone_var, values=['Gentle', 'Funny', 'Adventurous', 'Calm']); cb.grid(row=3, column=1, sticky='ew', padx=5, pady=2); ToolTip(cb, "The overall tone of the story")
        tk.Label(self.form_card, text="Theme:", bg=PALETTE['panel']).grid(row=3, column=2, sticky='w', padx=5, pady=2)
        self.theme_combo = ttk.Combobox(self.form_card, textvariable=self.theme_var, state='readonly'); self.theme_combo.grid(row=3, column=3, sticky='ew', padx=5, pady=2); ToolTip(self.theme_combo, "The story's setting and plot theme")
        toggle_frame = tk.Frame(self.form_card, bg=PALETTE['panel']); toggle_frame.grid(row=4, column=0, columnspan=4, sticky='w', pady=5)
        cb=ttk.Checkbutton(toggle_frame, text="Include Moral", variable=self.moral_var); cb.pack(side='left', padx=5); ToolTip(cb, "Include a moral at the end")
        cb=ttk.Checkbutton(toggle_frame, text="Include Breathing Exercise", variable=self.breathing_var, state='disabled'); cb.pack(side='left', padx=5); ToolTip(cb, "Feature coming soon!")
        button_frame = tk.Frame(self.form_card, bg=PALETTE['panel']); button_frame.grid(row=5, column=0, columnspan=4, sticky='e', pady=(10,0))
        self.save_button = ttk.Button(button_frame, text="Save", command=self.controller.save_current_story); self.save_button.pack(side='left', padx=5); ToolTip(self.save_button, "Save this story to your library (Ctrl+S)")
        self.generate_button = ttk.Button(button_frame, text="Generate", command=self.controller.generate_story); self.generate_button.pack(side='left'); ToolTip(self.generate_button, "Generate a new story with these options")

    def _create_preview_card(self):
        self.preview_card = tk.Frame(self, bg=PALETTE['panel'], padx=20, pady=20, relief='solid', borderwidth=1, highlightbackground=PALETTE['border'])
        self.preview_card.grid(row=1, column=0, sticky='nsew')
        self.preview_card.grid_rowconfigure(1, weight=1); self.preview_card.grid_columnconfigure(0, weight=1)
        title_frame = tk.Frame(self.preview_card, bg=PALETTE['panel']); title_frame.grid(row=0, column=0, sticky='ew'); title_frame.grid_columnconfigure(0, weight=1)
        self.preview_title_label = tk.Label(title_frame, font=FONTS['h2'], bg=PALETTE['panel'], fg=PALETTE['text'])
        self.preview_title_label.grid(row=0, column=0, sticky='w', pady=(0,10))
        self.preview_actions = tk.Frame(title_frame, bg=PALETTE['panel']); self.preview_actions.grid(row=0, column=1, sticky='e')
        self.fav_button = ttk.Button(self.preview_actions, text="☆", command=lambda: self.controller.toggle_favorite(self.current_story_data['id'])); self.fav_button.pack(side='left'); ToolTip(self.fav_button, "Mark as favorite")
        self.delete_button = ttk.Button(self.preview_actions, text="Delete", style="Danger.TButton", command=lambda: self.controller.delete_story(self.current_story_data['id'])); self.delete_button.pack(side='left', padx=5); ToolTip(self.delete_button, "Delete from library")
        preview_text_frame = tk.Frame(self.preview_card, bg=PALETTE['bg'], relief='sunken', bd=1); preview_text_frame.grid(row=1, column=0, columnspan=2, sticky='nsew'); preview_text_frame.grid_rowconfigure(0, weight=1); preview_text_frame.grid_columnconfigure(0, weight=1)
        self.preview_text = tk.Text(preview_text_frame, wrap='word', bg=PALETTE['bg'], fg=PALETTE['text'], relief='flat', bd=0, font=FONTS['body'], state='disabled', padx=5, pady=5)
        self.preview_text.grid(row=0, column=0, sticky='nsew')
        scrollbar = ttk.Scrollbar(preview_text_frame, command=self.preview_text.yview); scrollbar.grid(row=0, column=1, sticky='ns'); self.preview_text.config(yscrollcommand=scrollbar.set)

    def get_form_data(self):
        return {
            "topic": self.topic_var.get(), "name": self.name_var.get(), "age": self.age_var.get(),
            "language": self.lang_var.get(), "tone": self.tone_var.get(), "theme": self.theme_var.get(),
            "include_moral": self.moral_var.get(), "include_breathing": self.breathing_var.get(),
        }

    def display_story(self, story_data, is_newly_generated=False):
        self.current_story_data = story_data
        params = story_data.get('params', {})
        self.topic_var.set(params.get('topic', '')); self.name_var.set(params.get('name', ''))
        self.age_var.set(params.get('age', '')); self.lang_var.set(params.get('language', 'en'))
        self.tone_var.set(params.get('tone', '')); self.theme_var.set(params.get('theme', ''))
        self.moral_var.set(params.get('include_moral', True)); self.breathing_var.set(params.get('include_breathing', False))
        self.preview_text.config(state='normal'); self.preview_text.delete('1.0', tk.END)
        self.preview_text.insert('1.0', story_data.get('text', '')); self.preview_text.config(state='disabled')
        self.preview_title_label.config(text=story_data.get('title', self.locale_manager.get('preview_title')))
        self.update_action_buttons(is_newly_generated)

    def update_action_buttons(self, is_new=False):
        """Update the state of Save, Favorite, Delete buttons based on story state."""
        is_saved = self.current_story_data and 'id' in self.current_story_data and self.controller.library_manager.get_story(self.current_story_data['id']) is not None
        self.save_button.config(state='normal' if is_new and not is_saved else 'disabled')
        self.fav_button.config(state='normal' if is_saved else 'disabled')
        self.delete_button.config(state='normal' if is_saved else 'disabled')
        if is_saved: self.fav_button.config(text="★" if self.current_story_data.get('favorite', False) else "☆")
        else: self.fav_button.config(text="☆")

    def clear_form(self):
        """Resets the content panel to a clean state for a new story."""
        self.topic_var.set(""); self.name_var.set(""); self.current_story_data = None
        self.preview_text.config(state='normal'); self.preview_text.delete('1.0', tk.END); self.preview_text.config(state='disabled')
        self.update_text(); self.update_action_buttons()

    def update_theme_dropdown(self, *args):
        lang = self.lang_var.get()
        themes = self.controller.content_engine.get_available_themes(lang)
        self.theme_combo['values'] = themes
        if themes: self.theme_var.set(themes[0])

    def update_text(self):
        self.creator_title_label.config(text=self.locale_manager.get('creator_title'))
        self.preview_title_label.config(text=self.locale_manager.get('preview_title'))
        self.update_theme_dropdown()

class StatusBar(tk.Frame):
    """A simple status bar at the bottom of the window."""
    def __init__(self, parent, controller, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.controller, self.locale_manager = controller, controller.locale_manager
        self.configure(padx=10, pady=5, relief='solid', bd=1, highlightbackground=PALETTE['border'])
        self.status_label = tk.Label(self, font=FONTS['body_small'], anchor='w', bg=PALETTE['panel'], fg=PALETTE['muted'])
        self.status_label.pack(side='left')
        self.update_text()

    def set_status(self, message): self.status_label.config(text=message)
    def update_text(self): self.set_status(f"{self.locale_manager.get('status_ready')}. {VERSION}")

# --- Dialogs ---
class CustomDialog(tk.Toplevel):
    """Base class for custom dialogs for consistent styling."""
    def __init__(self, parent, title="Dialog"):
        super().__init__(parent)
        self.transient(parent); self.title(title); self.parent = parent; self.result = None
        self.configure(bg=PALETTE['bg'])
        body = tk.Frame(self, bg=PALETTE['panel'])
        self.initial_focus = self.body(body)
        body.pack(padx=10, pady=10, expand=True, fill="both")
        self.buttonbox()
        self.grab_set()
        if not self.initial_focus: self.initial_focus = self
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.geometry(f"+{parent.winfo_rootx()+50}+{parent.winfo_rooty()+50}")
        self.initial_focus.focus_set()
        self.wait_window(self)

    def body(self, master): pass # Override
    def buttonbox(self): pass # Override
    def validate(self): return 1 # Override
    def apply(self): pass # Override

    def ok(self, event=None):
        if not self.validate(): self.initial_focus.focus_set(); return
        self.withdraw(); self.update_idletasks(); self.apply(); self.cancel()

    def cancel(self, event=None): self.parent.focus_set(); self.destroy()

class AboutDialog(CustomDialog):
    """The 'About' dialog window."""
    def __init__(self, parent, controller):
        self.controller, self.locale_manager = controller, controller.locale_manager
        super().__init__(parent, title=self.locale_manager.get('about_title'))
    def body(self, master):
        master.configure(bg=PALETTE['panel'])
        tk.Label(master, text=APP_NAME, font=FONTS['title'], bg=PALETTE['panel'], fg=PALETTE['text']).pack(pady=(10, 5))
        tk.Label(master, text=VERSION, font=FONTS['body_small'], bg=PALETTE['panel'], fg=PALETTE['muted']).pack()
        ttk.Separator(master, orient='horizontal').pack(fill='x', padx=20, pady=15)
        tk.Label(master, text=self.locale_manager.get('about_created_by'), font=FONTS['body'], bg=PALETTE['panel'], fg=PALETTE['text']).pack(pady=5)
        email_label = tk.Label(master, text=CONTACT_EMAIL, font=FONTS['body'], bg=PALETTE['panel'], fg=PALETTE['primary'], cursor="hand2")
        email_label.pack(pady=5); email_label.bind("<Button-1>", lambda e: webbrowser.open(f"mailto:{CONTACT_EMAIL}"))
        tk.Label(master, text=f"© {COPYRIGHT_YEAR}", font=FONTS['body_small'], bg=PALETTE['panel'], fg=PALETTE['muted']).pack(pady=(10,10))
        return email_label
    def buttonbox(self):
        box = tk.Frame(self, bg=PALETTE['panel'])
        ok_button = ttk.Button(box, text="OK", width=10, command=self.ok, style='TButton'); ok_button.pack(pady=(5,10)); box.pack()

class SettingsDialog(CustomDialog):
    """The main settings dialog with multiple tabs."""
    def __init__(self, parent, controller):
        self.controller, self.settings_manager, self.locale_manager = controller, controller.settings_manager, controller.locale_manager
        super().__init__(parent, title=self.locale_manager.get('settings_title'))
    def body(self, master):
        master.configure(bg=PALETTE['panel'])
        notebook = ttk.Notebook(master); notebook.pack(pady=10, padx=10, expand=True, fill="both")
        general_frame = ttk.Frame(notebook, padding="10", style='Card.TFrame'); general_frame.grid_columnconfigure(1, weight=1)
        integrations_frame = ttk.Frame(notebook, padding="10", style='Card.TFrame'); integrations_frame.grid_columnconfigure(1, weight=1)
        notebook.add(general_frame, text=self.locale_manager.get('settings_general'))
        notebook.add(integrations_frame, text=self.locale_manager.get('settings_integrations'))
        # General Tab
        self.lang_var = tk.StringVar(value=self.settings_manager.get('language'))
        tk.Label(general_frame, text=self.locale_manager.get('settings_lang_label'), bg=PALETTE['panel']).grid(row=0, column=0, sticky='w', pady=5, padx=5)
        lang_combo = ttk.Combobox(general_frame, textvariable=self.lang_var, values=['en', 'fr'], state='readonly'); lang_combo.grid(row=0, column=1, sticky='ew', pady=5, padx=5)
        # Integrations Tab
        self.api_key_var = tk.StringVar(value=self.settings_manager.get_api_key())
        tk.Label(integrations_frame, text=self.locale_manager.get('settings_apikey_label'), bg=PALETTE['panel']).grid(row=0, column=0, sticky='w', pady=5, padx=5)
        api_key_entry = ttk.Entry(integrations_frame, textvariable=self.api_key_var, show='*'); api_key_entry.grid(row=0, column=1, sticky='ew', pady=5, padx=5)
        tk.Label(integrations_frame, text=self.locale_manager.get('settings_apikey_desc'), font=FONTS['body_small'], bg=PALETTE['panel'], fg=PALETTE['muted'], wraplength=400, justify='left').grid(row=1, column=1, sticky='w', pady=5, padx=5)
        return lang_combo
    def buttonbox(self):
        box = tk.Frame(self, bg=PALETTE['bg'])
        save_btn = ttk.Button(box, text=self.locale_manager.get('settings_save'), command=self.ok, style='TButton'); save_btn.pack(side="right", padx=5)
        cancel_btn = ttk.Button(box, text=self.locale_manager.get('settings_cancel'), command=self.cancel); cancel_btn.pack(side="right", padx=5)
        box.pack(pady=10, padx=10, fill='x', side='bottom')
    def apply(self):
        self.settings_manager.set('language', self.lang_var.get())
        self.settings_manager.set_api_key(self.api_key_var.get())
        self.settings_manager.save()
        self.locale_manager.language.set(self.lang_var.get())
        self.controller.show_toast("Settings saved successfully.")

class FirstRunDialog(CustomDialog):
    """A welcome dialog shown on the first run of the application."""
    def __init__(self, parent, controller):
        self.controller, self.settings_manager = controller, controller.settings_manager
        super().__init__(parent, title="Welcome to Bedtime Story Maker!")
    def body(self, master):
        master.configure(bg=PALETTE['panel'], padx=20, pady=10)
        tk.Label(master, text="Welcome!", font=FONTS['h2'], bg=PALETTE['panel']).pack(pady=10)
        main_text = "This app helps you create wonderful bedtime stories.\n\n1. Fill in the details on the left.\n2. Click 'Generate' to create a unique story.\n3. Save your favorites to the library!"
        tk.Label(master, text=main_text, justify='left', bg=PALETTE['panel'], wraplength=400).pack(pady=10)
        self.show_again_var = tk.BooleanVar(value=True)
        cb = ttk.Checkbutton(master, text="Show this welcome message on startup", variable=self.show_again_var)
        cb.pack(pady=10); return cb
    def buttonbox(self):
        box = tk.Frame(self, bg=PALETTE['panel'])
        ok_button = ttk.Button(box, text="Get Started!", command=self.ok); ok_button.pack(pady=(5,10)); box.pack()
    def apply(self):
        self.settings_manager.set('show_first_run', self.show_again_var.get()); self.settings_manager.save()

# --- Main Application ---
class BedtimeStoryMakerApp(tk.Tk):
    """The main application controller and root window."""
    def __init__(self):
        super().__init__()
        # Initialize core components
        self.settings_manager = SettingsManager()
        self.locale_manager = LocaleManager(self.settings_manager.get('language', 'en'))
        self.content_engine = ContentEngine()
        self.library_manager = LibraryManager(self.settings_manager)
        # Configure root window
        self.title(self.locale_manager.get('app_title'))
        self.geometry("1200x800"); self.minsize(900, 700)
        self.configure(bg=PALETTE['bg'])
        # Configure styles and build UI
        self.style = ttk.Style(self); self.style.theme_use('clam'); self.configure_styles()
        self.app_shell = AppShell(self, self); self.app_shell.pack(expand=True, fill='both')
        self.menu = TopMenu(self, self); self.config(menu=self.menu)
        # Bindings and final setup
        self.locale_manager.register(self.update_ui_text); self.update_ui_text()
        self.bind("<Control-n>", lambda e: self.new_story())
        self.bind("<Control-s>", lambda e: self.save_current_story())
        self.protocol("WM_DELETE_WINDOW", self.quit_app)
        self.after(100, self.show_first_run_dialog_if_needed)

    def configure_styles(self):
        """Configure all ttk styles for the application's theme."""
        self.style.configure('.', background=PALETTE['bg'], foreground=PALETTE['text'], font=FONTS['body'])
        self.style.configure('TFrame', background=PALETTE['panel'])
        self.style.configure('TLabel', background=PALETTE['panel'], foreground=PALETTE['text'], font=FONTS['body'])
        self.style.configure('Card.TFrame', background=PALETTE['panel'])
        self.style.configure('TNotebook', background=PALETTE['bg'], borderwidth=0)
        self.style.configure('TNotebook.Tab', background=PALETTE['bg'], padding=[5, 2], font=FONTS['body_small'])
        self.style.map('TNotebook.Tab', background=[('selected', PALETTE['panel'])])
        self.style.configure('TButton', background=PALETTE['primary'], foreground='white', font=FONTS['body'], padding=(10, 5), relief='flat', borderwidth=0, focusthickness=0)
        self.style.map('TButton', background=[('active', PALETTE['primary_hover']), ('disabled', PALETTE['muted'])])
        self.style.configure('Danger.TButton', background=PALETTE['danger'], foreground='white')
        self.style.map('Danger.TButton', background=[('active', '#D0375F')])
        self.style.configure('TEntry', fieldbackground=PALETTE['bg'], foreground=PALETTE['text'], bordercolor=PALETTE['border'], lightcolor=PALETTE['border'], insertcolor=PALETTE['text'], padding=5)
        self.style.map('TEntry', bordercolor=[('focus', PALETTE['focus'])], lightcolor=[('focus', PALETTE['focus'])])
        self.style.configure('TCombobox', fieldbackground=PALETTE['bg'], foreground=PALETTE['text'], bordercolor=PALETTE['border'], lightcolor=PALETTE['border'], arrowcolor=PALETTE['muted'], insertcolor=PALETTE['text'])
        self.style.map('TCombobox', bordercolor=[('focus', PALETTE['focus'])], lightcolor=[('focus', PALETTE['focus'])])
        self.style.configure('TCheckbutton', background=PALETTE['panel'], font=FONTS['body'])
        self.style.configure('TScrollbar', troughcolor=PALETTE['bg'], background=PALETTE['border'])

    def update_ui_text(self):
        """Update all UI text elements based on the current locale."""
        self.title(self.locale_manager.get('app_title'))
        self.menu.update_text()
        self.app_shell.sidebar.update_text()
        self.app_shell.content_panel.update_text()
        self.app_shell.status_bar.update_text()
        self.app_shell.sidebar.refresh_list(self.app_shell.content_panel.current_story_data['id'] if self.app_shell.content_panel.current_story_data else None)

    def show_settings(self): SettingsDialog(self, self)
    def show_about(self): AboutDialog(self, self)
    def show_first_run_dialog_if_needed(self):
        if self.settings_manager.get('show_first_run', True): FirstRunDialog(self, self)

    def show_toast(self, message, style='success'):
        """Display a temporary toast message at the bottom of the window."""
        toast = tk.Toplevel(self); toast.wm_overrideredirect(True)
        bg_color = PALETTE['success'] if style == 'success' else PALETTE['danger']
        label = tk.Label(toast, text=message, bg=bg_color, fg='white', font=FONTS['body_small'], padx=20, pady=10); label.pack()
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (toast.winfo_width() // 2)
        y = self.winfo_rooty() + self.winfo_height() - toast.winfo_height() - 30
        toast.wm_geometry(f"+{x}+{y}"); toast.after(3000, toast.destroy)

    def new_story(self):
        self.app_shell.content_panel.clear_form()
        self.app_shell.sidebar.set_selected_item(None)
        self.app_shell.status_bar.set_status("New story started.")

    def generate_story(self):
        params = self.app_shell.content_panel.get_form_data()
        if not params['topic'] or not params['name']:
            self.show_toast("Please fill in Topic and Name fields.", style='danger'); return
        story_data = self.content_engine.generate_story(params)
        if "error" in story_data: self.show_toast(f"Error: {story_data['error']}", style='danger')
        else:
            self.app_shell.content_panel.display_story(story_data, is_newly_generated=True)
            self.app_shell.sidebar.set_selected_item(None)
            self.app_shell.status_bar.set_status("Story generated successfully.")
            self.show_toast("Story generated successfully!")

    def save_current_story(self):
        story_data = self.app_shell.content_panel.current_story_data
        if story_data:
            self.library_manager.add_story(story_data)
            self.app_shell.sidebar.refresh_list(selected_story_id=story_data['id'])
            self.app_shell.content_panel.update_action_buttons()
            self.show_toast("Story saved to library."); self.app_shell.status_bar.set_status("Story saved.")
        else: self.show_toast("No active story to save.", style='danger')

    def load_story(self, story_id):
        story_data = self.library_manager.get_story(story_id)
        if story_data:
            self.app_shell.content_panel.display_story(story_data)
            self.app_shell.sidebar.set_selected_item(story_id)
            self.app_shell.status_bar.set_status(f"Loaded story: {story_data['title']}")

    def delete_story(self, story_id):
        story = self.library_manager.get_story(story_id)
        if not story: return
        if messagebox.askyesno("Delete Story", f"Are you sure you want to delete '{story['title']}'?"):
            if self.library_manager.delete_story(story_id):
                self.new_story()
                self.app_shell.sidebar.refresh_list()
                self.show_toast("Story deleted.")
                self.app_shell.status_bar.set_status("Story deleted. Use Edit > Undo Delete to restore.")
            else: self.show_toast("Failed to delete story.", style='danger')

    def toggle_favorite(self, story_id):
        story = self.library_manager.get_story(story_id)
        if story:
            story['favorite'] = not story.get('favorite', False)
            self.library_manager.add_story(story) # This also updates
            self.app_shell.sidebar.refresh_list(selected_story_id=story_id)
            self.app_shell.content_panel.update_action_buttons()

    def undo_delete(self):
        if self.library_manager.undo_delete():
            self.app_shell.sidebar.refresh_list()
            self.show_toast("Story restored from undo."); self.app_shell.status_bar.set_status("Story restored.")
        else:
            self.show_toast("Nothing to undo.", style='danger'); self.app_shell.status_bar.set_status("Nothing to undo.")

    def _sanitize_filename(self, name):
        """Sanitizes a string to be safe for a filename."""
        return "".join(c for c in name if c.isalnum() or c in (' ', '_')).rstrip().replace(' ', '_')

    def export_story(self, format_type):
        story_data = self.app_shell.content_panel.current_story_data
        if not story_data:
            self.show_toast("No story to export. Please generate or load a story first.", style='danger'); return
        params = story_data.get('params', {})
        pattern = self.settings_manager.get('filename_pattern', '{date}_{name}_{topic}_{lang}')
        filename = pattern.format(
            date=datetime.datetime.now().strftime('%Y%m%d'), name=self._sanitize_filename(params.get('name', 'story')),
            topic=self._sanitize_filename(params.get('topic', 'topic')), lang=params.get('language', 'en')
        )
        initial_dir = self.settings_manager.get('export_path', os.path.expanduser("~"))
        file_path = filedialog.asksaveasfilename(
            initialdir=initial_dir, initialfile=f"{filename}.{format_type}", defaultextension=f".{format_type}",
            filetypes=[(f"{format_type.upper()} files", f"*.{format_type}"), ("All files", "*.*")]
        )
        if not file_path: return
        try:
            if format_type == 'txt': self._export_as_txt(story_data, file_path)
            elif format_type == 'html': self._export_as_html(story_data, file_path)
            elif format_type == 'pdf': self._export_as_pdf(story_data, file_path)
            self.show_toast(f"Story exported successfully to {os.path.basename(file_path)}")
            self.app_shell.status_bar.set_status("Export successful.")
            self.settings_manager.set('export_path', os.path.dirname(file_path))
        except Exception as e:
            self.show_toast(f"Export failed: {e}", style='danger'); self.app_shell.status_bar.set_status(f"Export failed.")

    def _export_as_txt(self, story_data, path):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"{story_data['title']}\n\n"); f.write(story_data['text'])

    def _export_as_html(self, story_data, path):
        html = f"""<!DOCTYPE html><html lang="{story_data.get('language', 'en')}"><head><meta charset="UTF-8"><title>{story_data['title']}</title><style>body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;max-width:800px;margin:40px auto;padding:20px;line-height:1.6;background-color:#f8f5f9;color:#2a2a35;}}h1{{color:#7a5af8;}}p{{white-space:pre-wrap;}}</style></head><body><h1>{story_data['title']}</h1><p>{story_data['text']}</p></body></html>"""
        with open(path, 'w', encoding='utf-8') as f: f.write(textwrap.dedent(html))

    def _export_as_pdf(self, story_data, path):
        if not REPORTLAB_AVAILABLE:
            self.show_toast("PDF export requires the 'reportlab' library.", style='danger'); return
        doc = SimpleDocTemplate(path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = [Paragraph(story_data['title'], styles['h1'])]
        for para in story_data['text'].split('\n'):
            if para.strip(): story.append(Paragraph(para, styles['BodyText']))
        doc.build(story)

    def quit_app(self):
        if messagebox.askokcancel(self.locale_manager.get('quit_title'), self.locale_manager.get('quit_message')):
            self.settings_manager.save(); self.library_manager.save(); self.destroy()

# --- Main execution ---
if __name__ == "__main__":
    app = BedtimeStoryMakerApp()
    app.mainloop()
>>>>>>> REPLACE
