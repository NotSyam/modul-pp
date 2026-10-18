#!/usr/bin/env python3
"""
generate_audio.py — Edge-TTS Audio Narration Generator for Modul PP

Reads narration scripts from a content.json and generates studio-quality neural
MP3 audio files, one per slide, using Microsoft Edge-TTS.

NARRATION RESOLUTION ORDER (per slide index N)
  1. `slides[N].narration`                       (most specific wins)
  2. `narration["N"]` / `narration[N]`           (course-wide transcript map)
  3. Auto "intisari" fallback                    (composed from the slide's own
     title/lead/descs/steps/takeaways — disable with --no-fallback)
  4. Skipped, and reported at the end.

  Steps 1 and 2 are both first-class: the shell renders either one into the
  Transcript tab and the CC dock (slideDef.narration || COURSE.narration[N]).

PHONETIC RESPELLING
  SOP/ISO/LMS/BUMN-style abbreviations and PT PP / HRIS / KPI jargon are expanded
  into pronounceable forms before synthesis, because Edge-TTS reads bare acronyms
  inconsistently. The dictionary lives in PRONUNCIATION_MAP; extend it per
  project with --pronunciation-file (JSON: {"SOP": "es o pe"}).

USAGE
  python3 scripts/generate_audio.py --content <content.json> [options]

OPTIONS
  --content PATH            content.json (or a standalone narration JSON)
  --output-dir PATH         Output folder for MP3 files (default: ./audio)
  --voice NAME              gadis | ardi | jenny | guy | any full Edge-TTS voice
  --rate RATE               e.g. +0%, +10%, -5% (default: +0%)
  --unit INDEX              Generate a single unit only
  --force                   Re-generate files that already exist
  --dry-run                 Print the exact script per slide; no TTS calls
  --check                   Report narration coverage only; no TTS calls
  --no-phonetic             Disable the pronunciation dictionary
  --no-fallback             Disable the intisari fallback (only explicit narration)
  --pronunciation-file P    JSON file merging extra {TERM: "respell"} entries

EXAMPLES
  python3 scripts/generate_audio.py --content content.json
  python3 scripts/generate_audio.py --content content.json --voice ardi --rate -4%
  python3 scripts/generate_audio.py --content content.json --check
  python3 scripts/generate_audio.py --content content.json --dry-run --unit 3
"""
import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


VOICE_CHOICES = {
    "gadis": "id-ID-GadisNeural",      # Female, warm & expressive (Indonesian)
    "ardi": "id-ID-ArdiNeural",        # Male, authoritative & formal (Indonesian)
    "jenny": "en-US-JennyNeural",      # Female, natural & engaging (English)
    "guy": "en-US-GuyNeural",          # Male, professional (English)
}

# Acronyms and corporate jargon that Edge-TTS mispronounces when left bare.
# Longest keys are applied first so "PT PP" wins over "PP".
PRONUNCIATION_MAP = {
    "SOP": "es o pe",
    "ISO": "i es o",
    "LMS": "el em es",
    "HRIS": "ha er i es",
    "HRD": "ha er de",
    "HC": "ha se",
    "KPI": "ka pe i",
    "BUMN": "be u em en",
    "BUMD": "be u em de",
    "PT PP": "pe te pe pe",
    "PTPP": "pe te pe pe",
    "QC": "kiu si",
    "QA": "kiu e",
    "PIC": "pi ai si",
    "SLA": "es el e",
    "TOR": "te o er",
    "RAB": "er a be",
    "SPO": "es pe o",
    "SCC": "es si si",
    "WI": "we i",
    "NIP": "en i pe",
    "NRP": "en er pe",
    "e-learning": "i learning",
}

# Slide keys that hold *narrative* copy worth speaking in the intisari fallback.
NARRATABLE_KEYS = (
    "title", "heroTitle", "heroLead", "lead", "subtitle", "intro", "desc",
    "body", "note", "caption", "summary", "takeaways", "label", "value",
    "feedback", "scenario", "statement",
)
# Keys that must never be auto-narrated (quiz answers, media paths, metadata).
NEVER_NARRATE_KEYS = {
    "type", "icon", "category", "duration", "narration", "src", "url", "href",
    "logo", "image", "images", "webhookUrl", "question", "options", "explanation",
    "acceptedAnswers", "correctIndex", "correctBool", "placeholder", "id",
    "isCorrect", "status", "statusPendingLabel", "columns", "rows", "gradient",
    "brand", "course", "units", "slides", "glossary", "template",
}

MAX_FALLBACK_WORDS = 220


# ────────────────────────────────────────────────────────────────────────────
# Narration extraction
# ────────────────────────────────────────────────────────────────────────────
def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"[!] Error parsing JSON {path}: {e}", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"[!] Cannot read {path}: {e}", file=sys.stderr)
        sys.exit(1)


def collect_phrases(node, out, depth=0, max_depth=4):
    """Walk a slide and collect human-readable phrases for the fallback script."""
    if depth > max_depth or len(out) > 60:
        return
    if isinstance(node, str):
        text = node.strip()
        # Skip HTML-ish or path-ish fragments.
        if text and not text.startswith(("http", "data:", "./")) and len(text) > 1:
            out.append(text)
        return
    if isinstance(node, list):
        for entry in node:
            collect_phrases(entry, out, depth + 1, max_depth)
        return
    if isinstance(node, dict):
        for key, value in node.items():
            if key in NEVER_NARRATE_KEYS:
                continue
            if key in NARRATABLE_KEYS or isinstance(value, (dict, list)):
                collect_phrases(value, out, depth + 1, max_depth)


def fallback_script(slide: dict) -> str:
    """Compose an 'intisari' narration from the slide's own content."""
    if not isinstance(slide, dict):
        return ""
    phrases = []
    collect_phrases(slide, phrases)
    seen = set()
    unique = []
    for p in phrases:
        key = p.lower()
        if key in seen:
            continue
        seen.add(key)
        # Normalise sentence endings so the join below never yields "..".
        unique.append(p.rstrip().rstrip("."))
    if not unique:
        return ""
    text = re.sub(r"\s+", " ", ". ".join(u for u in unique if u)).strip()
    if not text.endswith((".", "!", "?")):
        text += "."
    words = text.split()
    if len(words) > MAX_FALLBACK_WORDS:
        text = " ".join(words[:MAX_FALLBACK_WORDS]).rstrip(",;:") + "."
    return text


def resolve_narrations(content: dict):
    """Return (entries, slide_count, problems). entries = [(idx, text, source)]."""
    slides = content.get("slides") if isinstance(content.get("slides"), list) else []
    narration_map = content.get("narration") if isinstance(content.get("narration"), dict) else {}

    problems = []
    entries = []

    if slides:
        indices = list(range(len(slides)))
    elif narration_map:
        indices = sorted(int(k) for k in narration_map.keys() if str(k).lstrip("-").isdigit())
    else:
        return [], 0, ["no 'slides' array and no 'narration' map in the input file"]

    extra_keys = sorted(
        str(k) for k in narration_map.keys()
        if str(k).lstrip("-").isdigit() and slides and int(k) >= len(slides)
    )
    if extra_keys:
        problems.append(
            f"narration keys beyond the last slide (slides={len(slides)}): {', '.join(extra_keys)}"
        )

    for idx in indices:
        slide = slides[idx] if slides and idx < len(slides) else {}
        explicit = slide.get("narration") if isinstance(slide, dict) else None
        if isinstance(explicit, str) and explicit.strip():
            entries.append((idx, explicit.strip(), "slide.narration"))
            continue
        mapped = narration_map.get(str(idx), narration_map.get(idx))
        if isinstance(mapped, str) and mapped.strip():
            entries.append((idx, mapped.strip(), "narration[%d]" % idx))
            continue
        entries.append((idx, "", "missing"))

    return entries, len(slides), problems


# ────────────────────────────────────────────────────────────────────────────
# Text conditioning
# ────────────────────────────────────────────────────────────────────────────
def apply_pronunciation(text: str, table: dict) -> str:
    if not table:
        return text
    # Whole-term matching, longest first, so "PT PP" wins over "PP".
    for term in sorted(table, key=len, reverse=True):
        spoken = str(table[term])
        pattern = re.compile(rf"(?<![A-Za-z0-9]){re.escape(term)}(?![A-Za-z0-9])")
        text = pattern.sub(spoken, text)
    return text


def strip_markup(text: str) -> str:
    """Narration may carry the same Safe HTML/Markdown as slide copy."""
    text = re.sub(r"<br\s*/?>", ". ", text, flags=re.I)
    text = re.sub(r"</(p|div|li|h[1-6])>", ". ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    return re.sub(r"\s+", " ", text).strip()


def prepare_text(raw: str, table: dict) -> str:
    return apply_pronunciation(strip_markup(raw), table)


# ────────────────────────────────────────────────────────────────────────────
# Synthesis
# ────────────────────────────────────────────────────────────────────────────
async def generate_unit_audio(unit_id, text: str, output_path: Path, voice: str, rate: str):
    import edge_tts
    print(f"[*] unit_{unit_id}.mp3 ← {len(text)} chars | voice={voice} rate={rate}")
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(str(output_path))
    size_kb = output_path.stat().st_size / 1024
    print(f"    ✓ {output_path.name} ({size_kb:.1f} KB)")


def report_coverage(entries):
    explicit = [e for e in entries if e[2] not in ("missing", "fallback")]
    fallback = [e for e in entries if e[2] == "fallback"]
    missing = [e for e in entries if e[2] == "missing"]
    print(f"  explicit narration : {len(explicit)}")
    print(f"  fallback (intisari): {len(fallback)}")
    print(f"  missing            : {len(missing)}")
    if missing:
        print("  missing indices    : " + ", ".join(str(e[0]) for e in missing))
    weak = [e for e in fallback if len(e[1].split()) < 8]
    if weak:
        print("  WARN: thin fallback scripts (< 8 words) at indices: "
              + ", ".join(str(e[0]) for e in weak))
    return missing


async def run(args):
    content_path = Path(args.content).resolve()
    if not content_path.exists():
        print(f"[!] Error: file not found: {content_path}", file=sys.stderr)
        sys.exit(1)

    raw = load_json(content_path)

    # Standalone narration JSON: {"0": "text", "1": "text"}
    if isinstance(raw, dict) and "narration" not in raw and raw and all(isinstance(v, str) for v in raw.values()):
        raw = {"narration": raw, "slides": []}

    entries, slide_count, problems = resolve_narrations(raw)
    if not entries:
        print(f"[!] Error: no narration found in {content_path}", file=sys.stderr)
        for p in problems:
            print(f"    - {p}", file=sys.stderr)
        print('    Expected either slides[N].narration or {"narration": {"0": "..."}}', file=sys.stderr)
        sys.exit(1)

    for p in problems:
        print(f"[!] WARN: {p}", file=sys.stderr)

    # Pronunciation table
    table = {} if args.no_phonetic else dict(PRONUNCIATION_MAP)
    if args.pronunciation_file:
        extra = load_json(Path(args.pronunciation_file).resolve())
        if not isinstance(extra, dict):
            print("[!] Error: --pronunciation-file must contain a JSON object", file=sys.stderr)
            sys.exit(1)
        table.update({str(k): str(v) for k, v in extra.items()})

    # Resolve text (explicit → fallback)
    slides = raw.get("slides") if isinstance(raw.get("slides"), list) else []
    resolved = []
    for idx, text, source in entries:
        if source == "missing" and not args.no_fallback:
            text = fallback_script(slides[idx] if idx < len(slides) else {})
            source = "fallback" if text else "missing"
        resolved.append((idx, prepare_text(text, table) if text else "", source))

    print("\n🎙️  Modul PP Audio Narration Builder")
    print("=" * 52)
    print(f"Source        : {content_path.name}")
    print(f"Slides        : {slide_count or len(resolved)}")
    print(f"Voice         : {VOICE_CHOICES.get(args.voice.lower(), args.voice)}")
    print(f"Rate          : {args.rate}")
    print(f"Phonetic map  : {'off' if args.no_phonetic else str(len(table)) + ' entries'}")
    print("Coverage:")
    report_coverage(resolved)

    if args.check:
        print("\n[OK] --check: no audio generated.")
        return

    targets = resolved
    if args.unit is not None:
        targets = [e for e in resolved if e[0] == int(args.unit)]
        if not targets:
            print(f"[!] Error: unit index {args.unit} is out of range", file=sys.stderr)
            sys.exit(1)

    if args.dry_run:
        print("\n--- DRY RUN: exact script that would be synthesised ---")
        for idx, text, source in targets:
            print(f"\n[unit_{idx}] ({source}, {len(text.split())} words)")
            print(text if text else "  <empty — would be skipped>")
        print("\n[OK] --dry-run: no audio generated.")
        return

    try:
        import edge_tts  # noqa: F401
    except ImportError:
        print("\n[!] 'edge-tts' is not installed.", file=sys.stderr)
        print("    pip install edge-tts", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    voice = VOICE_CHOICES.get(args.voice.lower(), args.voice)

    done = skipped = failed = 0
    for idx, text, source in targets:
        if not text:
            print(f"[!] Skipping unit_{idx}: no narration text.")
            skipped += 1
            continue
        out_file = out_dir / f"unit_{idx}.mp3"
        if out_file.exists() and not args.force:
            size_kb = out_file.stat().st_size / 1024
            print(f"[=] unit_{idx}.mp3 exists ({size_kb:.1f} KB) — use --force to overwrite")
            skipped += 1
            continue
        try:
            await generate_unit_audio(idx, text, out_file, voice, args.rate)
            done += 1
        except Exception as e:  # network/TTS failures must not abort the whole batch
            print(f"[!] Failed unit_{idx}.mp3: {e}", file=sys.stderr)
            failed += 1

    print(f"\n✓ Generated {done}, skipped {skipped}, failed {failed} → {out_dir}")
    if failed:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Modul PP Edge-TTS Narration Generator")
    parser.add_argument("--content", required=True, help="Path to content.json or a narration JSON file")
    parser.add_argument("--output-dir", default="./audio", help="Directory for MP3 files (default: ./audio)")
    parser.add_argument("--voice", default="gadis", help="gadis, ardi, jenny, guy, or a full Edge-TTS voice name")
    parser.add_argument("--rate", default="+0%", help="Speed modifier, e.g. +0%%, +10%%, -5%%")
    parser.add_argument("--unit", default=None, help="Generate one unit only (e.g. 0)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing MP3 files")
    parser.add_argument("--dry-run", action="store_true", help="Print scripts without calling TTS")
    parser.add_argument("--check", action="store_true", help="Report narration coverage only")
    parser.add_argument("--no-phonetic", action="store_true", help="Disable the pronunciation dictionary")
    parser.add_argument("--no-fallback", action="store_true", help="Disable the intisari auto-narration fallback")
    parser.add_argument("--pronunciation-file", default=None,
                        help="JSON file with extra {TERM: 'respell'} entries")
    args = parser.parse_args()

    asyncio.run(run(args))


if __name__ == "__main__":
    main()
