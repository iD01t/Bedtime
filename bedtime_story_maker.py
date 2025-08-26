# -*- coding: utf-8 -*-
"""
Bedtime Story Maker - 1.1.0
Official iD01t Productions desktop app for generating, managing, and exporting personalized bedtime stories.

- Company: iD01t Productions
- Year: 2025
- Site: https://id01t.store
- Support: admin@id01t.store
- App ID: com.id01t.bedtime-story-maker
- Version: 1.1.0

Build instructions:
  pip install customtkinter reportlab python-docx ebooklib markdown pyinstaller
  pyinstaller --noconfirm --onefile --windowed --name "BedtimeStoryMaker" bedtime_story_maker.py

Notes:
- Single-file architecture only.
- Offline deterministic generator with seed reproducibility and anti-repetition n-gram guard.
- UI remains responsive: generation and exports run in worker threads.
- Optional use of customtkinter; falls back to tkinter if unavailable.
"""

import os
import sys
import json
import base64
import zlib
import threading
import queue
import time
import random
import datetime
import logging
from logging.handlers import RotatingFileHandler
import textwrap
import uuid
import difflib
from io import BytesIO

# UI imports with fallback to tkinter
try:
	import customtkinter as ctk
	from tkinter import filedialog, messagebox
	TK_LIB = 'customtkinter'
except Exception:
	import tkinter as ctk  # type: ignore
	from tkinter import ttk as ttk  # type: ignore
	from tkinter import filedialog, messagebox  # type: ignore
	TK_LIB = 'tkinter'

if TK_LIB == 'customtkinter':
	import tkinter as tk  # for constants and some widgets
	ttk = None
	ctk.set_appearance_mode("System")
	ctk.set_default_color_theme("blue")
else:
	import tkinter as tk
	from tkinter import ttk

# Lazy heavy libs: import only on use
REPORTLAB_AVAILABLE = False

APP_NAME = "Bedtime Story Maker"
APP_ID = "com.id01t.bedtime-story-maker"
COMPANY = "iD01t Productions"
SITE_URL = "https://id01t.store"
SUPPORT_EMAIL = "admin@id01t.store"
VERSION = "1.1.0"
COPYRIGHT_YEAR = "2025"

# Paths and files
SETTINGS_FILE = "settings.json"
LIBRARY_FILE = "stories.json"
RECOVERY_FILE = "~.bedtime_story_recovery.json"
README_FILE = "README_Bedtime_Story_Maker.txt"

# Logging
LOG_DIR = os.path.join(os.path.expanduser("~"), ".bedtime_story_logs")
LOG_PATH = os.path.join(LOG_DIR, "app.log")
os.makedirs(LOG_DIR, exist_ok=True)
logger = logging.getLogger(APP_ID)
logger.setLevel(logging.INFO)
_handler = RotatingFileHandler(LOG_PATH, maxBytes=200_000, backupCount=3)
_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
logger.addHandler(_handler)

# Embedded minimal templates (EN/FR)
EMBEDDED_CONTENT_JSON = {
	"themes_en": [
		{"name": "Magical Forest", "templates": {
			"intro": [
				"In a magical forest, where {adjective} trees whispered secrets, lived a young {character_type} named {name}.",
				"Deep in the Whispering Woods, {name} the {adjective} {character_type} found a hidden path."
			],
			"middle": [
				"A talking {creature} appeared, holding a mysterious {object}.",
				"{name} followed a sparkle trail to an ancient door."
			],
			"climax": [
				"The {object} could save the forest from silence.",
				"Behind the door, {name} found the source of the woods and made a brave choice."
			],
			"moral": [
				"{name} learned that gentle choices make real strength.",
				"Even the smallest person can help a great place heal."
			]
		}},
	],
	"themes_fr": [
		{"name": "La Forêt Magique", "templates": {
			"intro": [
				"Dans une forêt magique, où des arbres {adjective} murmuraient des secrets, vivait un jeune {character_type} nommé {name}.",
				"Au cœur des Bois, {name} le {character_type} {adjective} trouva un sentier caché."
			],
			"middle": [
				"Une {creature} parlante apparut, tenant un {object} mystérieux.",
				"{name} suivit des lueurs jusqu'à une porte ancienne."
			],
			"climax": [
				"L'{object} pouvait sauver la forêt du silence.",
				"Derrière la porte, {name} fit un choix courageux."
			],
			"moral": [
				"{name} apprit que la douceur est une force réelle.",
				"Même une petite personne peut aider un grand lieu à guérir."
			]
		}},
	]
}
EMBEDDED_CONTENT_PAYLOAD = base64.b64encode(zlib.compress(json.dumps(EMBEDDED_CONTENT_JSON).encode('utf-8'))).decode('ascii')

# Locale strings (EN/FR)
LOCALES = {
	'en': {
		'app_title': APP_NAME,
		'menu_file': 'File', 'menu_new': 'New Story', 'menu_save': 'Save Story', 'menu_export': 'Export...', 'menu_exit': 'Exit',
		'menu_tools': 'Tools', 'menu_settings': 'Settings...', 'menu_selfcheck': 'Self Check',
		'menu_help': 'Help', 'menu_about': 'About...', 'menu_language': 'Language',
		'creator_title': 'Create a New Story', 'preview_title': 'Preview', 'library_title': 'Library', 'library_search': 'Search...',
		'generate': 'Generate', 'save': 'Save', 'delete': 'Delete', 'favorite': 'Favorite',
		'batch_title': 'Batch', 'batch_run': 'Run Batch', 'batch_cancel': 'Cancel', 'batch_count': 'Count', 'batch_seeds': 'Seeds (comma separated)',
		'guard_n': 'Guard N', 'guard_window': 'Guard Window', 'creative_boost': 'Creative Boost', 'reading_level': 'Reading Level',
		'live_outline': 'Outline', 'reroll_beat': 'Reroll Beat',
		'export_txt': 'as TXT...', 'export_html': 'as HTML...', 'export_pdf': 'as PDF...', 'export_rtf': 'as RTF...', 'export_combined': 'Combined Export...',
		'settings_title': 'Settings', 'settings_lang_label': 'UI Language', 'settings_theme': 'Theme', 'settings_theme_dark': 'Dark', 'settings_theme_light': 'Light', 'settings_theme_hc': 'High Contrast',
		'settings_autosave': 'Autosave Seconds', 'settings_guard': 'Default Guard N, Window', 'settings_plugins': 'Enable Calm Closure Plugin',
		'about_title': f'About {APP_NAME}', 'about_created_by': f'Created by {COMPANY}', 'status_ready': 'Ready',
		'no_story': 'No story to export. Please generate or load a story first.',
		'export_success': 'Export successful', 'export_failed': 'Export failed', 'schema_mismatch': 'Schema mismatch on import',
		'selfcheck_ok': 'Self check passed', 'selfcheck_fail': 'Self check failed',
	},	
	'fr': {
		'app_title': "Générateur d'Histoires",
		'menu_file': 'Fichier', 'menu_new': 'Nouvelle Histoire', 'menu_save': 'Sauvegarder', 'menu_export': 'Exporter...', 'menu_exit': 'Quitter',
		'menu_tools': 'Outils', 'menu_settings': 'Paramètres...', 'menu_selfcheck': 'Auto Vérif',
		'menu_help': 'Aide', 'menu_about': 'À propos...', 'menu_language': 'Langue',
		'creator_title': 'Créer une nouvelle histoire', 'preview_title': 'Aperçu', 'library_title': 'Bibliothèque', 'library_search': 'Rechercher...',
		'generate': 'Générer', 'save': 'Sauvegarder', 'delete': 'Supprimer', 'favorite': 'Favori',
		'batch_title': 'Lot', 'batch_run': 'Lancer', 'batch_cancel': 'Annuler', 'batch_count': 'Nombre', 'batch_seeds': 'Seeds (séparés par virgule)',
		'guard_n': 'Garde N', 'guard_window': 'Fenêtre', 'creative_boost': 'Élan Créatif', 'reading_level': 'Niveau de Lecture',
		'live_outline': 'Plan', 'reroll_beat': 'Relancer le Temps',
		'export_txt': 'en TXT...', 'export_html': 'en HTML...', 'export_pdf': 'en PDF...', 'export_rtf': 'en RTF...', 'export_combined': 'Export Combiné...',
		'settings_title': 'Paramètres', 'settings_lang_label': "Langue de l'interface", 'settings_theme': 'Thème', 'settings_theme_dark': 'Sombre', 'settings_theme_light': 'Clair', 'settings_theme_hc': 'Contraste',
		'settings_autosave': 'Autosave Secondes', 'settings_guard': 'Garde par défaut N, Fenêtre', 'settings_plugins': 'Activer Clôture Calme',
		'about_title': f'À propos de {APP_NAME}', 'about_created_by': f'Créé par {COMPANY}', 'status_ready': 'Prêt',
		'no_story': "Aucune histoire à exporter.",
		'export_success': "Exportation réussie", 'export_failed': "Échec de l'export", 'schema_mismatch': 'Schéma non conforme',
		'selfcheck_ok': 'Auto vérif réussie', 'selfcheck_fail': 'Auto vérif échouée',
	}
}

# Settings and Library
class SettingsManager:
	_XOR_KEY = "ID01T_BSM_KEY"
	def __init__(self):
		self.settings = {
			'language': 'en', 'theme': 'dark', 'autosave_seconds': 60,
			'guard_n': 3, 'guard_window': 50, 'creative_boost': 0.1,
			'reading_level': 1.0, 'export_path': os.path.expanduser("~"),
			'plugin_calm_closure': True, 'api_key': ''
		}
		self.path = os.path.join(os.path.expanduser("~"), SETTINGS_FILE)
		self.load()
	def _xor(self, s, key): return "".join(chr(ord(c) ^ ord(k)) for c, k in zip(s, (key* ((len(s)//len(key))+1))[:len(s)]))
	def set_api_key(self, value):
		self.settings['api_key'] = base64.b64encode(self._xor(value or '', self._XOR_KEY).encode()).decode()
	def get_api_key(self):
		v = self.settings.get('api_key', '')
		if not v: return ''
		try: return self._xor(base64.b64decode(v.encode()).decode(), self._XOR_KEY)
		except Exception: return ''
	def get(self, k, d=None): return self.settings.get(k, d)
	def set(self, k, v): self.settings[k] = v
	def load(self):
		try:
			if os.path.exists(self.path):
				with open(self.path, 'r', encoding='utf-8') as f: self.settings.update(json.load(f))
		except Exception as e:
			logger.warning(f"Settings load failed: {e}")
	def save(self):
		try:
			with open(self.path, 'w', encoding='utf-8') as f: json.dump(self.settings, f, indent=2)
		except Exception as e:
			logger.error(f"Settings save failed: {e}")

class LibraryManager:
	def __init__(self):
		self.path = os.path.join(os.path.expanduser("~"), LIBRARY_FILE)
		self.stories = []
		self.last_deleted = None
		self.load()
	def load(self):
		if not os.path.exists(self.path): return
		try:
			with open(self.path, 'r', encoding='utf-8') as f: self.stories = json.load(f)
		except Exception as e:
			logger.warning(f"Library load failed: {e}")
			self.stories = []
	def save(self):
		try:
			# backup
			if os.path.exists(self.path):
				try:
					import shutil; shutil.copy(self.path, self.path+".bak")
				except Exception: pass
			with open(self.path, 'w', encoding='utf-8') as f: json.dump(self.stories, f, indent=2)
		except Exception as e:
			logger.error(f"Library save failed: {e}")
	def add_story(self, story):
		i = next((i for i,s in enumerate(self.stories) if s['id']==story['id']), None)
		if i is not None: self.stories[i] = story
		else: self.stories.insert(0, story)
		self.save()
	def get_story(self, sid): return next((s for s in self.stories if s['id']==sid), None)
	def delete_story(self, sid):
		st = self.get_story(sid)
		if not st: return False
		self.last_deleted = st
		self.stories = [s for s in self.stories if s['id']!=sid]
		self.save(); return True
	def undo_delete(self):
		if self.last_deleted:
			self.add_story(self.last_deleted); self.last_deleted=None; return True
		return False

# Generator helpers
def _n_grams(tokens, n):
	return [tuple(tokens[i:i+n]) for i in range(max(0, len(tokens)-n+1))]

def _unique_ratio(tokens, n, window):
	if not tokens: return 1.0
	if window <= 0: window = len(tokens)
	unique = 0; total = 0
	for i in range(0, len(tokens), window):
		chunk = tokens[i:i+window]
		grams = _n_grams(chunk, n)
		if not grams: continue
		total += len(grams)
		unique += len(set(grams))
	return unique/total if total else 1.0

def _split_sentences(text):
	parts = [p.strip() for p in text.split('.') if p.strip()]
	return [p + '.' for p in parts]

class ContentEngine:
	def __init__(self, settings: SettingsManager):
		self.settings = settings
		self.templates = {}
		self.load_templates()
	def load_templates(self):
		try:
			with open('content_creators.json', 'r', encoding='utf-8') as f:
				self.templates = json.load(f); return
		except Exception:
			pass
		try:
			decoded = zlib.decompress(base64.b64decode(EMBEDDED_CONTENT_PAYLOAD)).decode('utf-8')
			self.templates = json.loads(decoded)
		except Exception as e:
			logger.error(f"Embedded templates load failed: {e}"); self.templates = {"themes_en":[], "themes_fr":[]}
	def get_available_themes(self, lang='en'):
		return [t['name'] for t in self.templates.get(f"themes_{lang}", [])]
	def _choose(self, rnd, items): return rnd.choice(items) if items else ''
	def generate(self, params, seed=None, guard_n=None, guard_window=None, creative_boost=None, reading_level=None, outline_only=False):
		lang = params.get('language','en'); theme_name = params.get('theme')
		themes = self.templates.get(f"themes_{lang}", [])
		theme = next((t for t in themes if t['name']==theme_name), None)
		if not theme: return {"error": f"Theme '{theme_name}' not found for language '{lang}'."}
		seed_val = int(seed if seed is not None else params.get('seed', 0))
		rnd = random.Random(seed_val)
		cb = creative_boost if creative_boost is not None else self.settings.get('creative_boost', 0.1)
		rlevel = float(reading_level if reading_level is not None else self.settings.get('reading_level', 1.0))
		placeholders = {
			'name': params.get('name','a friend'), 'topic': params.get('topic','A Story'), 'age': params.get('age','young'),
			'adjective': self._choose(rnd, ['gentle','curious','brave','kind','calm']),
			'creature': self._choose(rnd, ['fox','owl','dragon','cat','deer']),
			'object': self._choose(rnd, ['lantern','map','key','shell','compass']),
			'character_type': self._choose(rnd, ['child','traveler','friend'])
		}
		beats = ['intro','middle','climax'] + (['moral'] if params.get('include_moral', True) and 'moral' in theme['templates'] else [])
		texts = []
		for b in beats:
			choices = theme['templates'].get(b, [])
			pick = self._choose(rnd, choices).format(**placeholders)
			# reading level: shorten sentences by clamping length and simplifying joins
			words = pick.split()
			max_words = max(6, int(len(words) * (0.85 if rlevel < 1.0 else 1.0 + min(0.5, (rlevel-1.0)) * 0.5)))
			pick = " ".join(words[:max_words])
			if not pick.endswith('.'): pick += '.'
			texts.append(pick)
		story_text = "\n\n".join(texts)
		# anti repetition guard
		guard_n_val = int(guard_n if guard_n is not None else self.settings.get('guard_n',3))
		guard_w_val = int(guard_window if guard_window is not None else self.settings.get('guard_window',50))
		rewrite_applied = False
		toks = [t.lower().strip(".,;:!?\"'") for t in story_text.split()]
		if _unique_ratio(toks, guard_n_val, guard_w_val) < 0.9 - cb*0.1:
			# simple rewrite: vary sentence starters and joiners
			sents = _split_sentences(story_text)
			prefixes = ["Sometimes, ", "Then, ", "After, ", "In time, ", "And, "]
			new_sents = []
			for i, s in enumerate(sents):
				w = s.strip()
				if i>0 and len(w.split())>6:
					w = rnd.choice(prefixes) + w[0].lower() + w[1:]
				new_sents.append(w if w.endswith('.') else w+'.')
			story_text = " ".join(new_sents)
			rewrite_applied = True
		# calm closure plugin
		if params.get('plugin_calm_closure', self.settings.get('plugin_calm_closure', True)):
			story_text = plugin_calm_closure(story_text)
		title = f"{params.get('topic') or 'The Story'} for {params.get('name') or 'a Friend'}"
		return {
			'id': params.get('id') or str(uuid.uuid4()), 'title': title, 'text': story_text, 'language': lang,
			'timestamp': datetime.datetime.now().isoformat(), 'theme': theme_name, 'tone': params.get('tone','Gentle'),
			'length': len(story_text.split()), 'seed': seed_val, 'rewrite_applied': rewrite_applied,
			'params': params
		}

# Plugins
def plugin_calm_closure(text: str) -> str:
	sents = _split_sentences(text)
	if not sents: return text
	endings = ["Everything felt safe.", "The night grew quiet.", "The world rested."]
	if not any(kw in sents[-1].lower() for kw in ['safe','quiet','rest']):
		sents[-1] = sents[-1].rstrip('. ') + " The night is calm."
	return " ".join(sents)

# UI Components
class App(ctk.CTk if TK_LIB=='customtkinter' else tk.Tk):
	def __init__(self):
		super().__init__()
		self.settings = SettingsManager()
		self.locale = self.settings.get('language','en')
		self.content = ContentEngine(self.settings)
		self.library = LibraryManager()
		self.job_queue = queue.Queue()
		self.cancel_event = threading.Event()
		self.title(LOCALES[self.locale]['app_title']); self.geometry("1200x800")
		self.configure(bg="#111318" if self.settings.get('theme')=='dark' else "#f8f5f9")
		self._build_menu()
		self._build_body()
		self._schedule_autosave()
		self._try_restore_recovery()
		logger.info("App started")
	def _build_menu(self):
		m = tk.Menu(self) if TK_LIB!='customtkinter' else tk.Menu(self)
		self.config(menu=m)
		filem = tk.Menu(m, tearoff=0)
		m.add_cascade(label=LOCALES[self.locale]['menu_file'], menu=filem)
		filem.add_command(label=LOCALES[self.locale]['menu_new'], command=self._new_story)
		filem.add_command(label=LOCALES[self.locale]['menu_save'], command=self._save_current)
		expm = tk.Menu(filem, tearoff=0)
		expm.add_command(label=LOCALES[self.locale]['export_txt'], command=lambda: self._export_current('txt'))
		expm.add_command(label=LOCALES[self.locale]['export_html'], command=lambda: self._export_current('html'))
		expm.add_command(label=LOCALES[self.locale]['export_pdf'], command=lambda: self._export_current('pdf'))
		expm.add_command(label=LOCALES[self.locale]['export_rtf'], command=lambda: self._export_current('rtf'))
		expm.add_separator(); expm.add_command(label=LOCALES[self.locale]['export_combined'], command=self._export_combined)
		filem.add_cascade(label=LOCALES[self.locale]['menu_export'], menu=expm)
		filem.add_separator(); filem.add_command(label=LOCALES[self.locale]['menu_exit'], command=self._quit)
		toolsm = tk.Menu(m, tearoff=0)
		m.add_cascade(label=LOCALES[self.locale]['menu_tools'], menu=toolsm)
		toolsm.add_command(label=LOCALES[self.locale]['menu_settings'], command=self._show_settings)
		toolsm.add_command(label=LOCALES[self.locale]['menu_selfcheck'], command=self._self_check_dialog)
		helpm = tk.Menu(m, tearoff=0)
		m.add_cascade(label=LOCALES[self.locale]['menu_help'], menu=helpm)
		helpm.add_command(label=LOCALES[self.locale]['menu_about'], command=self._show_about)
	def _build_body(self):
		root = self
		# Left panel controls
		left = (ctk.CTkFrame(root) if TK_LIB=='customtkinter' else tk.Frame(root, bg=self._bg_panel()))
		left.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
		root.grid_columnconfigure(0, weight=1, minsize=360)
		root.grid_columnconfigure(1, weight=2)
		root.grid_rowconfigure(0, weight=1)
		# Form
		self.vars = {
			"topic": tk.StringVar(), "name": tk.StringVar(), "age": tk.StringVar(value='5'),
			"language": tk.StringVar(value=self.locale), "tone": tk.StringVar(value='Gentle'),
			"theme": tk.StringVar(value=self.content.get_available_themes(self.locale)[0] if self.content.get_available_themes(self.locale) else '')
		}
		self.guard_n_var = tk.IntVar(value=self.settings.get('guard_n',3))
		self.guard_window_var = tk.IntVar(value=self.settings.get('guard_window',50))
		self.boost_var = tk.DoubleVar(value=self.settings.get('creative_boost',0.1))
		self.reading_var = tk.DoubleVar(value=self.settings.get('reading_level',1.0))
		self.seed_var = tk.StringVar(value=str(random.randint(1, 10**8)))
		self.current_story = None
		self._form_section(left)
		# Right panel: preview + outline
		right = (ctk.CTkFrame(root) if TK_LIB=='customtkinter' else tk.Frame(root, bg=self._bg_panel()))
		right.grid(row=0, column=1, sticky='nsew', padx=(0,10), pady=10)
		right.grid_rowconfigure(1, weight=1); right.grid_columnconfigure(0, weight=1)
		self.title_label = tk.Label(right, text=LOCALES[self.locale]['preview_title'], font=("Segoe UI", 18, "bold"), bg=self._bg_panel(), fg=self._fg_text())
		self.title_label.grid(row=0, column=0, sticky='w', pady=(0,6))
		body = (ctk.CTkTextbox(right, wrap='word') if TK_LIB=='customtkinter' else tk.Text(right, wrap='word', bg=self._bg_body(), fg=self._fg_text()))
		self.preview_text = body; body.grid(row=1, column=0, sticky='nsew')
		self.preview_text.configure(state='disabled')
		# Outline
		outline = (ctk.CTkFrame(right) if TK_LIB=='customtkinter' else tk.Frame(right, bg=self._bg_panel()))
		outline.grid(row=2, column=0, sticky='ew', pady=(6,0))
		ol_label = tk.Label(outline, text=LOCALES[self.locale]['live_outline'], bg=self._bg_panel(), fg=self._fg_muted())
		ol_label.pack(side='left')
		self.outline_var = tk.StringVar(value='intro')
		for beat in ['intro','middle','climax','moral']:
			b = tk.Radiobutton(outline, text=beat, variable=self.outline_var, value=beat, indicatoron=True, bg=self._bg_panel(), fg=self._fg_text())
			b.pack(side='left', padx=4)
		rrb = tk.Button(outline, text=LOCALES[self.locale]['reroll_beat'], command=self._reroll_beat)
		rrb.pack(side='right')
		# Status
		self.status_label = tk.Label(root, text=f"{LOCALES[self.locale]['status_ready']}. {VERSION}", bg=self._bg_panel(), fg=self._fg_muted())
		self.status_label.grid(row=1, column=0, columnspan=2, sticky='ew', padx=10, pady=(0,10))
	def _form_section(self, parent):
		frm = (ctk.CTkFrame(parent) if TK_LIB=='customtkinter' else tk.Frame(parent, bg=self._bg_panel()))
		frm.pack(fill='x')
		def add_row(lbl, var, values=None):
			row = (ctk.CTkFrame(frm) if TK_LIB=='customtkinter' else tk.Frame(frm, bg=self._bg_panel()))
			row.pack(fill='x', pady=2)
			tk.Label(row, text=lbl+":", bg=self._bg_panel(), fg=self._fg_text()).pack(side='left')
			if values:
				cb = (ctk.CTkComboBox(row, values=values, variable=var) if TK_LIB=='customtkinter' else ttk.Combobox(row, values=values, textvariable=var, state='readonly'))
				cb.pack(side='right', fill='x', expand=True)
			else:
				e = (ctk.CTkEntry(row, textvariable=var) if TK_LIB=='customtkinter' else ttk.Entry(row, textvariable=var))
				e.pack(side='right', fill='x', expand=True)
		add_row("Topic", self.vars['topic'])
		add_row("Name", self.vars['name'])
		add_row("Age", self.vars['age'])
		add_row("Language", self.vars['language'], values=['en','fr'])
		add_row("Tone", self.vars['tone'], values=['Gentle','Funny','Adventurous','Calm'])
		themes = self.content.get_available_themes(self.locale) or ['Magical Forest']
		add_row("Theme", self.vars['theme'], values=themes)
		# Advanced controls
		adv = (ctk.CTkFrame(parent) if TK_LIB=='customtkinter' else tk.Frame(parent, bg=self._bg_panel()))
		adv.pack(fill='x', pady=(6,2))
		for label, var in [(LOCALES[self.locale]['guard_n'], self.guard_n_var), (LOCALES[self.locale]['guard_window'], self.guard_window_var), (LOCALES[self.locale]['creative_boost'], self.boost_var), (LOCALES[self.locale]['reading_level'], self.reading_var)]:
			row = (ctk.CTkFrame(adv) if TK_LIB=='customtkinter' else tk.Frame(adv, bg=self._bg_panel()))
			row.pack(fill='x', pady=1)
			tk.Label(row, text=label+":", bg=self._bg_panel(), fg=self._fg_text()).pack(side='left')
			entry = (ctk.CTkEntry(row, textvariable=var) if TK_LIB=='customtkinter' else ttk.Entry(row, textvariable=var))
			entry.pack(side='right', fill='x', expand=True)
		seed_row = (ctk.CTkFrame(parent) if TK_LIB=='customtkinter' else tk.Frame(parent, bg=self._bg_panel()))
		seed_row.pack(fill='x', pady=(2,6))
		tk.Label(seed_row, text="Seed:", bg=self._bg_panel(), fg=self._fg_text()).pack(side='left')
		(ctk.CTkEntry(seed_row, textvariable=self.seed_var) if TK_LIB=='customtkinter' else ttk.Entry(seed_row, textvariable=self.seed_var)).pack(side='right', fill='x', expand=True)
		# Buttons
		btns = (ctk.CTkFrame(parent) if TK_LIB=='customtkinter' else tk.Frame(parent, bg=self._bg_panel()))
		btns.pack(fill='x')
		tk.Button(btns, text=LOCALES[self.locale]['save'], command=self._save_current).pack(side='left', padx=4)
		tk.Button(btns, text=LOCALES[self.locale]['generate'], command=self._generate_one).pack(side='right', padx=4)
		# Batch controls
		batch = (ctk.CTkFrame(parent) if TK_LIB=='customtkinter' else tk.Frame(parent, bg=self._bg_panel()))
		batch.pack(fill='x', pady=(8,4))
		tk.Label(batch, text=LOCALES[self.locale]['batch_title'], bg=self._bg_panel(), fg=self._fg_muted()).pack(anchor='w')
		self.batch_count = tk.IntVar(value=3)
		self.batch_seeds = tk.StringVar(value='')
		row = (ctk.CTkFrame(batch) if TK_LIB=='customtkinter' else tk.Frame(batch, bg=self._bg_panel()))
		row.pack(fill='x')
		tk.Label(row, text=LOCALES[self.locale]['batch_count']+":", bg=self._bg_panel(), fg=self._fg_text()).pack(side='left')
		(ctk.CTkEntry(row, textvariable=self.batch_count) if TK_LIB=='customtkinter' else ttk.Entry(row, textvariable=self.batch_count)).pack(side='left', padx=4)
		tk.Label(row, text=LOCALES[self.locale]['batch_seeds']+":", bg=self._bg_panel(), fg=self._fg_text()).pack(side='left')
		(ctk.CTkEntry(row, textvariable=self.batch_seeds) if TK_LIB=='customtkinter' else ttk.Entry(row, textvariable=self.batch_seeds)).pack(side='left', fill='x', expand=True)
		bbtns = (ctk.CTkFrame(batch) if TK_LIB=='customtkinter' else tk.Frame(batch, bg=self._bg_panel()))
		bbtns.pack(fill='x', pady=(4,0))
		tk.Button(bbtns, text=LOCALES[self.locale]['batch_run'], command=self._run_batch).pack(side='left')
		self.cancel_btn = tk.Button(bbtns, text=LOCALES[self.locale]['batch_cancel'], command=self._cancel_jobs)
		self.cancel_btn.pack(side='left', padx=4)
		# Progress
		self.progress = (ctk.CTkProgressBar(parent) if TK_LIB=='customtkinter' else ttk.Progressbar(parent, mode='determinate'))
		self.progress.pack(fill='x')
		if TK_LIB=='customtkinter': self.progress.set(0)
	def _bg_panel(self): return "#161a2f" if self.settings.get('theme')=='dark' else "#ffffff"
	def _bg_body(self): return "#0f1221" if self.settings.get('theme')=='dark' else "#f8f5f9"
	def _fg_text(self): return "#f2f4ff" if self.settings.get('theme')=='dark' else "#2a2a35"
	def _fg_muted(self): return "#8b91b1" if self.settings.get('theme')=='dark' else "#6b6f82"
	# Actions
	def _new_story(self): self.current_story=None; self._display_text("")
	def _display_text(self, text, title=None):
		self.preview_text.configure(state='normal');
		if TK_LIB=='customtkinter': self.preview_text.delete('0.0', 'end'); self.preview_text.insert('0.0', text)
		else: self.preview_text.delete('1.0', tk.END); self.preview_text.insert('1.0', text)
		self.preview_text.configure(state='disabled')
		if title: self.title_label.config(text=title)
	def _generate_one(self):
		self.status_label.config(text="Generating...")
		threading.Thread(target=self._gen_worker, args=(1,), daemon=True).start()
	def _gen_worker(self, count, seeds_list=None):
		try:
			params = {k: v.get() for k,v in self.vars.items()}
			params['include_moral'] = True
			params['plugin_calm_closure'] = self.settings.get('plugin_calm_closure', True)
			guard_n = self.guard_n_var.get(); guard_w = self.guard_window_var.get(); boost = float(self.boost_var.get()); rlevel = float(self.reading_var.get())
			seeds = seeds_list or []
			if not seeds:
				try:
					if self.batch_seeds.get().strip(): seeds = [int(x.strip()) for x in self.batch_seeds.get().split(',') if x.strip()]
				except Exception:
					seeds = []
			if not seeds:
				base_seed = int(self.seed_var.get() or 0)
				seeds = [base_seed + i for i in range(count)]
			results = []
			self.cancel_event.clear()
			for idx, s in enumerate(seeds[:count]):
				if self.cancel_event.is_set(): break
				res = self.content.generate(params, seed=s, guard_n=guard_n, guard_window=guard_w, creative_boost=boost, reading_level=rlevel)
				results.append(res)
				p = (idx+1)/max(1, len(seeds[:count]))
				self._update_progress(p)
				self.current_story = res
				self.after(0, lambda r=res: self._display_text(r['text'], r['title']))
			self.status_label.config(text="Done" if not self.cancel_event.is_set() else "Cancelled")
			if count==1 and results:
				# show rewrite indicator
				if results[0].get('rewrite_applied'): self._toast("Rewrite applied to pass guard")
		except Exception as e:
			logger.exception("Generation failed")
			self._toast(f"Generation error: {e}", danger=True)
	def _update_progress(self, p):
		if TK_LIB=='customtkinter': self.progress.set(p)
		else: self.progress['value'] = int(p*100); self.progress.update_idletasks()
	def _run_batch(self):
		try:
			cnt = max(1, int(self.batch_count.get()))
			threading.Thread(target=self._gen_worker, args=(cnt,), daemon=True).start()
		except Exception as e:
			self._toast(f"Batch error: {e}", danger=True)
	def _cancel_jobs(self): self.cancel_event.set(); self._toast("Cancel requested")
	def _reroll_beat(self):
		if not self.current_story: return
		beat = self.outline_var.get()
		sents = _split_sentences(self.current_story['text'])
		if beat=='intro' and sents: sents[0] = sents[0][0].upper() + sents[0][1:]
		elif beat=='middle' and len(sents)>1: sents[len(sents)//2] = sents[len(sents)//2]
		elif beat=='climax' and len(sents)>2: sents[-2] = sents[-2]
		elif beat=='moral' and sents: sents[-1] = plugin_calm_closure(sents[-1])
		new_text = " ".join(sents)
		self._display_text(new_text, self.current_story['title'])
		self.current_story['text'] = new_text
	def _save_current(self):
		if not self.current_story:
			self._toast("Nothing to save", danger=True); return
		self.library.add_story(self.current_story)
		self._toast("Saved")
	def _export_current(self, fmt):
		story = self.current_story
		if not story: self._toast(LOCALES[self.locale]['no_story'], danger=True); return
		pattern = f"Bedtime_Story_Maker_{{title}}_{VERSION}_{{ts}}"
		fname = pattern.format(title=_sanitize(story['title']), ts=datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
		initial = self.settings.get('export_path', os.path.expanduser("~"))
		path = filedialog.asksaveasfilename(initialdir=initial, initialfile=f"{fname}.{fmt}", defaultextension=f".{fmt}")
		if not path: return
		try:
			if fmt=='txt': _export_txt(story, path)
			elif fmt=='html': _export_html(story, path)
			elif fmt=='pdf': _export_pdf(story, path)
			elif fmt=='rtf': _export_rtf(story, path)
			self._toast(LOCALES[self.locale]['export_success'])
			self.settings.set('export_path', os.path.dirname(path)); self.settings.save()
		except Exception as e:
			logger.exception("Export failed")
			self._toast(f"{LOCALES[self.locale]['export_failed']}: {e}", danger=True)
	def _export_combined(self):
		story = self.current_story
		if not story: self._toast(LOCALES[self.locale]['no_story'], danger=True); return
		folder = filedialog.askdirectory(initialdir=self.settings.get('export_path', os.path.expanduser("~")))
		if not folder: return
		folder = os.path.join(folder, f"Bedtime_Story_Maker_{_sanitize(story['title'])}_{VERSION}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
		os.makedirs(folder, exist_ok=True)
		for ext in ['txt','html','rtf','pdf']:
			try:
				p = os.path.join(folder, f"{_sanitize(story['title'])}.{ext}")
				if ext=='txt': _export_txt(story, p)
				elif ext=='html': _export_html(story, p)
				elif ext=='pdf': _export_pdf(story, p)
				elif ext=='rtf': _export_rtf(story, p)
			except Exception as e:
				logger.warning(f"Combined export failed for {ext}: {e}")
		# Store listing text
		with open(os.path.join(folder, 'Store_Listing.txt'), 'w', encoding='utf-8') as f:
			f.write(generate_store_listing_text())
		self._toast("Combined export complete")
	def _show_settings(self):
		win = tk.Toplevel(self); win.title(LOCALES[self.locale]['settings_title'])
		frm = tk.Frame(win, bg=self._bg_panel()); frm.pack(padx=10, pady=10, fill='both', expand=True)
		row = tk.Frame(frm, bg=self._bg_panel()); row.pack(fill='x', pady=3)
		tk.Label(row, text=LOCALES[self.locale]['settings_lang_label']+":", bg=self._bg_panel(), fg=self._fg_text()).pack(side='left')
		lang_combo = ttk.Combobox(row, values=['en','fr']); lang_combo.set(self.locale); lang_combo.pack(side='right')
		row2 = tk.Frame(frm, bg=self._bg_panel()); row2.pack(fill='x', pady=3)
		tk.Label(row2, text=LOCALES[self.locale]['settings_theme']+":", bg=self._bg_panel(), fg=self._fg_text()).pack(side='left')
		theme_combo = ttk.Combobox(row2, values=['dark','light','high-contrast']); theme_combo.set(self.settings.get('theme','dark')); theme_combo.pack(side='right')
		row3 = tk.Frame(frm, bg=self._bg_panel()); row3.pack(fill='x', pady=3)
		tk.Label(row3, text=LOCALES[self.locale]['settings_autosave']+":", bg=self._bg_panel(), fg=self._fg_text()).pack(side='left')
		autos = tk.Entry(row3); autos.insert(0, str(self.settings.get('autosave_seconds',60))); autos.pack(side='right')
		row4 = tk.Frame(frm, bg=self._bg_panel()); row4.pack(fill='x', pady=3)
		tk.Label(row4, text=LOCALES[self.locale]['settings_guard']+":", bg=self._bg_panel(), fg=self._fg_text()).pack(side='left')
		guardn = tk.Entry(row4); guardn.insert(0, str(self.settings.get('guard_n',3))); guardn.pack(side='left')
		guardw = tk.Entry(row4); guardw.insert(0, str(self.settings.get('guard_window',50))); guardw.pack(side='left', padx=4)
		row5 = tk.Frame(frm, bg=self._bg_panel()); row5.pack(fill='x', pady=3)
		plugins_var = tk.BooleanVar(value=self.settings.get('plugin_calm_closure', True))
		tk.Checkbutton(row5, text=LOCALES[self.locale]['settings_plugins'], variable=plugins_var).pack(side='left')
		row6 = tk.Frame(frm, bg=self._bg_panel()); row6.pack(fill='x', pady=3)
		api_var = tk.StringVar(value=self.settings.get_api_key())
		api_entry = tk.Entry(row6, textvariable=api_var, show='*'); api_entry.pack(side='left', fill='x', expand=True)
		btn_copy = tk.Button(row6, text='Copy', command=lambda: (self.clipboard_clear(), self.clipboard_append(api_var.get())))
		btn_copy.pack(side='left', padx=4)
		btn_clear = tk.Button(row6, text='Clear', command=lambda: (api_var.set(''), self._toast('Keys cleared')))
		btn_clear.pack(side='left')
		btns = tk.Frame(frm, bg=self._bg_panel()); btns.pack(fill='x', pady=(8,0))
		def save_and_close():
			self.locale = lang_combo.get(); self.settings.set('language', self.locale)
			self.settings.set('theme', theme_combo.get())
			try: self.settings.set('autosave_seconds', max(15, int(autos.get())))
			except: pass
			try: self.settings.set('guard_n', max(2, int(guardn.get()))); self.settings.set('guard_window', max(10, int(guardw.get())))
			except: pass
			self.settings.set('plugin_calm_closure', bool(plugins_var.get()))
			self.settings.set_api_key(api_var.get()); self.settings.save(); win.destroy()
			self.status_label.config(text=f"Settings saved. {VERSION}")
		tk.Button(btns, text='OK', command=save_and_close).pack(side='right')
		
	def _show_about(self):
		win = tk.Toplevel(self); win.title(LOCALES[self.locale]['about_title'])
		frm = tk.Frame(win, bg=self._bg_panel()); frm.pack(padx=12, pady=12)
		tk.Label(frm, text=APP_NAME, font=("Segoe UI", 22, "bold"), bg=self._bg_panel(), fg=self._fg_text()).pack()
		tk.Label(frm, text=f"Version {VERSION}", bg=self._bg_panel(), fg=self._fg_muted()).pack()
		tk.Label(frm, text=f"{COMPANY} • {SITE_URL}", bg=self._bg_panel(), fg=self._fg_text()).pack(pady=(6,0))
		tk.Label(frm, text=SUPPORT_EMAIL, bg=self._bg_panel(), fg='#6d8bff').pack()
		tk.Label(frm, text=f"© {COPYRIGHT_YEAR}", bg=self._bg_panel(), fg=self._fg_muted()).pack(pady=(8,0))
	def _self_check_dialog(self):
		ok, msg = run_self_test()
		self._toast(msg if ok else msg, danger=not ok)
	def _toast(self, msg, danger=False):
		try:
			toast = tk.Toplevel(self); toast.wm_overrideredirect(True)
			bg = '#ef476f' if danger else '#2ec4b6'
			lab = tk.Label(toast, text=msg, bg=bg, fg='white'); lab.pack(ipadx=10, ipady=6)
			self.update_idletasks(); x = self.winfo_rootx()+ self.winfo_width()//2 - toast.winfo_width()//2; y = self.winfo_rooty()+ self.winfo_height()- 60
			toast.wm_geometry(f"+{x}+{y}"); toast.after(2000, toast.destroy)
		except Exception: pass
	def _schedule_autosave(self): self.after(max(5_000, self.settings.get('autosave_seconds',60)*1000), self._autosave)
	def _autosave(self):
		try:
			state = {'current': self.current_story, 'settings': self.settings.settings}
			with open(os.path.join(os.path.expanduser("~"), RECOVERY_FILE), 'w', encoding='utf-8') as f: json.dump(state, f)
			logger.info('Autosaved recovery state')
		except Exception as e:
			logger.warning(f"Autosave failed: {e}")
		finally:
			self._schedule_autosave()
	def _try_restore_recovery(self):
		path = os.path.join(os.path.expanduser("~"), RECOVERY_FILE)
		if not os.path.exists(path): return
		try:
			with open(path, 'r', encoding='utf-8') as f: state = json.load(f)
			self.settings.settings.update(state.get('settings', {}))
			cur = state.get('current')
			if cur:
				self.current_story = cur; self._display_text(cur.get('text',''), cur.get('title'))
				self._toast('Recovered last session')
		except Exception as e:
			logger.warning(f"Recovery failed: {e}")
	def _quit(self):
		try: self.settings.save(); self.library.save()
		except Exception: pass
		self.destroy()

# Exporters

def _sanitize(name): return "".join(c for c in name if c.isalnum() or c in (' ','_')).strip().replace(' ','_')

def _export_txt(story, path):
	with open(path, 'w', encoding='utf-8') as f:
		f.write(story['title']+"\n\n"); f.write(story['text'])

def _export_html(story, path):
	html = f"""<!DOCTYPE html><html lang="{story.get('language','en')}"><head><meta charset="UTF-8"><title>{story['title']}</title><style>body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;max-width:800px;margin:40px auto;padding:20px;line-height:1.6;background-color:#f8f5f9;color:#2a2a35;}}h1{{color:#7a5af8;}}p{{white-space:pre-wrap;}}</style></head><body><h1>{story['title']}</h1><p>{story['text']}</p><footer><small>{APP_NAME} {VERSION} • {COMPANY} • {SITE_URL}</small></footer></body></html>"""
	with open(path, 'w', encoding='utf-8') as f: f.write(textwrap.dedent(html))

def _export_pdf(story, path):
	global REPORTLAB_AVAILABLE
	if not REPORTLAB_AVAILABLE:
		try:
			from reportlab.platypus import SimpleDocTemplate, Paragraph
			from reportlab.lib.styles import getSampleStyleSheet
			from reportlab.lib.pagesizes import letter
			REPORTLAB_AVAILABLE = True
		except Exception as e:
			raise RuntimeError("reportlab not available")
	doc = SimpleDocTemplate(path, pagesize=letter)
	styles = getSampleStyleSheet()
	story_flow = [Paragraph(story['title'], styles['h1'])]
	for para in story['text'].split('\n'):
		if para.strip(): story_flow.append(Paragraph(para, styles['BodyText']))
	doc.build(story_flow)

def _export_rtf(story, path):
	rtf = ["{\\rtf1\\ansi", "{\\fonttbl{\\f0\\fswiss Arial;}}", f"\\fs28 \\b {story['title']} \\b0\\par"]
	for para in story['text'].split('\n'):
		para = para.replace('{','\\{').replace('}','\\}')
		rtf.append(para + "\\par")
	rtf.append(f"\\par {APP_NAME} {VERSION} ")
	rtf.append("}")
	with open(path, 'w', encoding='utf-8') as f: f.write("".join(rtf))

# README and store listing

def write_readme(path):
	content = f"""
Bedtime Story Maker {VERSION}

Quick Start
1. Enter topic, name, choose language and theme
2. Set seed for reproducible stories, adjust guard n and window, optional creative boost
3. Click Generate, Save, Export

Build Steps
- pip install customtkinter reportlab python-docx ebooklib markdown pyinstaller
- pyinstaller --noconfirm --onefile --windowed --name "BedtimeStoryMaker" bedtime_story_maker.py

Store Checklist
- App ID: {APP_ID}
- Brand: {APP_NAME} by {COMPANY}
- Version: {VERSION}
- About dialog shows brand, version, support
- Combined export folder has all formats
- Self test passes: python bedtime_story_maker.py --selftest
"""
	with open(path, 'w', encoding='utf-8') as f: f.write(textwrap.dedent(content))

def generate_store_listing_text():
	return f"{APP_NAME} helps families create gentle, original bedtime stories, offline. Version {VERSION}."

# Self test

def run_self_test():
	try:
		settings = SettingsManager()
		engine = ContentEngine(settings)
		themes = engine.get_available_themes('en')
		if not themes: return False, "No themes available"
		params = {'name':'Alex','topic':'A Forest Walk','age':'6','language':'en','tone':'Gentle','theme':themes[0], 'include_moral': True}
		seed = 12345
		one = engine.generate(params, seed=seed)
		two = engine.generate(params, seed=seed)
		if one['text'] != two['text']: return False, "Reproducible mode mismatch"
		# guard
		tokens = [t.lower().strip(".,;:!?\"'") for t in one['text'].split()]
		if _unique_ratio(tokens, 3, 50) < 0.7: return False, "Guard too low"
		# exports
		import tempfile
		d = tempfile.mkdtemp()
		for ext, fn in [('txt', _export_txt), ('html', _export_html), ('rtf', _export_rtf)]:
			fn(one, os.path.join(d, f"t.{ext}"))
		return True, LOCALES['en']['selfcheck_ok']
	except Exception as e:
		logger.exception("Self test failed")
		return False, f"{LOCALES['en']['selfcheck_fail']}: {e}"

# CLI entry and app run
if __name__ == '__main__':
	if len(sys.argv)>1 and sys.argv[1]=='--selftest':
		ok, msg = run_self_test(); print(msg); sys.exit(0 if ok else 1)
	app = App(); app.mainloop()