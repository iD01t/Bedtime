import argparse
import json
import os
import random
import re
import subprocess
import sys
import textwrap
import site
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256
from typing import Dict, List, Optional, Set, Tuple

# --- Optional web imports (installed on demand) ---
try:
    from flask import Flask, jsonify, request, Response
except Exception:  # pragma: no cover
    Flask = None  # type: ignore
    jsonify = None  # type: ignore
    request = None  # type: ignore
    Response = None  # type: ignore

# --- Optional LLM imports (very optional) ---
TRANSFORMERS_AVAILABLE = False
try:
    if os.environ.get("USE_TRANSFORMERS", "0") == "1":
        from transformers import pipeline  # type: ignore
        TRANSFORMERS_AVAILABLE = True
except Exception:
    TRANSFORMERS_AVAILABLE = False


# ---------------------------
# Utilities and bootstrap
# ---------------------------

REQUIRED_PACKAGES = ["flask>=2.3.0,<3.0.0"]


def run(cmd: List[str]) -> int:
    return subprocess.call(cmd)


def ensure_dependencies(verbose: bool = True) -> None:
    global Flask, jsonify, request, Response
    if Flask is not None:
        return
    # Create a local virtualenv and install packages there to avoid PEP 668 issues
    base_dir = os.path.dirname(os.path.abspath(__file__))
    venv_dir = os.path.join(base_dir, ".venv")
    py_major, py_minor = sys.version_info.major, sys.version_info.minor
    site_dir = os.path.join(venv_dir, "lib", f"python{py_major}.{py_minor}", "site-packages")

    if not os.path.exists(venv_dir):
        if verbose:
            print(f"[bootstrap] Creating virtualenv at {venv_dir}")
        code = run([sys.executable, "-m", "venv", venv_dir])
        if code != 0:
            print("[bootstrap] Failed to create virtualenv. Falling back to system pip with --break-system-packages.")
            if verbose:
                print("[bootstrap] Installing dependencies: ", REQUIRED_PACKAGES)
            code = run([sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "--break-system-packages"] + REQUIRED_PACKAGES)
            if code != 0:
                print("[bootstrap] pip install failed. Please install dependencies manually:")
                print("           pip install " + " ".join(REQUIRED_PACKAGES))
                sys.exit(1)
        else:
            # venv created; proceed to install
            pass

    # Ensure pip exists in venv
    venv_pip = os.path.join(venv_dir, "bin", "pip")
    venv_python = os.path.join(venv_dir, "bin", "python")
    if os.path.exists(venv_dir) and not os.path.exists(venv_pip):
        run([sys.executable, "-m", "ensurepip", "--upgrade"])

    # Determine packages to install
    packages = list(REQUIRED_PACKAGES)
    if os.environ.get("USE_TRANSFORMERS", "0") == "1":
        packages += ["transformers>=4.40.0,<5"]

    if os.path.exists(venv_pip):
        if verbose:
            print("[bootstrap] Installing into venv:", packages)
        code = run([venv_pip, "install", "--disable-pip-version-check"] + packages)
        if code != 0:
            print("[bootstrap] venv install failed. Trying system pip with --break-system-packages")
            code = run([sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "--break-system-packages"] + packages)
            if code != 0:
                print("[bootstrap] Installation failed. Please install manually.")
                sys.exit(1)
    else:
        if verbose:
            print("[bootstrap] venv not available; using system pip with --break-system-packages")
        code = run([sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "--break-system-packages"] + packages)
        if code != 0:
            print("[bootstrap] Installation failed. Please install manually.")
            sys.exit(1)

    # Add venv or user site-packages to path and import Flask
    if os.path.isdir(site_dir):
        site.addsitedir(site_dir)
    else:
        try:
            user_site = site.getusersitepackages()
            if os.path.isdir(user_site):
                site.addsitedir(user_site)
        except Exception:
            pass
    try:
        from flask import Flask as _Flask, jsonify as _jsonify, request as _request, Response as _Response
        Flask, jsonify, request, Response = _Flask, _jsonify, _request, _Response
    except Exception as exc:
        print("[bootstrap] Import failed after install:", repr(exc))
        sys.exit(1)


# ---------------------------
# Story engine
# ---------------------------

@dataclass
class StoryConfig:
    genre: str
    tone: str
    length: str  # short, medium, long
    seed: Optional[int] = None
    title_hint: Optional[str] = None
    enable_llm: bool = False


@dataclass
class Character:
    name: str
    role: str
    trait: str


@dataclass
class StoryWorld:
    setting: str
    era: str
    mood: str


@dataclass
class StoryPlan:
    title: str
    protagonist: Character
    antagonist: Character
    ally: Character
    world: StoryWorld
    theme: str
    stakes: str
    object_of_desire: str
    beats: List[str] = field(default_factory=list)


def _rng(seed: Optional[int]) -> random.Random:
    if seed is None:
        seed = int.from_bytes(os.urandom(8), "big")
    return random.Random(seed)


NAME_BANK = {
    "general": [
        "Avery", "Rowan", "Quinn", "Jordan", "Riley", "Morgan", "Casey", "Emerson", "Hayden", "Parker",
        "Sage", "Taylor", "Elliot", "Reese", "Skyler", "Harper", "Finley", "Dakota", "Phoenix", "Alex",
    ],
    "fantasy": [
        "Elowen", "Kael", "Seraphine", "Thorin", "Lyra", "Alaric", "Neris", "Isolde", "Corin", "Mira",
    ],
    "scifi": [
        "Nova", "Orion", "Vega", "Cassian", "Zara", "Kepler", "Astra", "Juno", "Talon", "Cyra",
    ],
    "mystery": [
        "Marlow", "Sable", "Hollis", "Ellis", "Percy", "Greer", "Briar", "Blaine", "Tamsin", "Maven",
    ],
}

SETTING_BANK = {
    "fantasy": [
        ("a mist-laced valley of towering ruins", "age of fractured kingdoms", "enchanted"),
        ("a cliffside city carved from obsidian", "era of quiet rebellions", "brooding"),
    ],
    "scifi": [
        ("a rotating habitat above a blue dwarf star", "post-expansion cycle", "clinical"),
        ("a dust-wreathed outpost on a tidally-locked world", "pre-jump renaissance", "austere"),
    ],
    "mystery": [
        ("a rain-dimmed harbor town of salt and neon", "off-season lull", "sombre"),
        ("a museum wing closed for renovation", "funding drought", "hushed"),
    ],
    "general": [
        ("a quiet suburb stitched by cul-de-sacs", "early autumn", "wistful"),
        ("a sun-warmed seaside village", "late summer", "golden"),
    ],
}

THEMES = [
    "the cost of truth",
    "becoming who you already are",
    "the kindness of strangers",
    "power and what it asks of us",
    "promises kept too late",
]

DESIRES = [
    "to bring someone home",
    "to prove a quiet suspicion",
    "to keep a fragile promise",
    "to start again without erasing the past",
    "to protect a small thing that matters",
]

STAKE_PATTERNS = [
    "If they fail, {consequence}.",
    "Failure means {consequence}—and no one else will try again.",
    "Succeed, and {silver}; fail, and {consequence}.",
]

STAKE_FILLERS = {
    "consequence": [
        "someone gentle will be broken",
        "the place they love will be swallowed by indifference",
        "a quiet cruelty will become normal",
        "their name will be remembered for the wrong reason",
    ],
    "silver": [
        "they might finally sleep without rehearsing the past",
        "the ones who doubted will share their warmth",
        "they will get a sliver of their old life back",
    ],
}

TRAITS = [
    "soft-spoken but relentless",
    "a careful observer with a crooked grin",
    "unlucky, and done apologizing",
    "methodical until it matters, then reckless",
    "haunted by a promise they meant to keep",
]

ANTAGONIST_TRAITS = [
    "smiles without showing teeth",
    "collects debts that were never owed",
    "believes mercy is a kind of theft",
    "tidies every room they enter",
]

ALLY_TRAITS = [
    "laughs too loud at the wrong time",
    "keeps lists inside of lists",
    "says maybe when they mean yes",
]

TONE_TO_STYLE = {
    "warm": dict(adjectives=["warm", "tender", "golden"], cadence="flowing"),
    "dark": dict(adjectives=["dim", "hushed", "severe"], cadence="staccato"),
    "whimsical": dict(adjectives=["unruly", "lilting", "bright"], cadence="playful"),
    "serious": dict(adjectives=["measured", "quiet", "precise"], cadence="measured"),
}

BEAT_ORDER = [
    "Hook",
    "Inciting Incident",
    "Debate",
    "Midpoint",
    "Bad Turn",
    "Climax",
    "Resolution",
]


def choose(rng: random.Random, items: List[str]) -> str:
    return rng.choice(items)


def choose_tuple(rng: random.Random, items: List[Tuple[str, str, str]]) -> Tuple[str, str, str]:
    return rng.choice(items)


def pick_name_by_genre(rng: random.Random, genre: str) -> str:
    bank = NAME_BANK.get(genre, []) + NAME_BANK["general"]
    return choose(rng, bank)


def plan_story(config: StoryConfig) -> StoryPlan:
    rng = _rng(config.seed)

    genre_key = config.genre if config.genre in SETTING_BANK else "general"
    setting, era, mood = choose_tuple(rng, SETTING_BANK[genre_key])

    protagonist = Character(
        name=pick_name_by_genre(rng, config.genre),
        role="protagonist",
        trait=choose(rng, TRAITS),
    )
    antagonist = Character(
        name=pick_name_by_genre(rng, config.genre),
        role="antagonist",
        trait=choose(rng, ANTAGONIST_TRAITS),
    )
    ally = Character(
        name=pick_name_by_genre(rng, config.genre),
        role="ally",
        trait=choose(rng, ALLY_TRAITS),
    )

    world = StoryWorld(setting=setting, era=era, mood=mood)

    theme = choose(rng, THEMES)
    object_of_desire = choose(rng, DESIRES)

    stake_tpl = choose(rng, STAKE_PATTERNS)
    stakes = stake_tpl.format(
        consequence=choose(rng, STAKE_FILLERS["consequence"]),
        silver=choose(rng, STAKE_FILLERS["silver"]),
    )

    title_seed = config.title_hint or theme
    hashed = sha256((title_seed + protagonist.name + world.setting).encode()).hexdigest()[:6]
    title = f"{title_seed.title()} ({hashed})"

    return StoryPlan(
        title=title,
        protagonist=protagonist,
        antagonist=antagonist,
        ally=ally,
        world=world,
        theme=theme,
        stakes=stakes,
        object_of_desire=object_of_desire,
    )


def _sentence_variants(base: str) -> List[str]:
    variants = [
        base,
        base.replace("and", "&"),
        base.replace(",", "—"),
    ]
    if base.endswith("."):
        variants.append(base[:-1])
    return variants


def _clean_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _n_grams(tokens: List[str], n: int) -> Set[Tuple[str, ...]]:
    return set(tuple(tokens[i : i + n]) for i in range(0, max(0, len(tokens) - n + 1)))


def _unique_ngram_ratio(tokens: List[str], n: int) -> float:
    total = max(0, len(tokens) - n + 1)
    if total <= 0:
        return 1.0
    seen = set(tuple(tokens[i:i+n]) for i in range(total))
    return len(seen) / float(total)


def _avoid_repetition(sentences: List[str], block_ngrams: int = 3) -> List[str]:
    seen: Set[Tuple[str, ...]] = set()
    curated: List[str] = []
    for s in sentences:
        tokens = s.lower().split()
        grams = _n_grams(tokens, block_ngrams)
        if grams & seen:
            # Try a simple paraphrase by shuffling commas/dashes, else skip
            for v in _sentence_variants(s):
                grams_v = _n_grams(v.lower().split(), block_ngrams)
                if not (grams_v & seen):
                    curated.append(v)
                    seen |= grams_v
                    break
            else:
                continue
        else:
            curated.append(s)
            seen |= grams
    return curated


def _apply_global_guard(beats_sentences: List[List[str]], n: int = 4) -> List[List[str]]:
    seen: Set[Tuple[str, ...]] = set()
    curated_beats: List[List[str]] = []
    for sentences in beats_sentences:
        curated: List[str] = []
        for s in sentences:
            toks = s.lower().split()
            grams = _n_grams(toks, n)
            if grams & seen:
                variant_applied = False
                for v in _sentence_variants(s):
                    vg = _n_grams(v.lower().split(), n)
                    if not (vg & seen):
                        curated.append(v)
                        seen |= vg
                        variant_applied = True
                        break
                if not variant_applied:
                    continue
            else:
                curated.append(s)
                seen |= grams
        curated_beats.append(curated)
    return curated_beats


def _style_sentence(text: str, tone: str, rng: random.Random) -> str:
    style = TONE_TO_STYLE.get(tone, TONE_TO_STYLE["serious"])  # default
    adjectives = style["adjectives"]
    cadence = style["cadence"]

    # Vary openings to avoid repetition
    openers = {
        "flowing": ["And", "Sometimes", "Often", "Meanwhile"],
        "staccato": ["Then", "Now", "After", "Before"],
        "playful": ["Suppose", "Maybe", "Consider", "Imagine"],
        "measured": ["In time", "At last", "Eventually", "In truth"],
    }[cadence]

    opener = rng.choice(["", rng.choice(openers) + ", "])  # occasionally add opener
    adjective = rng.choice(["", rng.choice(adjectives)])

    sentence = text
    if adjective and rng.random() < 0.5:
        sentence = sentence.replace(" ", f" {adjective} ", 1)

    sentence = opener + sentence
    sentence = sentence[0].upper() + sentence[1:]
    if not sentence.endswith(('.', '!', '?')):
        sentence += "."
    return _clean_spaces(sentence)


def expand_beat(beat_name: str, plan: StoryPlan, tone: str, rng: random.Random, use_llm: bool) -> List[str]:
    base_prompts = {
        "Hook": (
            f"Introduce {plan.protagonist.name}, {plan.protagonist.trait}, in {plan.world.setting} during {plan.world.era}. "
            f"They want {plan.object_of_desire}."
        ),
        "Inciting Incident": (
            f"Something disrupts the ordinary: {plan.antagonist.name}, who {plan.antagonist.trait}, interferes."
        ),
        "Debate": (
            f"{plan.protagonist.name} doubts the path forward. {plan.ally.name}, {plan.ally.trait}, offers help."
        ),
        "Midpoint": (
            f"A reveal reframes the goal about {plan.theme}. The cost emerges: {plan.stakes}"
        ),
        "Bad Turn": (
            f"A setback. {plan.antagonist.name} gains advantage in {plan.world.mood} circumstances."
        ),
        "Climax": (
            f"A decisive choice by {plan.protagonist.name} in the face of {plan.antagonist.name}."
        ),
        "Resolution": (
            f"Aftermath in {plan.world.setting}. The world tilts; threads resolve, not neatly, but honestly."
        ),
    }

    target_sentences = {"short": 3, "medium": 5, "long": 7}
    n_sent = target_sentences.get(plan_length_cache.get("length", "medium"), 5)

    base = base_prompts.get(beat_name, "A moment advances the story.")

    if use_llm and TRANSFORMERS_AVAILABLE:
        try:
            gen = pipeline("text-generation", model=os.environ.get("GEN_MODEL", "sshleifer/tiny-gpt2"))
            seed = plan_length_cache.get("seed", 0)
            random.seed(seed)
            txt = gen(base, max_new_tokens=80, num_return_sequences=1, do_sample=True, temperature=0.9)[0]["generated_text"]
            # Split into sentences and keep the last n_sent sentences
            parts = re.split(r"(?<=[.!?])\s+", txt)
            parts = [p.strip() for p in parts if p.strip()]
            parts = parts[-max(n_sent, 3) :]
            styled = [_style_sentence(p, tone, rng) for p in parts]
            return _avoid_repetition(styled, block_ngrams=4)
        except Exception:
            pass

    # Offline handcrafted expansion with variant prefixes/verbs
    detail_prefixes = [
        "A detail:", "One small detail:", "A stray detail:", "Noted in passing:", "A tiny detail:",
    ]
    place_intros = [
        "The place feels", "This place feels", "The setting seems", "Here, it feels", "Around them it feels",
    ]
    choose_verbs = ["chooses", "opts for", "decides on", "elects", "picks"]
    ally_suggests = ["suggests", "offers", "proposes", "whispers", "insists"]

    templates = [
        "{who} notices {change} and weighs {cost}.",
        "{who} recalls {memory} while {action}.",
        "{ally} {ally_verb} {suggestion}; it sounds {adverb} {feeling}.",
        "{who} {choose_verb} {choice} despite {risk}.",
        "{detail_prefix} {detail}.",
        "{place_intro} {place_feel}, like {simile}.",
    ]

    fill_base = {
        "who": plan.protagonist.name,
        "ally": plan.ally.name,
        "change": rng.choice([
            "a light that should be off",
            "a door that never locked",
            "footprints where there was dust",
            "a voice that remembers their name",
        ]),
        "cost": rng.choice([
            "the weight of their promise",
            "what it might make them become",
            "how it will mark their friends",
            "the life that will not return",
        ]),
        "memory": rng.choice([
            "a half-finished letter",
            "a shoreline at dusk",
            "an unfinished song",
            "a quiet apology",
        ]),
        "action": rng.choice([
            "sorting old tools",
            "following a map of rumors",
            "listening at the vents",
            "reading margins in a borrowed book",
        ]),
        "suggestion": rng.choice([
            "asking for help",
            "waiting one more night",
            "trading a secret",
            "turning back now",
        ]),
        "adverb": rng.choice(["strangely", "more", "less", "unexpectedly"]),
        "feeling": rng.choice(["right", "wrong", "necessary", "dangerous"]),
        "choice": rng.choice([
            "to tell the truth",
            "to trust a stranger",
            "to hide the proof",
            "to go alone",
        ]),
        "risk": rng.choice([
            "their name becoming a rumor",
            "losing the last photograph",
            "someone learning what they fear",
            "never being believed",
        ]),
        "detail": rng.choice([
            "chalk dust on a windowsill",
            "a key with teeth filed flat",
            "knuckles inked with directions",
            "a calendar missing its days",
        ]),
        "place_feel": rng.choice(["tilted", "watchful", "hollow", "expectant"]),
        "simile": rng.choice([
            "a room holding its breath",
            "a song missing its middle",
            "a tide waiting under ice",
            "an elevator between floors",
        ]),
    }

    sentences: List[str] = []
    # Seed one sentence from the base beat prompt to anchor coherence
    sentences.append(_style_sentence(base, tone, rng))
    while len(sentences) < n_sent:
        tpl = rng.choice(templates)
        fill = dict(fill_base)
        fill["detail_prefix"] = rng.choice(detail_prefixes)
        fill["place_intro"] = rng.choice(place_intros)
        fill["choose_verb"] = rng.choice(choose_verbs)
        fill["ally_verb"] = rng.choice(ally_suggests)
        s = tpl.format(**fill)
        s = _style_sentence(s, tone, rng)
        sentences.append(s)
    return _avoid_repetition(sentences, block_ngrams=4)


# cache for length and seed accessible to beat expansion (simple approach)
plan_length_cache: Dict[str, int] = {}


def generate_story(config: StoryConfig) -> Dict[str, object]:
    rng = _rng(config.seed)
    plan = plan_story(config)
    # store length as string for expand_beat to read correctly
    plan_length_cache["length"] = config.length  # type: ignore
    plan_length_cache["seed"] = config.seed or 0

    beats: List[Tuple[str, List[str]]] = []
    beat_sentences: List[List[str]] = []

    for beat_name in BEAT_ORDER:
        sentences = expand_beat(beat_name, plan, config.tone, _rng(config.seed), use_llm=config.enable_llm)
        beats.append((beat_name, sentences))
        beat_sentences.append(sentences)

    # Apply a global 4-gram guard across beats to reduce cross-beat repetition
    guarded = _apply_global_guard(beat_sentences, n=4)

    # Assemble paragraphs
    paragraphs: List[str] = []
    for idx, (name, _sentences) in enumerate(beats):
        paragraph = " ".join(guarded[idx])
        paragraphs.append(paragraph)

    story_text = "\n\n".join(paragraphs)

    # Simple non-repetition check: compute 4-gram uniqueness ratio
    all_tokens = re.findall(r"[a-z']+", story_text.lower())
    uniq4 = _unique_ngram_ratio(all_tokens, 4)
    # Dynamic threshold by length
    length_key = config.length
    threshold = {"short": 0.86, "medium": 0.9, "long": 0.92}.get(length_key, 0.9)
    anti_rep_ok = uniq4 >= threshold

    meta = {
        "title": plan.title,
        "genre": config.genre,
        "tone": config.tone,
        "length": config.length,
        "seed": config.seed,
        "theme": plan.theme,
        "stakes": plan.stakes,
        "world": {
            "setting": plan.world.setting,
            "era": plan.world.era,
            "mood": plan.world.mood,
        },
        "characters": {
            "protagonist": plan.protagonist.__dict__,
            "antagonist": plan.antagonist.__dict__,
            "ally": plan.ally.__dict__,
        },
        "beats": [name for name, _ in beats],
        "anti_repetition_passed": anti_rep_ok,
        "uniqueness_score": round(uniq4, 4),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    return {
        "meta": meta,
        "text": story_text,
        "paragraphs": paragraphs,
    }


# ---------------------------
# Web app
# ---------------------------

def create_app() -> "Flask":  # type: ignore
    ensure_dependencies()
    app = Flask(__name__)

    @app.get("/")
    def index() -> Response:
        html = INDEX_HTML
        return Response(html, mimetype="text/html")

    @app.get("/api/health")
    def health() -> Response:
        return jsonify({"ok": True, "time": datetime.utcnow().isoformat() + "Z"})

    @app.post("/api/generate")
    def api_generate() -> Response:
        payload = request.get_json(force=True, silent=True) or {}
        cfg = StoryConfig(
            genre=payload.get("genre", "general"),
            tone=payload.get("tone", "serious"),
            length=payload.get("length", "medium"),
            seed=payload.get("seed"),
            title_hint=payload.get("title_hint"),
            enable_llm=bool(payload.get("enable_llm", False)),
        )
        result = generate_story(cfg)
        return jsonify(result)

    return app


# ---------------------------
# Frontend (embedded)
# ---------------------------

INDEX_HTML = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>Story Forge – Offline Narrative Generator</title>
  <style>
    :root {
      --bg: #0f1221;
      --panel: #161a2f;
      --muted: #8b91b1;
      --text: #f2f4ff;
      --brand: #6d8bff;
      --accent: #20e3b2;
      --warn: #ffb86b;
      --danger: #ff6d6d;
      --shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
      --radius: 14px;
    }
    * { box-sizing: border-box; }
    html, body { height: 100%; }
    body {
      margin: 0;
      font: 15px/1.5 system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, "Helvetica Neue", Arial;
      color: var(--text);
      background: radial-gradient(1200px 700px at 20% 0%, #161a2f, var(--bg)), var(--bg);
    }
    .nav {
      position: sticky; top: 0; z-index: 10;
      display: flex; gap: 14px; align-items: center; justify-content: space-between;
      padding: 14px 18px; background: rgba(15,18,33,0.7); backdrop-filter: blur(10px);
      border-bottom: 1px solid rgba(255,255,255,0.06);
    }
    .brand { display: flex; align-items: center; gap: 12px; font-weight: 700; letter-spacing: 0.3px; }
    .brand .logo { width: 22px; height: 22px; border-radius: 6px; background: linear-gradient(135deg, var(--brand), var(--accent)); box-shadow: var(--shadow); }
    .nav .actions { display: flex; gap: 10px; }
    .btn { padding: 10px 14px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); color: var(--text); background: #1a1f39; cursor: pointer; transition: all .15s; }
    .btn.primary { background: linear-gradient(135deg, var(--brand), #5568ff); border-color: transparent; }
    .btn:hover { transform: translateY(-1px); box-shadow: var(--shadow); }
    .shell { max-width: 1100px; margin: 26px auto; padding: 0 18px; }

    .layout { display: grid; grid-template-columns: 360px 1fr; gap: 22px; }
    @media (max-width: 940px) { .layout { grid-template-columns: 1fr; } }

    .panel { background: rgba(22,26,47,0.9); border: 1px solid rgba(255,255,255,0.06); border-radius: var(--radius); box-shadow: var(--shadow); }
    .card { padding: 18px; }
    .card h2 { margin: 2px 0 14px; font-size: 16px; letter-spacing: .2px; }

    .field { display: grid; gap: 6px; margin-bottom: 12px; }
    .field label { font-size: 12px; color: var(--muted); }
    .field input, .field select, .field textarea {
      width: 100%; padding: 10px 12px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.08);
      color: var(--text); background: #0f1330; outline: none;
    }
    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }

    .story { padding: 0; overflow: hidden; }
    .story .header { padding: 18px; border-bottom: 1px solid rgba(255,255,255,0.06); background: linear-gradient(0deg, rgba(109,139,255,0.05), rgba(32,227,178,0.05)); }
    .story .title { font-size: 20px; font-weight: 700; margin: 0; }
    .story .meta { font-size: 12px; color: var(--muted); margin-top: 6px; }
    .story .content { padding: 18px; }
    .para { margin: 0 0 14px; text-wrap: pretty; }

    .toolbar { display: flex; gap: 8px; flex-wrap: wrap; padding: 12px 18px; border-top: 1px solid rgba(255,255,255,0.06); background: rgba(0,0,0,0.12); }
    .pill { font-size: 12px; padding: 6px 10px; border-radius: 999px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.08); color: var(--muted); }

    .grid { display: grid; gap: 10px; grid-template-columns: repeat(2, 1fr); }
    @media (max-width: 680px) { .grid { grid-template-columns: 1fr; } }

    .kbd { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; font-size: 12px; padding: 2px 6px; border-radius: 6px; background: rgba(255,255,255,0.08); }
    .muted { color: var(--muted); }

    .ghost { opacity: .6; }
    .skeleton { background: linear-gradient(90deg, rgba(255,255,255,0.05), rgba(255,255,255,0.12), rgba(255,255,255,0.05)); background-size: 200% 100%; animation: shimmer 1.4s infinite; border-radius: 8px; }
    @keyframes shimmer { from { background-position: 200% 0; } to { background-position: -200% 0; } }

    footer { text-align: center; padding: 20px; color: var(--muted); }
  </style>
</head>
<body>
  <div class="nav">
    <div class="brand"><div class="logo"></div> Story Forge</div>
    <div class="actions">
      <button class="btn" id="btn-copy">Copy</button>
      <button class="btn" id="btn-download">Download</button>
      <button class="btn primary" id="btn-generate">Generate</button>
    </div>
  </div>

  <div class="shell">
    <div class="layout">
      <div class="panel card">
        <h2>Controls</h2>
        <div class="field">
          <label>Title hint</label>
          <input id="title_hint" placeholder="e.g., a quiet rebellion" />
        </div>
        <div class="row">
          <div class="field">
            <label>Genre</label>
            <select id="genre">
              <option>general</option>
              <option>fantasy</option>
              <option>scifi</option>
              <option>mystery</option>
            </select>
          </div>
          <div class="field">
            <label>Tone</label>
            <select id="tone">
              <option>serious</option>
              <option>warm</option>
              <option>dark</option>
              <option>whimsical</option>
            </select>
          </div>
        </div>
        <div class="row">
          <div class="field">
            <label>Length</label>
            <select id="length">
              <option>short</option>
              <option selected>medium</option>
              <option>long</option>
            </select>
          </div>
          <div class="field">
            <label>Seed <span class="muted">(leave blank for random)</span></label>
            <input id="seed" type="number" placeholder="e.g., 1337" />
          </div>
        </div>
        <div class="field">
          <label><input type="checkbox" id="enable_llm" /> Try tiny LLM if available</label>
        </div>
        <div class="grid">
          <div class="pill">Offline, template + logic generator</div>
          <div class="pill">Anti-repetition n-gram guard</div>
        </div>
      </div>

      <div class="panel story">
        <div class="header">
          <h1 class="title" id="story-title">Your story will appear here</h1>
          <div class="meta" id="story-meta">Set options and click Generate.</div>
        </div>
        <div class="content" id="story-content">
          <p class="para ghost">Nothing yet. Try a warm fantasy or a dark mystery.</p>
        </div>
        <div class="toolbar">
          <div class="pill" id="beat-pill">Beats: –</div>
          <div class="pill" id="guard-pill">Repetition check: –</div>
        </div>
      </div>
    </div>

    <footer>
      Built to run fully offline. Tip: press <span class="kbd">G</span> to generate.
    </footer>
  </div>

  <script>
    const el = (id) => document.getElementById(id);
    const titleEl = el('story-title');
    const metaEl = el('story-meta');
    const contentEl = el('story-content');
    const beatPill = el('beat-pill');
    const guardPill = el('guard-pill');

    async function generate() {
      const payload = {
        title_hint: el('title_hint').value || undefined,
        genre: el('genre').value,
        tone: el('tone').value,
        length: el('length').value,
        seed: el('seed').value ? parseInt(el('seed').value, 10) : undefined,
        enable_llm: el('enable_llm').checked,
      };

      contentEl.innerHTML = '<div class="skeleton" style="height: 18px; margin: 8px 0;"></div>'.repeat(12);
      titleEl.textContent = 'Generating…';
      metaEl.textContent = 'Please wait';

      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      titleEl.textContent = data.meta.title;
      metaEl.textContent = `${data.meta.genre} · ${data.meta.tone} · ${data.meta.length}`;
      beatPill.textContent = `Beats: ${data.meta.beats.join(' → ')}`;
      guardPill.textContent = `Repetition check: ${data.meta.anti_repetition_passed ? 'passed' : 'warn'}`;

      contentEl.innerHTML = '';
      data.paragraphs.forEach(p => {
        const para = document.createElement('p');
        para.className = 'para';
        para.textContent = p;
        contentEl.appendChild(para);
      });

      try { localStorage.setItem('last_story', JSON.stringify(data)); } catch (_) {}
    }

    function copyStory() {
      const title = titleEl.textContent.trim();
      const paras = [...contentEl.querySelectorAll('.para')].map(p => p.textContent);
      const txt = `# ${title}\n\n` + paras.join('\n\n') + '\n';
      navigator.clipboard.writeText(txt);
    }

    function downloadStory() {
      const title = titleEl.textContent.trim().replace(/[^a-z0-9\- ]/gi, '').replace(/\s+/g, '_') || 'story';
      const paras = [...contentEl.querySelectorAll('.para')].map(p => p.textContent);
      const blob = new Blob([paras.join('\n\n') + '\n'], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = `${title}.txt`; a.click();
      setTimeout(() => URL.revokeObjectURL(url), 2500);
    }

    el('btn-generate').addEventListener('click', generate);
    el('btn-copy').addEventListener('click', copyStory);
    el('btn-download').addEventListener('click', downloadStory);

    window.addEventListener('keydown', (e) => { if (e.key.toLowerCase() === 'g') generate(); });

    // Load last story if present
    try {
      const cached = localStorage.getItem('last_story');
      if (cached) {
        const data = JSON.parse(cached);
        el('story-title').textContent = data.meta.title;
        el('story-meta').textContent = `${data.meta.genre} · ${data.meta.tone} · ${data.meta.length}`;
        beatPill.textContent = `Beats: ${data.meta.beats.join(' → ')}`;
        guardPill.textContent = `Repetition check: ${data.meta.anti_repetition_passed ? 'passed' : 'warn'}`;
        contentEl.innerHTML = '';
        data.paragraphs.forEach(p => {
          const para = document.createElement('p');
          para.className = 'para';
          para.textContent = p;
          contentEl.appendChild(para);
        });
      }
    } catch (_) {}
  </script>
</body>
</html>
"""


# ---------------------------
# CLI
# ---------------------------

def cli(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Story Forge – offline story generator")
    parser.add_argument("command", choices=["serve", "generate", "self-test", "install"], help="action to run")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)))
    parser.add_argument("--genre", default="general")
    parser.add_argument("--tone", default="serious")
    parser.add_argument("--length", default="medium", choices=["short", "medium", "long"])
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--title-hint", dest="title_hint", default=None)
    parser.add_argument("--enable-llm", action="store_true")

    args = parser.parse_args(argv)

    if args.command == "install":
        ensure_dependencies()
        print("Dependencies installed.")
        return 0

    if args.command == "serve":
        ensure_dependencies()
        app = create_app()
        app.run(host=args.host, port=args.port, debug=False)
        return 0

    if args.command == "generate":
        cfg = StoryConfig(
            genre=args.genre,
            tone=args.tone,
            length=args.length,
            seed=args.seed,
            title_hint=args.title_hint,
            enable_llm=args.enable_llm,
        )
        result = generate_story(cfg)
        print(result["meta"]["title"])  # title line
        print()
        print(result["text"])  # full text
        return 0

    if args.command == "self-test":
        # Basic regression: generate all combos small set
        seeds = [None, 42, 1337]
        genres = ["general", "fantasy", "scifi", "mystery"]
        tones = ["serious", "warm", "dark", "whimsical"]
        lengths = ["short", "medium"]
        ok = True
        for g in genres:
            for t in tones:
                for l in lengths:
                    for s in seeds:
                        cfg = StoryConfig(genre=g, tone=t, length=l, seed=s)
                        out = generate_story(cfg)
                        text = out["text"]
                        assert len(text) > 100, "Story too short"
                        # Check 3-gram repetition guard passed
                        assert out["meta"]["anti_repetition_passed"], "Repetition guard failed"
        if ok:
            print("Self-test passed.")
            return 0

    return 1


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # default to serve
        sys.exit(cli(["serve"]))
    sys.exit(cli())