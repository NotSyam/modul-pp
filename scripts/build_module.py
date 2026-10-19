#!/usr/bin/env python3
"""
build_module.py — E-Learning Module Builder (Modul PP)

Reads a content.json (matching assets/content.schema.json) + an optional brand
profile (from assets/brand.profiles.json) and an optional custom certificate
template, injects everything into assets/shell.template.html, and writes a
self-contained final HTML module.

USAGE
  python3 build_module.py --content <content.json> --output <out.html> [options]

OPTIONS
  --content PATH            Path to content.json (required)
  --output PATH             Path to write final HTML (required)
  --brand-preset NAME       Override brand.preset in content.json
                            (ptpp | corporate | education | tech-startup | custom)
  --certificate-template P  Override course.certificate.template
  --skill-root PATH         Path to skill root (default: this script's parent dir)
  --validate                Run validate_content.py before building
  --no-validate             Skip validation (default)
  --allow-placeholders      Downgrade leftover-build-placeholder failure to a warning
  --no-contrast-check       Skip the WCAG contrast advisory on brand tokens
  --quiet                   Only print errors and the final path

BUILD ORDER (do not reorder — each step is order-sensitive)
  1. brand color tokens   — rewrites the template's *palette*, never user content
  2. __PLACEHOLDER__      — build-time scalars (course chrome + certificate)
  3. {{certificate}}      — optional custom certificate template
  4. COURSE injection     — content.json becomes the COURSE literal

  Steps 1-3 must run BEFORE step 4. If COURSE were injected first, the brand
  palette pass and the placeholder pass would silently rewrite literal hex
  codes and `__TOKEN__` strings that the author wrote inside slide copy.

EXAMPLE
  python3 build_module.py \\
    --content ./content.json \\
    --output ./dist/my-module.html \\
    --validate
"""
import argparse
import base64
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


BUILD_VERSION = "2.0.0"

# The palette the shell template is authored against. Keyed by the UPPERCASE
# hex literal that appears in assets/shell.template.html; the value is the
# brand.profiles.json field that replaces it.
BASE_PALETTE = {
    "#2B73BD": "primary",
    "#205C99": "primaryHover",
    "#5A89B8": "secondary",
    "#7EABD9": "secondaryLight",
    "#38BDF8": "accent",
    "#F0F4F7": "iceBg",
    "#09111E": "darkBg",
    "#111C2E": "darkSurface",
    "#1F2F4A": "darkBorder",
    "#16233B": "darkSubtle",
}

LOGO_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
    ".gif": "image/gif",
}
# Searched in the content.json folder, then its assets/ subfolder.
LOGO_STEMS = ("logo", "brand", "brand-logo", "brand_logo", "logo-brand")
LOGO_DARK_STEMS = ("logo-dark", "logo_dark", "brand-dark", "brand_dark", "logo-white", "logo_white")

HEX_RE = re.compile(r"#[0-9A-Fa-f]{6}")
PLACEHOLDER_RE = re.compile(r"__[A-Z][A-Z0-9_]*__")
CERT_TOKEN_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")
CERT_START = "<!-- CERT-TEMPLATE-START -->"
LOGO_START = "<!-- LOGO-START -->"
LOGO_END = "<!-- LOGO-END -->"
CERT_END = "<!-- CERT-TEMPLATE-END -->"

# Page geometry defaults, in millimetres, keyed by the CSS `@page { size: ... }`
# value that browsers understand.
PAGE_SIZES = {
    "a4 landscape": (297.0, 210.0),
    "a4 portrait": (210.0, 297.0),
    "letter landscape": (279.4, 215.9),
    "letter portrait": (215.9, 279.4),
}

# Labels for the built-in certificate markup. Overridable per project through
# course.certificate.labels so non-Indonesian modules do not print Indonesian
# boilerplate.
DEFAULT_CERT_LABELS = {
    "kicker": "SERTIFIKAT KELULUSAN RESMI E-LEARNING",
    "presentedTo": "Diberikan secara sah kepada:",
    "passNote": "Telah menyelesaikan seluruh modul dan dinyatakan <strong>LULUS UJI PEMAHAMAN (KOMPETEN)</strong>",
    "scoreLabel": "Skor Pemahaman",
    "passThresholdNote": "Lulus Evaluasi Pemahaman (Ambang Batas {passingScore}%)",
    "dateLabel": "Tanggal Kelulusan:",
    "footerNote": "Sistem Autentikasi E-Learning HCM",
}

# Build-time tokens available inside a custom certificate template ({{token}}).
# Runtime values (recipient name/NIP, score, date, registration number) are NOT
# tokens: the template must expose the DOM ids certRecipientName /
# certRecipientNIP / certScoreVal / certDateVal / certNumberLabel, which the
# engine fills on print. tools/verify_module.py enforces those ids.
CERT_TOKEN_KEYS = (
    "judul_kursus", "kode_kursus", "organisasi", "divisi", "penandatangan",
    "judul_sertifikat", "prefix_reg", "tanggal_cetak", "passing_score",
    "label_kicker", "label_presented_to", "label_pass_note", "label_score",
    "label_pass_threshold", "label_date", "label_footer",
    "warna_primary", "warna_secondary", "warna_accent",
)


def log(args, message):
    if not getattr(args, "quiet", False):
        print(message)


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        fail(f"Invalid JSON in {path}: {e}")
    except OSError as e:
        fail(f"Cannot read {path}: {e}")


def resolve_brand(content: dict, profiles: dict, preset_override: str = None) -> dict:
    """Merge: profile preset → inline content.brand overrides → CLI override.
    Returns a flat brand dict with all keys."""
    brand_block = dict(content.get("brand") or {})
    preset_name = preset_override or brand_block.get("preset", "ptpp")

    if preset_name == "custom":
        # Use inline fields verbatim
        return brand_block
    if preset_name not in profiles:
        fail(f"Unknown brand preset '{preset_name}'. Available: {', '.join(profiles.keys())}")

    merged = dict(profiles[preset_name])
    # Overlay inline fields
    for k, v in brand_block.items():
        if k == "preset":
            continue
        merged[k] = v
    merged["preset"] = preset_name
    return merged


def apply_color_tokens(template: str, brand: dict) -> str:
    """Rewrite the template palette in a SINGLE pass.

    A single re.sub() pass is required. Chaining str.replace() calls (the old
    implementation) let one brand token clobber another: replacing `#2B73BD`
    with a value equal to a *later* token's hex (e.g. primary = "1F2F4A") meant
    the later darkBorder pass rewrote the primary-coloured elements too.
    re.sub() scans the original string, so a replacement is never re-scanned.
    """
    def repl(match):
        field = BASE_PALETTE.get(match.group(0).upper())
        if not field:
            return match.group(0)
        value = str(brand.get(field) or "").strip().lstrip("#")
        return f"#{value}" if re.fullmatch(r"[0-9A-Fa-f]{6}", value) else match.group(0)

    return HEX_RE.sub(repl, template)


def _find_logo_file(content_dir: Path, stems, override: str = None):
    """Find a brand image on disk: explicit path first, then conventional names."""
    candidates = []
    if override:
        p = Path(override)
        candidates.append(p if p.is_absolute() else (content_dir / p))
    for base in (content_dir, content_dir / "assets", content_dir / "img", content_dir / "images"):
        for stem in stems:
            for ext in LOGO_MIME:
                candidates.append(base / f"{stem}{ext}")
    for path in candidates:
        try:
            if path.is_file() and path.suffix.lower() in LOGO_MIME:
                return path
        except OSError:
            continue
    return None


def _data_uri(path: Path) -> str:
    mime = LOGO_MIME.get(path.suffix.lower())
    if not mime:
        return ""
    try:
        payload = base64.b64encode(path.read_bytes()).decode("ascii")
    except OSError:
        return ""
    return f"data:{mime};base64,{payload}"


def resolve_logo(content: dict, content_dir: Path, args=None) -> dict:
    """Make `course.logo` self-contained (data URI) and pick up a dark variant.

    A declared path that exists is inlined; a data URI is kept as-is. When nothing is
    declared, conventional filenames next to content.json are used, so a project that
    simply drops `logo.png` beside its content gets a logo without extra config.
    """
    course = content.setdefault("course", {})
    declared = str(course.get("logo") or "").strip()
    info = {"logo": "", "dark": "", "source": "none"}

    if declared.startswith("data:"):
        info["logo"] = declared
        info["source"] = "inline (dari content.json)"
    else:
        path = None
        if declared:
            candidate = Path(declared)
            path = candidate if candidate.is_absolute() else (content_dir / candidate)
            if not (path.is_file() and path.suffix.lower() in LOGO_MIME):
                path = None
        if path is None:
            path = _find_logo_file(content_dir, LOGO_STEMS, getattr(args, "logo", None))
        if path is not None:
            info["logo"] = _data_uri(path)
            if info["logo"]:
                info["source"] = f"inline {path.name} ({path.stat().st_size / 1024:.0f} KB)"
                course["logo"] = info["logo"]

    dark_path = _find_logo_file(content_dir, LOGO_DARK_STEMS,
                                getattr(args, "logo_dark", None)) if info["logo"] else None
    if dark_path is not None:
        info["dark"] = _data_uri(dark_path)
        if info["dark"]:
            info["dark_source"] = dark_path.name
            course["logoDark"] = info["dark"]

    if info["logo"]:
        course.setdefault("logoAlt", course.get("title", "Logo"))
    return info


def monogram_for(brand: dict) -> str:
    """Two-letter fallback when no logo file exists, e.g. 'PT PP (Persero) Tbk' -> 'PP'."""
    name = str(brand.get("orgName") or brand.get("preset") or "Modul").upper()
    skip = {"PT", "TBK", "PERSERO", "PERSEROAN", "CV", "UD", "THE", "OF", "AND", "DAN", "&"}
    words = [w for w in re.findall(r"[A-Z0-9]+", name) if w not in skip]
    if not words:
        return "M"
    if len(words) == 1:
        return words[0][:2]
    return (words[0][:1] + words[1][:1])[:2]


def apply_logo_block(template: str, content: dict, brand: dict, logo_info: dict, args=None) -> str:
    """Swap the header logo block for the right variant.

    - dark variant present  -> two <img>s, one per theme (no colour filter)
    - single logo           -> the built-in filtered <img> (white silhouette in dark mode)
    - no logo at all        -> a monogram badge, so the header never shows a broken image
    """
    start = template.find(LOGO_START)
    end = template.find(LOGO_END)
    if start == -1 or end == -1 or end < start:
        return template

    alt = str(content.get("course", {}).get("logoAlt") or brand.get("orgName") or "").replace('"', "&quot;")
    logo = logo_info.get("logo") or ""
    dark = logo_info.get("dark") or ""
    indent = "      "

    if logo and dark:
        body = (
            f'<img src="{logo}" alt="{alt}" class="h-8 w-auto object-contain shrink-0 transition-all dark:hidden" />\n'
            f'{indent}<img src="{dark}" alt="{alt}" class="hidden h-8 w-auto object-contain shrink-0 transition-all dark:block" />'
        )
        mode = "logo + varian dark"
    elif logo:
        body = (
            f'<img src="{logo}" alt="{alt}" '
            'class="h-8 w-auto object-contain shrink-0 dark:brightness-0 dark:invert transition-all" />'
        )
        mode = "logo tunggal (silhouette di dark mode)"
    else:
        initials = monogram_for(brand)
        body = (
            f'<div class="h-8 w-8 shrink-0 rounded-lg bg-brand-primary/15 border border-brand-primary/30 '
            f'flex items-center justify-center text-[11px] font-black font-mono text-brand-primary '
            f'dark:text-brand-lightBlue" aria-label="{alt or "Logo"}" title="{alt or "Logo"}">{initials}</div>'
        )
        mode = f"monogram '{initials}' (tidak ada file logo)"

    # Markers are build-time only: ship the chosen block without them.
    template = (template[:start] + indent + body + "\n" + indent
                + template[end + len(LOGO_END):])
    log(args, f"  Logo: {mode} — {logo_info.get('source', 'n/a')}"
              + (f" · dark: {logo_info.get('dark_source')}" if logo_info.get("dark_source") else ""))
    return template


def certificate_config(content: dict, args=None) -> dict:
    """Resolve course.certificate (defaults + user overrides)."""
    course = content.get("course") or {}
    cert = dict(course.get("certificate") or {})

    page_key = str(cert.get("pageSize") or "A4 landscape").strip().lower()
    if page_key not in PAGE_SIZES:
        fail(
            f"course.certificate.pageSize '{cert.get('pageSize')}' is not supported. "
            f"Use one of: {', '.join(sorted(PAGE_SIZES))}, or set pageWidthMm/pageHeightMm."
        )
    default_w, default_h = PAGE_SIZES[page_key]

    labels = dict(DEFAULT_CERT_LABELS)
    labels.update({k: v for k, v in (cert.get("labels") or {}).items() if v is not None})

    template_override = getattr(args, "certificate_template", None) if args else None

    return {
        "pageSize": cert.get("pageSize") or "A4 landscape",
        "pageWidthMm": float(cert.get("pageWidthMm") or default_w),
        "pageHeightMm": float(cert.get("pageHeightMm") or default_h),
        "printPadding": str(cert.get("printPadding") or "15mm"),
        "dateLocale": str(cert.get("dateLocale") or "id-ID"),
        "regNumberFormat": str(cert.get("regNumberFormat") or "{prefix}/{year}/{seq}"),
        "template": template_override or cert.get("template"),
        "labels": labels,
    }


def build_cert_tokens(content: dict, brand: dict, cert: dict) -> dict:
    """Values for {{token}} substitution inside a custom certificate template."""
    course = content.get("course") or {}
    labels = cert["labels"]
    passing = course.get("passingScore", 80)
    return {
        "judul_kursus": course.get("title", ""),
        "kode_kursus": course.get("code", ""),
        "organisasi": brand.get("orgName", ""),
        "divisi": brand.get("orgDivision", ""),
        "penandatangan": brand.get("signatory", ""),
        "judul_sertifikat": brand.get("certTitle", ""),
        "prefix_reg": brand.get("certRegPrefix", "REG"),
        "tanggal_cetak": "",  # intentionally empty at build time; filled at runtime
        "passing_score": str(passing),
        "label_kicker": labels["kicker"],
        "label_presented_to": labels["presentedTo"],
        "label_pass_note": labels["passNote"],
        "label_score": labels["scoreLabel"],
        "label_pass_threshold": str(labels["passThresholdNote"]).replace("{passingScore}", str(passing)),
        "label_date": labels["dateLabel"],
        "label_footer": labels["footerNote"],
        "warna_primary": "#" + str(brand.get("primary", "2B73BD")).lstrip("#"),
        "warna_secondary": "#" + str(brand.get("secondary", "5A89B8")).lstrip("#"),
        "warna_accent": "#" + str(brand.get("accent", "38BDF8")).lstrip("#"),
    }


def build_placeholder_map(content: dict, brand: dict, cert: dict) -> dict:
    """Every __PLACEHOLDER__ the shell template may contain → its value.

    Exposed as a function so scripts/self_check.py can assert that the shell
    never references a placeholder the builder does not know about.
    """
    course = content.get("course") or {}
    labels = cert["labels"]
    passing = course.get("passingScore", 80)

    return {
        "__BUILD_VERSION__":         BUILD_VERSION,
        "__COURSE_TITLE__":          course.get("title", "Untitled Module"),
        "__COURSE_CODE__":           course.get("code", ""),
        "__COURSE_EFFECTIVE_DATE__": course.get("effectiveDate", ""),
        "__COURSE_LOGO__":           course.get("logo", ""),
        "__COURSE_LOGO_ALT__":       course.get("logoAlt", course.get("title", "")),
        "__COURSE_TITLE_TEXT__":     course.get("title", ""),
        "__COURSE_CODE2__":          course.get("code", ""),
        "__COURSE_RESOURCES_DESC__": course.get("resourcesDesc", ""),
        "__GLOSSARY_SEARCH_PLACEHOLDER__": course.get("glossarySearchPlaceholder", "Cari istilah..."),

        # Business data the engine reads at runtime.
        "__COURSE_PASSING_SCORE__":  str(passing),
        "__CERT_DATE_LOCALE__":      cert["dateLocale"],
        "__CERT_REG_FORMAT__":       cert["regNumberFormat"],

        # Certificate identity (build-time).
        "__CERT_BRAND_NAME__":       brand.get("orgName", ""),
        "__CERT_DIVISION__":         brand.get("orgDivision", ""),
        "__CERT_SIGNATORY__":        brand.get("signatory", ""),
        "__CERT_TITLE__":            brand.get("certTitle", "Standard Operating Procedure"),
        "__CERT_REG_PREFIX__":       brand.get("certRegPrefix", "REG"),

        # Certificate labels + page geometry (build-time).
        "__CERT_KICKER__":           labels["kicker"],
        "__CERT_PRESENTED_TO__":     labels["presentedTo"],
        "__CERT_PASS_NOTE__":        labels["passNote"],
        "__CERT_SCORE_LABEL__":      labels["scoreLabel"],
        "__CERT_PASS_THRESHOLD_NOTE__": str(labels["passThresholdNote"]).replace("{passingScore}", str(passing)),
        "__CERT_DATE_LABEL__":       labels["dateLabel"],
        "__CERT_FOOTER_NOTE__":      labels["footerNote"],
        "__CERT_PAGE_SIZE__":        cert["pageSize"],
        "__CERT_PAGE_WIDTH_MM__":    f"{cert['pageWidthMm']:g}mm",
        "__CERT_PAGE_HEIGHT_MM__":   f"{cert['pageHeightMm']:g}mm",
        "__CERT_PRINT_PADDING__":    cert["printPadding"],
    }


def apply_placeholders(template: str, content: dict, brand: dict, cert: dict) -> str:
    """Replace every __PLACEHOLDER__ in the template with a concrete value."""
    for key, value in build_placeholder_map(content, brand, cert).items():
        template = template.replace(key, str(value))
    return template


def render_certificate_template(template: str, content: dict, brand: dict, cert: dict,
                                content_dir: Path, args) -> str:
    """Swap the built-in certificate markup for a user-supplied HTML template.

    The custom file replaces the *inner* HTML of #certificatePrintArea.
    """
    rel = cert.get("template")
    if not rel:
        return template

    path = Path(rel)
    if not path.is_absolute():
        path = (content_dir / path).resolve()
    if not path.exists():
        fail(f"course.certificate.template not found: {path}")

    try:
        custom = path.read_text(encoding="utf-8")
    except OSError as e:
        fail(f"Cannot read certificate template {path}: {e}")

    # Authoring comments never ship and never count as tokens: a template's own
    # documentation may legitimately contain literal {{token}} examples.
    custom = re.sub(r"<!--.*?-->", "", custom, flags=re.S)

    tokens = build_cert_tokens(content, brand, cert)
    unknown = sorted({t for t in CERT_TOKEN_RE.findall(custom) if t not in tokens})
    if unknown:
        fail(
            f"Unknown {{{{token}}}} in certificate template {path.name}: {', '.join(unknown)}. "
            f"Available tokens: {', '.join(CERT_TOKEN_KEYS)}"
        )
    custom = CERT_TOKEN_RE.sub(lambda m: str(tokens[m.group(1)]), custom)

    start = template.find(CERT_START)
    end = template.find(CERT_END)
    if start == -1 or end == -1 or end < start:
        fail(
            f"Certificate markers {CERT_START} / {CERT_END} are missing from "
            "assets/shell.template.html — cannot apply a custom certificate template."
        )
    template = template[:start + len(CERT_START)] + "\n" + custom.strip() + "\n      " + template[end:]
    log(args, f"  ✓ Applied custom certificate template: {path.name}")
    return template


def check_contrast(brand: dict, args):
    """Advisory WCAG check: flag palette tokens that cannot carry white body text."""
    def lum(hex6):
        hex6 = hex6.lstrip("#")
        ch = [int(hex6[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        ch = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in ch]
        return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]

    def ratio(a, b):
        la, lb = lum(a), lum(b)
        hi, lo = max(la, lb), min(la, lb)
        return (hi + 0.05) / (lo + 0.05)

    if getattr(args, "no_contrast_check", False):
        return

    warnings = []
    for field in ("primary", "primaryHover", "secondary", "secondaryLight", "accent"):
        raw = str(brand.get(field) or "").strip().lstrip("#")
        if not re.fullmatch(r"[0-9A-Fa-f]{6}", raw):
            continue
        r = ratio(raw, "FFFFFF")
        if r < 4.5:
            warnings.append(f"{field} #{raw.upper()} → white text contrast {r:.2f}:1 (< 4.5 AA)")
    if warnings:
        print("WARN: brand contrast advisory (only matters where the token carries white body text):", file=sys.stderr)
        for w in warnings:
            print(f"      - {w}", file=sys.stderr)


def inject_course_data(template: str, course_obj: dict) -> str:
    """Replace `let COURSE = null; // __COURSE_DATA_INJECTION_POINT__` with the
    content.json literal. Runs LAST so no later pass can mutate author copy."""
    marker = "let COURSE = null; // __COURSE_DATA_INJECTION_POINT__"
    injection = "let COURSE = " + json.dumps(course_obj, ensure_ascii=False, indent=2) + ";"
    if marker in template:
        template = template.replace(marker, injection)
    else:
        m = re.search(r"let\s+COURSE\s*=\s*null;.*__COURSE_DATA_INJECTION_POINT__", template)
        if not m:
            fail("Could not find COURSE_DATA injection point in template.")
        template = template[:m.start()] + injection + template[m.end():]
    # Belt and braces: the marker must not survive in comment text either.
    template = template.replace("__COURSE_DATA_INJECTION_POINT__", "COURSE data")
    return template


def main():
    ap = argparse.ArgumentParser(description="E-Learning Module Builder")
    ap.add_argument("--content", required=True, help="Path to content.json")
    ap.add_argument("--output", required=True, help="Path to write final HTML")
    ap.add_argument("--brand-preset", default=None, help="Override brand.preset (ptpp|corporate|education|tech-startup|custom)")
    ap.add_argument("--certificate-template", default=None, help="Override course.certificate.template (HTML file)")
    ap.add_argument("--skill-root", default=None, help="Path to skill root (default: this script's parent)")
    ap.add_argument("--validate", action="store_true", default=False, help="Run validate_content.py before building")
    ap.add_argument("--no-validate", dest="validate", action="store_false")
    ap.add_argument("--allow-placeholders", action="store_true", default=False,
                    help="Do not fail when build placeholders remain unfilled")
    ap.add_argument("--no-contrast-check", action="store_true", default=False,
                    help="Skip the WCAG contrast advisory")
    ap.add_argument("--quiet", action="store_true", default=False, help="Only print errors and the output path")
    ap.add_argument("--logo", default=None, help="Override the logo image path (png/jpg/svg/webp)")
    ap.add_argument("--logo-dark", default=None, help="Override the dark-mode logo image path")
    args = ap.parse_args()

    # Resolve skill root
    script_dir = Path(__file__).parent.resolve()
    skill_root = Path(args.skill_root).resolve() if args.skill_root else script_dir.parent
    template_path = skill_root / "assets" / "shell.template.html"
    profiles_path = skill_root / "assets" / "brand.profiles.json"
    validator_path = skill_root / "scripts" / "validate_content.py"

    content_path = Path(args.content).resolve()
    if not content_path.exists():
        fail(f"content.json not found at {content_path}")
    content = load_json(content_path)

    # Optional validation
    if args.validate and validator_path.exists():
        import subprocess
        log(args, f"Validating {content_path} against schema...")
        result = subprocess.run(
            [sys.executable, str(validator_path), str(content_path)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        print(result.stdout, end="")
        if result.returncode != 0:
            print(result.stderr, file=sys.stderr, end="")
            fail("Validation failed. Aborting.")

    # Ensure brand block exists
    if "brand" not in content:
        content["brand"] = {"preset": "ptpp"}

    # Make the logo self-contained before anything reads course.logo.
    logo_info = resolve_logo(content, content_path.parent, args)

    profiles = {k: v for k, v in load_json(profiles_path).items() if not k.startswith("_")}
    brand = resolve_brand(content, profiles, args.brand_preset)
    cert = certificate_config(content, args)

    if not template_path.exists():
        fail(f"shell.template.html not found at {template_path}")
    template = template_path.read_text(encoding="utf-8")

    # ── Step 1: brand palette (template only — content is not injected yet) ──
    log(args, f"Step 1: Applying brand palette (preset: {brand.get('preset', 'custom')})...")
    template = apply_color_tokens(template, brand)

    # ── Step 2: build-time placeholders ─────────────────────────────────────
    log(args, "Step 2: Replacing build-time placeholders...")
    template = apply_placeholders(template, content, brand, cert)

    # ── Step 3: custom certificate template ─────────────────────────────────
    log(args, "Step 3: Resolving certificate template...")
    template = render_certificate_template(template, content, brand, cert, content_path.parent, args)

    # ── Step 3b: header logo (dark variant / monogram fallback) ─────────────
    template = apply_logo_block(template, content, brand, logo_info, args)

    # ── Step 3c: default theme mode (light/dark) ───────────────────────────
    course_cfg = content.get("course") or {}
    if course_cfg.get("defaultDark") is False:
        template = template.replace(
            '<body id="playerRoot" class="h-full w-full overflow-hidden flex flex-col font-sans bg-brand-darkBg text-slate-100 dark">',
            '<body id="playerRoot" class="h-full w-full overflow-hidden flex flex-col font-sans bg-brand-darkBg text-slate-100">'
        )
        template = template.replace(
            '<span class="material-symbols-outlined text-sm text-brand-primary dark:text-brand-lightBlue shrink-0" id="themeIcon">light_mode</span>',
            '<span class="material-symbols-outlined text-sm text-brand-primary dark:text-brand-lightBlue shrink-0" id="themeIcon">dark_mode</span>'
        )
        template = template.replace(
            '<span class="hidden xl:inline" id="themeLabel">Light</span>',
            '<span class="hidden xl:inline" id="themeLabel">Dark</span>'
        )

    # ── Step 4: inject COURSE (must be last) ────────────────────────────────
    log(args, "Step 4: Injecting COURSE data...")
    template = inject_course_data(template, content)

    # ── Post-checks ─────────────────────────────────────────────────────────
    leftover = sorted(set(PLACEHOLDER_RE.findall(template)))
    if leftover:
        message = f"Unfilled build placeholders remain: {', '.join(leftover)}"
        if args.allow_placeholders:
            print(f"WARN: {message}", file=sys.stderr)
        else:
            fail(message + " (pass --allow-placeholders to downgrade this to a warning)")

    stray = sorted(set(CERT_TOKEN_RE.findall(template)))
    if stray:
        print(f"WARN: literal {{{{token}}}} text remains in the output: {', '.join(stray)}", file=sys.stderr)

    check_contrast(brand, args)

    # ── Write output ────────────────────────────────────────────────────────
    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(template, encoding="utf-8")

    slides = content.get("slides", [])
    type_counts = {}
    for s in slides:
        t = s.get("type", "?")
        type_counts[t] = type_counts.get(t, 0) + 1

    log(args, f"\n✓ Built module: {out_path}")
    log(args, f"  Size: {len(template):,} chars, {template.count(chr(10)) + 1:,} lines")
    log(args, f"  Brand: {brand.get('preset', 'custom')} ({brand.get('orgName', '—')})")
    log(args, f"  Certificate: {cert['pageSize']} @ {cert['printPadding']} pad, "
              f"template={'custom:' + Path(cert['template']).name if cert['template'] else 'built-in'}")
    log(args, f"  Slides: {len(slides)} | Units: {len(content.get('units', []))}")
    log(args, "  Types: " + ", ".join(f"{k}×{v}" for k, v in sorted(type_counts.items())))


if __name__ == "__main__":
    main()
