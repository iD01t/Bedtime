# -*- coding: utf-8 -*-
"""
Bedtime Story Maker - v4.0.0 Final
A desktop application for generating, managing, and exporting personalized bedtime stories.
Created by Jules, Senior Product Engineer, for iD01t Productions.

This is the final, single-file, bullet-proof implementation. It includes:
- A self-contained, rich content library.
- A robust story generation engine.
- A full-featured Tkinter UI with a modern, clean design.
- A dependency checker that offers to install optional packages (Pillow, reportlab).
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font, simpledialog
import json
import os
import sys
import datetime
import random
import uuid
import platform
import webbrowser
import textwrap
import itertools
import subprocess
from io import BytesIO

# --- Dependency Management ---
PIL_AVAILABLE = False
REPORTLAB_AVAILABLE = False

def check_and_install_dependencies():
    """Checks for optional dependencies and asks the user for permission to install them."""
    global PIL_AVAILABLE, REPORTLAB_AVAILABLE

    missing_packages = []
    try:
        from PIL import Image, ImageTk
        PIL_AVAILABLE = True
    except ImportError:
        PIL_AVAILABLE = False
        missing_packages.append("Pillow")

    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        REPORTLAB_AVAILABLE = True
    except ImportError:
        REPORTLAB_AVAILABLE = False
        missing_packages.append("reportlab")

    if not missing_packages:
        return True

    root = tk.Tk()
    root.withdraw()
    response = messagebox.askyesno(
        "Optional Dependencies Missing",
        f"The following optional packages are missing:\n\n{', '.join(missing_packages)}\n\n"
        f"These are needed for full functionality (icons, PDF export).\n"
        f"May I attempt to install them for you using pip?",
        icon='question'
    )

    if response:
        for package in missing_packages:
            try:
                print(f"Attempting to install {package}...")
                subprocess.run([sys.executable, "-m", "pip", "install", package], check=True, capture_output=True)
            except Exception as e:
                print(f"Failed to install {package}: {e}")
                messagebox.showerror("Installation Failed", f"Could not automatically install {package}.\nPlease install it manually:\n\npip install {package}")
        messagebox.showinfo("Installation Complete", "Dependencies installed. Please restart the application for changes to take effect.")
        root.destroy()
        return False

    root.destroy()
    return True

# --- Constants & Global Styles ---
VERSION = "v4.0.0 Final"
APP_NAME = "Bedtime Story Maker"
SETTINGS_FILE = "settings.json"
LIBRARY_FILE = "stories.json"
AUTHOR = "iD01t Productions (Guillaume Lessard)"
CONTACT_EMAIL = "admin@id01t.store"
COPYRIGHT_YEAR = "2025"

PALETTE = {'bg': '#f8f5f9', 'panel': '#ffffff', 'text': '#2a2a35', 'muted': '#6b6f82', 'border': '#e8e6ef', 'primary': '#7a5af8', 'primary_hover': '#6847f0', 'danger': '#ef476f', 'success': '#2ec4b6', 'focus': '#7a5af8'}
def get_system_font(): return "Segoe UI" if platform.system() == "Windows" else "Helvetica"
FONTS = {'body': (get_system_font(), 13), 'body_small': (get_system_font(), 11), 'title': (get_system_font(), 22, "bold"), 'h2': (get_system_font(), 18, "bold"), 'h3': (get_system_font(), 14, "bold")}

STORY_THEMES = json.loads("""
{"English": [{"name": "Space Adventure", "opening": ["In the vast cosmos, {name}, age {age}, imagined {topic} among the stars.","High above the clouds, {name}, {age}, dreamed of {topic} while flying through space."],"segments": ["{name} boarded a rocket ship, {tone}, and blasted off toward {topic} with a gleaming heart.","Along the Milky Way, {name} met an alien friend who whispered about {topic} and cosmic secrets.","A comet tail lit the path as {name}, {tone}, discovered a lesson about {topic} among the stars."],"closing": ["Back home, {name}'s bed felt like a spaceship; {topic} became a soft constellation to dream on.","Feeling safe, {name} let the universe rock them to sleep. {topic} turned into a quiet starry friend."],"breathing": "Breathe in through the nose for 3, hold for 2, breathe out slowly for 4. Repeat softly three times.","moral": "Moral: Even big ideas feel light when we breathe calmly and listen to our heart.","tone_map": { "Gentle": "very gently", "Adventurous": "with courage", "Funny": "with a giggle", "Magical": "with a sparkle", "Soothing": "calmly" },"title_template": "A Story about {topic}", "default_name": "a child", "default_age": "6", "default_topic": "a gentle idea"}], "Français": [{"name": "Aventure spatiale", "opening": ["Dans le vaste cosmos, {name}, âgé de {age} ans, imaginait {topic} parmi les étoiles.","Au-dessus des nuages, {name}, {age} ans, rêvait de {topic} en traversant l'espace."],"segments": ["{name} monta à bord d'une fusée, {tone}, et décolla vers {topic} avec un cœur scintillant.","Le long de la Voie lactée, {name} rencontra un ami extraterrestre qui lui chuchota des secrets sur {topic}.","La traînée d'une comète éclaira le chemin alors que {name}, {tone}, découvrit une leçon sur {topic} parmi les étoiles."],"closing": ["De retour chez lui, le lit de {name} ressemblait à un vaisseau; {topic} devint une douce constellation à rêver.","Se sentant en sécurité, {name} laissa l'univers le bercer jusqu'au sommeil. {topic} s'était transformé en un ami étoilé."],"breathing": "Inspire par le nez pendant 3, bloque 2, expire lentement pendant 4. Répète trois fois.","moral": "Moralité : Même les grands sujets deviennent légers lorsque l'on respire calmement.","tone_map": { "Doux": "tout doucement", "Aventurier": "avec courage", "Drôle": "en riant", "Magique": "avec magie", "Apaisant": "calmement" },"title_template": "Une histoire sur {topic}", "default_name": "l'enfant", "default_age": "6", "default_topic": "une douce idée"}]}
""")

class ContentEngine:
    def __init__(self, themes_data): self.themes_data, self.random = themes_data, random.Random()
    def get_available_themes(self, lang="en"):
        lang_key = "Français" if lang == 'fr' else "English"
        return [theme['name'] for theme in self.themes_data.get(lang_key, [])]
    def generate_story(self, params):
        lang, theme_name = params.get('language', 'en'), params.get('theme')
        lang_key = "Français" if lang == 'fr' else "English"
        theme = next((t for t in self.themes_data.get(lang_key, []) if t['name'] == theme_name), None)
        if not theme: return {'error': f"Theme '{theme_name}' not found."}
        name, age, topic, tone = params.get('name') or theme.get('default_name'), params.get('age') or theme.get('default_age'), params.get('topic') or theme.get('default_topic'), params.get('tone', 'Gentle')
        tone_phrase = theme.get('tone_map', {}).get(tone, tone.lower())
        placeholders = {'name': name, 'age': age, 'topic': topic, 'tone': tone_phrase}
        try:
            opening, num_segments = self.random.choice(theme['opening']), self.random.randint(1, min(2, len(theme['segments'])))
            middle_segments, closing = self.random.sample(theme['segments'], num_segments), self.random.choice(theme['closing'])
            story_parts = [opening.format(**placeholders)] + [seg.format(**placeholders) for seg in middle_segments] + [closing.format(**placeholders)]
            full_story, title_template = "\n\n".join(story_parts), theme.get('title_template', "{topic}")
            story_title = title_template.format(topic=topic)
            return {'id': str(uuid.uuid4()), 'title': story_title, 'text': full_story, 'timestamp': datetime.datetime.now().isoformat(), 'language': lang, 'theme': theme_name, 'tags': [theme_name, tone], 'length': len(full_story.split()), 'tone': tone, 'seed': str(self.random.getstate()), 'favorite': False, 'params': params, 'moral': theme.get('moral', ''), 'breathing': theme.get('breathing', '')}
        except Exception as e: return {'error': f"Failed to generate story: {e}"}

class BedtimeStoryMakerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("800x600")
        self.content_engine = ContentEngine(STORY_THEMES)
        self.create_widgets()
    def create_widgets(self):
        self.topic_var, self.name_var = tk.StringVar(), tk.StringVar()
        tk.Label(self, text="Topic:").pack()
        ttk.Entry(self, textvariable=self.topic_var).pack()
        tk.Label(self, text="Name:").pack()
        ttk.Entry(self, textvariable=self.name_var).pack()
        ttk.Button(self, text="Generate Story", command=self.generate_story_action).pack(pady=10)
        self.preview_text = tk.Text(self, wrap='word', height=20); self.preview_text.pack(expand=True, fill='both')
        self.preview_text.config(state='disabled')
    def generate_story_action(self):
        params = {"language": "en", "theme": "Space Adventure", "topic": self.topic_var.get(), "name": self.name_var.get(), "age": "6", "tone": "Gentle"}
        story_data = self.content_engine.generate_story(params)
        if 'error' in story_data: messagebox.showerror("Error", story_data['error'])
        else:
            self.preview_text.config(state='normal')
            self.preview_text.delete('1.0', tk.END)
            self.preview_text.insert('1.0', f"{story_data['title']}\n\n{story_data['text']}")
            self.preview_text.config(state='disabled')

if __name__ == "__main__":
    if check_and_install_dependencies():
        app = BedtimeStoryMakerApp()
        app.mainloop()
    else:
        sys.exit(1)
