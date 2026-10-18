#!/usr/bin/env python3
"""
validate_content.py — Schema Validator for E-Learning Module content.json

USAGE
  python3 validate_content.py <content.json> [schema.json] [--strict] [--quiet]

Default schema path: ../assets/content.schema.json (relative to this script).

Works with zero third-party dependencies. If the `jsonschema` package happens to
be installed it is used; otherwise a built-in validator handles the JSON Schema
subset that content.schema.json actually uses:

  $ref, type, properties, required, additionalProperties, items, enum, const,
  oneOf, minItems, maxItems, minimum, maximum, pattern, minLength, maxLength

BEYOND THE SCHEMA
  The raw schema error for a bad slide is "matches 0 of 18 allowed schemas",
  which tells an author nothing. This script therefore re-validates every slide
  against its own type definition and reports the precise missing/unknown fields,
  suggests the closest slide type for a typo, and runs semantic checks the schema
  cannot express:
    - quiz correctIndex must be inside its options array
    - quiz question ids must be unique
    - fillIn questions need at least one accepted answer
    - units[].duration should look like MM:SS
    - course.totalQuestions should match the real question count
    - quiz-level passingScore should agree with course.passingScore
    - narration coverage (which slides would have no audio/CC)
    - course.certificate.template must exist, and a custom brand needs colours

Exit codes:
  0 = valid (warnings allowed unless --strict)
  1 = invalid
"""
import argparse
import difflib
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

try:
    import jsonschema as _jsonschema
except ImportError:
    _jsonschema = None


# ────────────────────────────────────────────────────────────────────────────
# Built-in validator (JSON Schema draft-7 subset used by content.schema.json)
# ────────────────────────────────────────────────────────────────────────────
class SchemaError:
    def __init__(self, path, message):
        self.path = "/".join(str(p) for p in path) or "<root>"
        self.message = message

    def __repr__(self):
        return f"{self.path}: {self.message}"


def _type_matches(value, name):
    if name == "object":
        return isinstance(value, dict)
    if name == "array":
        return isinstance(value, list)
    if name == "string":
        return isinstance(value, str)
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if name == "boolean":
        return isinstance(value, bool)
    if name == "null":
        return value is None
    return True


def _resolve_ref(ref, root):
    if not ref.startswith("#/"):
        raise ValueError(f"unsupported $ref: {ref}")
    node = root
    for token in ref[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or token not in node:
            raise ValueError(f"unresolvable $ref: {ref}")
        node = node[token]
    return node


def validate_node(value, schema, root, path, errors):
    """Validate `value` against `schema`, appending SchemaError to `errors`."""
    if schema is True or schema is None:
        return
    if schema is False:
        errors.append(SchemaError(path, "no value is allowed here"))
        return
    if not isinstance(schema, dict):
        return

    # In draft-7 a $ref replaces every sibling keyword.
    if "$ref" in schema:
        validate_node(value, _resolve_ref(schema["$ref"], root), root, path, errors)
        return

    # ── type ────────────────────────────────────────────────────────────────
    expected = schema.get("type")
    if expected is not None:
        allowed = expected if isinstance(expected, list) else [expected]
        if not any(_type_matches(value, t) for t in allowed):
            if isinstance(value, bool):
                shown = "boolean"
            elif isinstance(value, dict):
                shown = "object"
            elif isinstance(value, list):
                shown = "array"
            elif isinstance(value, str):
                shown = f"string {value!r}" if len(value) <= 60 else "string"
            else:
                shown = repr(value)
            errors.append(
                SchemaError(path, f"{shown} is not of type {'/'.join(allowed)}")
            )
            return

    # ── const / enum ────────────────────────────────────────────────────────
    if "const" in schema and value != schema["const"]:
        errors.append(
            SchemaError(path, f"{value!r} was not equal to the constant {schema['const']!r}")
        )
    if "enum" in schema and value not in schema["enum"]:
        allowed = ", ".join(repr(v) for v in schema["enum"])
        errors.append(SchemaError(path, f"{value!r} is not one of [{allowed}]"))

    # ── oneOf ───────────────────────────────────────────────────────────────
    if "oneOf" in schema:
        matches = 0
        for sub in schema["oneOf"]:
            sub_errors = []
            validate_node(value, sub, root, path, sub_errors)
            if not sub_errors:
                matches += 1
        if matches != 1:
            hint = ""
            discriminator = value.get("type") if isinstance(value, dict) else None
            if discriminator is not None:
                hint = f" (slide/question type {discriminator!r})"
            errors.append(
                SchemaError(
                    path,
                    f"matches {matches} of {len(schema['oneOf'])} allowed schemas, "
                    f"expected exactly 1{hint}",
                )
            )

    # ── string constraints ──────────────────────────────────────────────────
    if isinstance(value, str):
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(
                SchemaError(path, f"{value!r} does not match pattern {schema['pattern']!r}")
            )
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(SchemaError(path, f"{value!r} is shorter than {schema['minLength']}"))
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append(SchemaError(path, f"{value!r} is longer than {schema['maxLength']}"))

    # ── numeric constraints ─────────────────────────────────────────────────
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(
                SchemaError(path, f"{value!r} is less than the minimum {schema['minimum']!r}")
            )
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(
                SchemaError(path, f"{value!r} is greater than the maximum {schema['maximum']!r}")
            )

    # ── object constraints ──────────────────────────────────────────────────
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                errors.append(SchemaError(path, f"{key!r} is a required property"))
        for key, sub in props.items():
            if key in value:
                validate_node(value[key], sub, root, path + [key], errors)
        extra = schema.get("additionalProperties", True)
        if extra is not True:
            for key in value:
                if key in props:
                    continue
                if extra is False:
                    errors.append(
                        SchemaError(path, f"additional property {key!r} is not allowed")
                    )
                else:
                    validate_node(value[key], extra, root, path + [key], errors)

    # ── array constraints ───────────────────────────────────────────────────
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(
                SchemaError(path, f"has {len(value)} items, minimum is {schema['minItems']}")
            )
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(
                SchemaError(path, f"has {len(value)} items, maximum is {schema['maxItems']}")
            )
        items = schema.get("items")
        if isinstance(items, dict):
            for idx, entry in enumerate(value):
                validate_node(entry, items, root, path + [idx], errors)
        elif isinstance(items, list):
            for idx, sub in enumerate(items):
                if idx < len(value):
                    validate_node(value[idx], sub, root, path + [idx], errors)


def validate(content, schema):
    errors = []
    validate_node(content, schema, schema, [], errors)
    return errors


# ────────────────────────────────────────────────────────────────────────────
# Slide-aware diagnostics
# ────────────────────────────────────────────────────────────────────────────
def _resolve(schema, node, seen=None):
    seen = seen or set()
    while isinstance(node, dict) and "$ref" in node:
        ref = node["$ref"]
        if ref in seen:
            return None
        seen.add(ref)
        try:
            node = _resolve_ref(ref, schema)
        except ValueError:
            return None
    return node


def slide_definitions(schema):
    """{slideType: definition} resolved from definitions.slide.oneOf."""
    node = _resolve(schema, schema.get("definitions", {}).get("slide"))
    if not isinstance(node, dict):
        return {}
    defs = {}
    for branch in node.get("oneOf", []):
        branch = _resolve(schema, branch)
        if not isinstance(branch, dict):
            continue
        const = (branch.get("properties", {}).get("type", {}) or {}).get("const")
        if const:
            defs[const] = branch
    return defs


def slide_diagnostics(content, schema, defs):
    """Precise per-slide errors, replacing the generic oneOf message."""
    errors = []
    slides = content.get("slides")
    if not isinstance(slides, list):
        return errors
    for i, slide in enumerate(slides):
        if not isinstance(slide, dict):
            continue
        stype = slide.get("type")
        if stype is None:
            errors.append(SchemaError(["slides", i], "'type' is a required property"))
            continue
        if stype not in defs:
            close = difflib.get_close_matches(str(stype), list(defs), n=3, cutoff=0.5)
            hint = f" Did you mean {', '.join(repr(c) for c in close)}?" if close else ""
            errors.append(
                SchemaError(["slides", i, "type"],
                            f"{stype!r} is not a supported slide type.{hint} "
                            f"Supported: {', '.join(sorted(defs))}")
            )
            continue
        sub_errors = []
        validate_node(slide, defs[stype], schema, ["slides", i], sub_errors)
        errors.extend(sub_errors)
    return errors


# ────────────────────────────────────────────────────────────────────────────
# Interactivity analysis
# Keep these sets in sync with references/interactivity_patterns.md §2 and
# references/interactivity_roadmap.md. scripts/self_check.py asserts that every
# slide type declared in the schema is classified here, so a new renderer cannot
# silently escape the inventory.
# ────────────────────────────────────────────────────────────────────────────
ACTIVE_TYPES = {
    "quiz",              # summative: decides, gets feedback, score counts
    "scenarioPicker",    # one-step decision under a constraint
    "treeCanvas",        # explore: hotspots + role filter on a diagram
    "hotspotImage",      # explore/find: hotspot, labeled graphic, guided image
    "branchingScenario", # decide through a tree, with consequences
    "dragDropSet",       # categorize / sequence / match by manipulation
}
SEMI_TYPES = {
    "tabbedAccordion", "faqAccordion", "twoCardAccordion", "docTabs",
    "imageGallery", "videoEmbed", "verificationMatrix",
}
PASSIVE_TYPES = {
    "cover", "cardList", "kpiDashboard", "riskCards", "stepByStep",
    "comparisonTable", "calloutBox", "summaryCertificate",
}

# NOTE: `checkpoint` is deliberately NOT a slide type — it is an optional block that
# turns ANY slide active (see interactivity_analysis). Keeping it out of these sets
# is what makes the schema/classification parity check in self_check meaningful.

# Decided but not implemented yet — see references/interactivity_roadmap.md.
# Remove an entry as soon as its renderer + schema branch land.
PLANNED_TYPES = set()  # every decided type has shipped; add ids here while a type is in flight

GUIDANCE_ACTIVE_RATIO = 0.20   # interactivity_patterns.md §4 rule 2
GUIDANCE_MAX_PASSIVE_RUN = 5   # interactivity_patterns.md §4 rule 3


def slide_class(slide_type):
    if slide_type in ACTIVE_TYPES:
        return "active"
    if slide_type in SEMI_TYPES:
        return "semi"
    if slide_type in PASSIVE_TYPES:
        return "passive"
    return "unknown"


def interactivity_analysis(content: dict):
    """Classify slides and return (stats, warnings)."""
    slides = content.get("slides") if isinstance(content.get("slides"), list) else []
    classes = []
    checkpoint_count = 0
    for i, slide in enumerate(slides):
        stype = slide.get("type") if isinstance(slide, dict) else None
        cp = slide.get("checkpoint") if isinstance(slide, dict) else None
        has_checkpoint = isinstance(cp, dict) and bool(cp.get("question"))
        if has_checkpoint:
            checkpoint_count += 1
        # A checkpoint makes an otherwise passive slide active: the learner must act.
        classes.append((i, stype, "active" if has_checkpoint else slide_class(stype)))

    total = len(classes)
    n_active = sum(1 for _, _, c in classes if c == "active")
    n_semi = sum(1 for _, _, c in classes if c == "semi")
    n_passive = sum(1 for _, _, c in classes if c == "passive")
    n_unknown = sum(1 for _, _, c in classes if c == "unknown")

    stats = {
        "total": total, "active": n_active, "semi": n_semi,
        "passive": n_passive, "unknown": n_unknown,
        "ratio": (n_active / total) if total else 0.0,
        "quiz_count": sum(1 for _, t, _ in classes if t == "quiz"),
        "checkpoint_count": checkpoint_count,
        "longest_passive_run": 0,
    }

    warnings = []
    if not total:
        return stats, warnings

    longest_run, run, run_end = 0, 0, 0
    for i, _, c in classes:
        if c == "active":
            run = 0
        else:
            run += 1
            if run > longest_run:
                longest_run, run_end = run, i
    stats["longest_passive_run"] = longest_run

    if n_unknown:
        unknown = sorted({str(t) for _, t, c in classes if c == "unknown"})
        warnings.append(
            "slide type belum terklasifikasi untuk analitik interaktivitas: " + ", ".join(unknown)
            + " — perbarui ACTIVE/SEMI/PASSIVE_TYPES di validate_content.py + interactivity_patterns.md"
        )

    if n_active == 0:
        warnings.append(
            f"modul 100% pasif ({total} slide, 0 interaksi aktif). Learner hanya membaca; "
            "pertimbangkan 1–2 checkpoint di tengah materi (lihat interactivity_patterns.md)."
        )
    elif total >= 6 and stats["ratio"] < GUIDANCE_ACTIVE_RATIO:
        warnings.append(
            f"kepadatan interaksi {stats['ratio']*100:.1f}% ({n_active}/{total}) — di bawah pedoman "
            f"{GUIDANCE_ACTIVE_RATIO*100:.0f}%. Tambah 1–2 checkpoint/branching di bagian materi padat."
        )

    if stats["quiz_count"] == 0:
        warnings.append(
            "tidak ada slide 'quiz': modul tidak punya asesmen sumatif, jadi sertifikat tidak akan "
            "pernah terbuka dan skor tidak terkirim ke webhook."
        )
    elif n_active == stats["quiz_count"] == 1:
        warnings.append(
            "interaktivitas hanya berupa kuis di akhir (assessment-only). Latihan formatif di tengah "
            "modul memberi efek retensi yang jauh lebih besar."
        )

    if longest_run > GUIDANCE_MAX_PASSIVE_RUN:
        warnings.append(
            f"{longest_run} slide non-aktif berurutan (slide {run_end - longest_run + 1}–{run_end}). "
            f"Pedoman: maksimal {GUIDANCE_MAX_PASSIVE_RUN}. Sisipkan checkpoint/branching."
        )

    for i, stype, c in classes[:2]:
        if c == "active":
            warnings.append(
                f"slides[{i}] ({stype}) sudah interaktif di dua slide pertama — learner belum "
                "mendapat materi apa pun. Pedoman: dua slide pertama pasif."
            )

    return stats, warnings


def format_interactivity_line(stats: dict) -> str:
    if not stats.get("total"):
        return "Interaktivitas: —"
    cp = stats.get("checkpoint_count") or 0
    cp_note = f" · {cp} checkpoint" if cp else ""
    return (
        f"Interaktivitas: {stats['active']}/{stats['total']} aktif "
        f"({stats['ratio']*100:.0f}%) · {stats['semi']} semi · {stats['passive']} pasif"
        f"{cp_note} · pedoman ≥{GUIDANCE_ACTIVE_RATIO*100:.0f}%"
    )


# ────────────────────────────────────────────────────────────────────────────
# Learner-facing title lint: document clause numbering must not leak into titles
# ────────────────────────────────────────────────────────────────────────────
DOC_NUMBER_PATTERNS = [
    (re.compile(r"\bPoin\s+\d+(?:[.,]\d+)*", re.I), "menyebut 'Poin N'"),
    (re.compile(r"\b\d+\.\d+(?:\.\d+)*\b"), "berisi nomor klausul (mis. 6.1.2)"),
    (re.compile(r"\bPasal\s+\d+", re.I), "menyebut 'Pasal N'"),
    (re.compile(r"\bKlausul\s+\d+", re.I), "menyebut 'Klausul N'"),
    (re.compile(r"\bButir\s+\d+", re.I), "menyebut 'Butir N'"),
    (re.compile(r"\bAyat\s+\(?\d+\)?", re.I), "menyebut 'Ayat N'"),
    (re.compile(r"\bLampiran\s+[IVXLC0-9]+", re.I), "menyebut 'Lampiran N'"),
    (re.compile(r"\bs\.?\s?d\.?\s*\d", re.I), "berisi rentang 's.d.'"),
    (re.compile(r"\b(?:Ketentuan Umum|Ruang Lingkup)\b[^\n]{0,24}\d", re.I),
     "menggabungkan judul generik dengan angka"),
]

# Only learner-facing labels — body copy may legitimately cite clauses.
# Only titles/labels: lead and body copy may legitimately cite clause numbers.
LINT_KEYS = ("title", "heroTitle", "label")
LINT_LIST_KEYS = ("tabs", "cards", "steps", "kpis", "risks", "images", "items", "seasons")


def title_number_warnings(content: dict, limit: int = 8):
    out = []
    slides = content.get("slides") if isinstance(content.get("slides"), list) else []

    def check(value, where):
        if not isinstance(value, str) or len(value) < 3:
            return
        for pattern, reason in DOC_NUMBER_PATTERNS:
            match = pattern.search(value)
            if match:
                out.append(
                    f"{where} {reason}: {value.strip()[:60]!r} — judul untuk learner sebaiknya "
                    "tematik (mis. 'Prinsip Parenting, Grading & Perjanjian'), bukan nomor dokumen"
                )
                return

    for i, slide in enumerate(slides):
        if not isinstance(slide, dict):
            continue
        for key in LINT_KEYS:
            check(slide.get(key), f"slides[{i}].{key}")
        for key in LINT_LIST_KEYS:
            entries = slide.get(key)
            if not isinstance(entries, list):
                continue
            for j, entry in enumerate(entries):
                if not isinstance(entry, dict):
                    continue
                for sub in ("title", "label", "q", "name"):
                    check(entry.get(sub), f"slides[{i}].{key}[{j}].{sub}")
        if len(out) >= limit:
            break
    return out[:limit]


# ────────────────────────────────────────────────────────────────────────────
# Semantic checks the schema cannot express
# ────────────────────────────────────────────────────────────────────────────
def question_warnings(q: dict, where: str):
    """Per-question semantic checks, shared by quiz slides and checkpoints."""
    out = []
    qtype = q.get("type")
    if qtype == "mcq":
        options = q.get("options")
        idx = q.get("correctIndex")
        if isinstance(options, list) and isinstance(idx, int) and not (0 <= idx < len(options)):
            out.append(
                f"{where}.correctIndex {idx} is out of range for {len(options)} options "
                f"(0..{len(options) - 1}) — this question can never be answered correctly"
            )
    elif qtype == "fillIn":
        accepted = q.get("acceptedAnswers")
        if isinstance(accepted, list) and not [a for a in accepted if str(a).strip()]:
            out.append(f"{where}.acceptedAnswers is empty — this question can never be passed")
    elif qtype == "multipleResponse":
        options = q.get("options") or []
        idxs = q.get("correctIndexes") or []
        bad = [i for i in idxs if isinstance(i, int) and not (0 <= i < len(options))]
        if bad:
            out.append(
                f"{where}.correctIndexes {bad} out of range for {len(options)} options — "
                "those answers can never be selected"
            )
        if len(set(idxs)) != len(idxs):
            out.append(f"{where}.correctIndexes contains duplicates")
        if options and idxs and len(set(idxs)) == len(options):
            out.append(
                f"{where}.correctIndexes selects every option — this question cannot discriminate; "
                "make at least one option plausible-but-wrong"
            )
    elif qtype == "ordering":
        items = q.get("items") or []
        correct = q.get("correctOrder")
        if correct is not None and sorted(correct) != list(range(len(items))):
            out.append(
                f"{where}.correctOrder must be a permutation of 0..{len(items) - 1} "
                f"(got {correct}) — grading would always fail"
            )
    elif qtype == "matching":
        pairs = q.get("pairs") or []
        rights = [str((p or {}).get("right", "")).strip().lower() for p in pairs]
        if len(set(rights)) != len(rights):
            out.append(
                f"{where}.pairs has duplicate right-hand labels — the pairing becomes ambiguous "
                "for the learner (and impossible to grade fairly)"
            )
        lefts = [str((p or {}).get("left", "")).strip().lower() for p in pairs]
        if len(set(lefts)) != len(lefts):
            out.append(f"{where}.pairs has duplicate left-hand labels")
    elif qtype == "numeric":
        answer = q.get("answer")
        if not isinstance(answer, (int, float)) or isinstance(answer, bool):
            out.append(f"{where}.answer must be a number")
        tol = q.get("tolerance")
        if isinstance(tol, (int, float)) and tol < 0:
            out.append(f"{where}.tolerance must be >= 0")
    return out


def semantic_warnings(content, content_path: Path):
    warnings = []
    course = content.get("course") or {}
    slides = content.get("slides") if isinstance(content.get("slides"), list) else []
    units = content.get("units") if isinstance(content.get("units"), list) else []

    # units[].duration format
    for i, unit in enumerate(units):
        if not isinstance(unit, dict):
            continue
        duration = unit.get("duration")
        if isinstance(duration, str) and duration and not re.fullmatch(r"\d{1,2}:\d{2}", duration):
            warnings.append(f"units[{i}].duration {duration!r} is not MM:SS")

    # Quiz integrity
    real_questions = 0
    for i, slide in enumerate(slides):
        if not isinstance(slide, dict) or slide.get("type") != "quiz":
            continue
        questions = slide.get("questions") if isinstance(slide.get("questions"), list) else []
        real_questions += len(questions)
        seen_ids = set()
        for qi, q in enumerate(questions):
            if not isinstance(q, dict):
                continue
            where = f"slides[{i}].questions[{qi}]"
            qid = q.get("id")
            if qid is not None:
                if qid in seen_ids:
                    warnings.append(f"{where}.id {qid!r} is duplicated inside this quiz")
                seen_ids.add(qid)
            warnings.extend(question_warnings(q, where))
        slide_passing = slide.get("passingScore")
        if isinstance(slide_passing, int):
            warnings.append(
                f"slides[{i}].passingScore ({slide_passing}) is not read by the engine — the pass "
                "threshold is course-level. Set course.passingScore instead."
            )

    # Checkpoint questions are formative, but they still must be answerable.
    for i, slide in enumerate(slides):
        if not isinstance(slide, dict):
            continue
        cp = slide.get("checkpoint")
        if isinstance(cp, dict) and isinstance(cp.get("question"), dict):
            warnings.extend(question_warnings(cp["question"], f"slides[{i}].checkpoint.question"))

    # Branching scenario graph integrity — cross-references the schema cannot express.
    for i, slide in enumerate(slides):
        if not isinstance(slide, dict) or slide.get("type") != "branchingScenario":
            continue
        nodes = [n for n in (slide.get("nodes") or []) if isinstance(n, dict)]
        ids = [str(n.get("id")) for n in nodes]
        if len(set(ids)) != len(ids):
            warnings.append(f"slides[{i}].nodes has duplicate ids — choices may jump to the wrong node")
        start = slide.get("start")
        if start is not None and str(start) not in ids:
            warnings.append(f"slides[{i}].start {start!r} does not match any node id")
        endings = [n for n in nodes if n.get("ending") is True]
        if not endings:
            warnings.append(
                f"slides[{i}] has no ending node — the learner can never finish this scenario"
            )
        elif not any(n.get("correct") is True for n in endings):
            warnings.append(
                f"slides[{i}] has no ending with correct:true — the success path can never fire"
            )
        for node in nodes:
            nid = node.get("id")
            choices = node.get("choices") if isinstance(node.get("choices"), list) else []
            if not choices and node.get("ending") is not True:
                warnings.append(
                    f"slides[{i}].nodes[{nid}] has no choices and is not an ending — dead end"
                )
            for ci, choice in enumerate(choices):
                if not isinstance(choice, dict):
                    continue
                nxt = choice.get("next")
                if nxt is not None and str(nxt) not in ids:
                    warnings.append(
                        f"slides[{i}].nodes[{nid}].choices[{ci}].next {nxt!r} does not match any node id"
                    )

    declared_questions = course.get("totalQuestions")
    if isinstance(declared_questions, int) and real_questions and declared_questions != real_questions:
        warnings.append(
            f"course.totalQuestions ({declared_questions}) != actual question count ({real_questions})"
        )

    # Narration coverage
    narration_map = content.get("narration") if isinstance(content.get("narration"), dict) else {}
    if slides:
        missing = []
        for i, slide in enumerate(slides):
            explicit = slide.get("narration") if isinstance(slide, dict) else None
            if isinstance(explicit, str) and explicit.strip():
                continue
            if isinstance(narration_map.get(str(i)), str) and narration_map[str(i)].strip():
                continue
            missing.append(i)
        if missing:
            warnings.append(
                f"{len(missing)}/{len(slides)} slides have no narration "
                f"(indices: {', '.join(str(m) for m in missing[:12])}"
                + (", …" if len(missing) > 12 else "")
                + "). generate_audio.py will fall back to an intisari script, and the CC dock "
                  "will be empty for those slides."
            )

    # Certificate configuration
    cert = course.get("certificate") if isinstance(course.get("certificate"), dict) else {}
    template = cert.get("template")
    if template:
        tpl = Path(template)
        if not tpl.is_absolute():
            tpl = (content_path.parent / tpl).resolve()
        if not tpl.exists():
            warnings.append(f"course.certificate.template not found: {tpl}")
    if cert.get("pageWidthMm") or cert.get("pageHeightMm"):
        if not (cert.get("pageWidthMm") and cert.get("pageHeightMm")):
            warnings.append(
                "course.certificate sets only one of pageWidthMm/pageHeightMm; "
                "the other falls back to the pageSize default, which can distort the print area"
            )

    # Brand completeness for a custom palette
    brand = content.get("brand") if isinstance(content.get("brand"), dict) else {}
    if brand.get("preset") == "custom":
        for field in ("primary", "secondary", "accent"):
            if not brand.get(field):
                warnings.append(
                    f"brand.preset is 'custom' but brand.{field} is missing — the shell default "
                    "palette will be used for that token"
                )
    if isinstance(brand, dict) and not brand.get("preset"):
        warnings.append("brand.preset is missing; the builder defaults to 'ptpp'")

    return warnings


# ────────────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="Validate a Modul PP content.json")
    ap.add_argument("content", help="Path to content.json")
    ap.add_argument("schema", nargs="?", default=None, help="Path to content.schema.json")
    ap.add_argument("--strict", action="store_true", help="Treat semantic warnings as errors")
    ap.add_argument("--quiet", action="store_true", help="Only print the final verdict")
    args = ap.parse_args()

    content_path = Path(args.content)
    if not content_path.exists():
        print(f"ERROR: content.json not found: {content_path}", file=sys.stderr)
        sys.exit(1)

    schema_path = Path(args.schema) if args.schema else Path(__file__).parent.parent / "assets" / "content.schema.json"
    if not schema_path.exists():
        print(f"ERROR: schema not found: {schema_path}", file=sys.stderr)
        sys.exit(1)

    try:
        content = json.loads(content_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"✗ Invalid schema JSON: {e}", file=sys.stderr)
        sys.exit(1)

    # ── Schema validation ───────────────────────────────────────────────────
    if _jsonschema is not None:
        validator = _jsonschema.Draft7Validator(schema)
        raw_errors = [
            SchemaError(list(err.absolute_path), err.message)
            for err in validator.iter_errors(content)
        ]
    else:
        raw_errors = validate(content, schema)

    # Replace unhelpful slide-level "matches N of 18 / not valid under any of the
    # given schemas" errors with precise per-slide diagnostics.
    defs = slide_definitions(schema)
    precise = slide_diagnostics(content, schema, defs)
    generic_slide_errors = [
        e for e in raw_errors
        if e.path.startswith("slides/") and (
            "allowed schemas" in e.message
            or "is not valid under any of the given schemas" in e.message
            or "does not match" in e.message and "oneOf" in e.message
        )
    ]
    if generic_slide_errors:
        raw_errors = [e for e in raw_errors if e not in generic_slide_errors]
        flagged = {e.path.split("/")[1] for e in generic_slide_errors}
        raw_errors.extend([e for e in precise if e.path.split("/")[1] in flagged])
    elif precise and not raw_errors:
        # Bad content that slipped past the other engine (e.g. a $ref-only schema
        # path). Keep the precise diagnostics rather than reporting "valid".
        raw_errors.extend(precise)

    errors = raw_errors

    # ── Cross-field consistency checks ──────────────────────────────────────
    units = content.get("units", []) if isinstance(content.get("units"), list) else []
    slides = content.get("slides", []) if isinstance(content.get("slides"), list) else []

    if len(units) != len(slides):
        errors.append(
            SchemaError([], f"units.length ({len(units)}) != slides.length ({len(slides)})")
        )

    total_units = (content.get("course") or {}).get("totalUnits")
    if isinstance(total_units, int) and total_units != len(units):
        errors.append(
            SchemaError([], f"course.totalUnits ({total_units}) != units.length ({len(units)})")
        )

    # ── Semantic advisories (printed whether or not there are hard errors) ──
    warnings = semantic_warnings(content, content_path)
    inter_stats, inter_warnings = interactivity_analysis(content)
    warnings.extend(inter_warnings)
    warnings.extend(title_number_warnings(content))
    if warnings and not args.quiet:
        print(f"! {len(warnings)} advisory warning(s):", file=sys.stderr)
        for i, w in enumerate(warnings, 1):
            print(f"  [{i}] {w}", file=sys.stderr)

    if errors:
        print(f"✗ {len(errors)} validation error(s):", file=sys.stderr)
        for i, err in enumerate(errors[:25], 1):
            print(f"  [{i}] {err.path}: {err.message}", file=sys.stderr)
        if len(errors) > 25:
            print(f"  ... and {len(errors) - 25} more.", file=sys.stderr)
        sys.exit(1)

    if args.strict and warnings:
        print("✗ --strict: treating advisories as failures.", file=sys.stderr)
        sys.exit(1)

    print(f"✓ Valid! {len(units)} units, {len(slides)} slides.")
    if not args.quiet:
        type_counts = {}
        for s in slides:
            t = s.get("type", "?") if isinstance(s, dict) else "?"
            type_counts[t] = type_counts.get(t, 0) + 1
        for t, n in sorted(type_counts.items()):
            print(f"  {t}: {n}")
        print(f"  {format_interactivity_line(inter_stats)}")
    sys.exit(0)


if __name__ == "__main__":
    main()
