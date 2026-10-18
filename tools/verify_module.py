#!/usr/bin/env python3
"""
verify_module.py — offline quality gate for built e-learning modules.

Checks (no browser required):
  1. Static DOM tag balance (script blocks stripped first, since renderer markup
     lives inside JS template literals and would confuse a plain HTML parser).
  2. Every <script> block parses as valid JavaScript (via `node --check`).
  3. A required set of DOM ids exists in the static chrome, matched with an
     attribute-tolerant regex (`id="x"`, `id='x'`, attributes in any order).
  4. No stray literal ">" text nodes leak into the static DOM.
  5. Renderer functions referenced by SLIDE_RENDERERS all exist, and the registry
     covers every slide type declared in assets/content.schema.json.
  6. The COURSE literal was actually injected (not left as `null`).
  7. No unfilled `__BUILD_PLACEHOLDER__` survives into the shipped HTML.
  8. The certificate contract ids exist, so a custom
     course.certificate.template cannot silently break printing.
  9. With --content: the injected COURSE literal matches content.json byte for
     byte, i.e. the HTML really is the build of the content you think it is.

Advisories (never fail the gate):
  - native alert()/confirm() usage outside comments (banned by the design system)

USAGE
  python3 verify_module.py <built-module.html> [<built-module.html> ...]
                           [--content <content.json>] [--schema <schema.json>]

Exit codes: 0 = clean, 1 = at least one problem.
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKILL_ROOT = Path(__file__).resolve().parent.parent

VOID = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}

# Player chrome: must exist in the STATIC DOM (outside <script>).
REQUIRED_STATIC_IDS = [
    "topHeader", "courseSidebar", "slideBody", "bottomPlaybar", "seekBar",
    "slideViewport", "captionDock", "captionText", "btnPlayPause", "btnPrevSlide",
    "btnNextSlide", "slideCounterText", "modalTenggat", "modalTerminologi",
    "modalHint", "modalHotspot", "certificatePrintArea", "tenggatGrid", "hintGrid",
    "tabNavOutline", "tabNavNotes", "tabNavResources", "overallPercentage",
    "toastHost",
]

# Certificate contract: filled by printCertificate() at runtime. A custom
# certificate template must keep all five or printing silently degrades.
REQUIRED_CERT_IDS = [
    "certRecipientName", "certRecipientNIP", "certScoreVal", "certDateVal",
    "certNumberLabel",
]

# Renderer-owned ids: they live inside renderer template literals, so they are
# checked against the whole file rather than the static DOM.
RENDERER_IDS = ["lblCanvasZoom", "treeCanvasViewport", "treeScrollTrack", "treeScrollThumb"]

PLACEHOLDER_RE = re.compile(r"__[A-Z][A-Z0-9_]*__")

_KNOWN_PLACEHOLDERS = None


def known_placeholders():
    """Placeholder names the builder knows about (asked of build_module.py).

    Used to separate a genuine unfilled build placeholder (hard error) from a
    `__SOMETHING__` an author legitimately wrote inside slide copy (advisory).
    """
    global _KNOWN_PLACEHOLDERS
    if _KNOWN_PLACEHOLDERS is None:
        try:
            sys.path.insert(0, str(SKILL_ROOT / "scripts"))
            import build_module as bm
            stub = {"course": {}}
            cert = bm.certificate_config(stub, None)
            _KNOWN_PLACEHOLDERS = set(bm.build_placeholder_map(stub, {"preset": "custom"}, cert))
        except Exception:
            _KNOWN_PLACEHOLDERS = set()
    return _KNOWN_PLACEHOLDERS


class TagChecker(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.problems = []
        self.stray_gt = 0

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()))

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.problems.append(f"stray </{tag}> at line {self.getpos()[0]}")
            return
        if self.stack[-1][0] == tag:
            self.stack.pop()
            return
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                unclosed = [t for t, _ in self.stack[i + 1:]]
                self.problems.append(
                    f"</{tag}> at line {self.getpos()[0]} closes across unclosed {unclosed}"
                )
                del self.stack[i:]
                return
        self.problems.append(f"unmatched </{tag}> at line {self.getpos()[0]}")

    def handle_data(self, data):
        if data.strip() == ">":
            self.stray_gt += 1


def strip_scripts(html):
    return re.sub(r"<script\b.*?</script>", "", html, flags=re.S | re.I)


def extract_scripts(html):
    return re.findall(r"<script\b[^>]*>(.*?)</script>", html, flags=re.S | re.I)


def has_id(html, element_id):
    """Attribute-order/quote tolerant id lookup."""
    return re.search(rf"""id\s*=\s*["']{re.escape(element_id)}["']""", html) is not None


def check_js(scripts, node):
    """Return list of problem strings."""
    problems = []
    bodies = [(i, s) for i, s in enumerate(scripts) if s.strip()]
    if not bodies:
        return ["no non-empty <script> blocks found"]
    for idx, body in bodies:
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
            fh.write(body)
            tmp = Path(fh.name)
        try:
            res = subprocess.run([node, "--check", str(tmp)], capture_output=True, text=True)
            if res.returncode != 0:
                first = (res.stderr or "").strip().splitlines()[:4]
                problems.append(f"script #{idx} JS syntax error: {' | '.join(first)}")
        finally:
            tmp.unlink(missing_ok=True)
    return problems


def _resolve_ref(schema, node):
    """Follow local $ref chains (#/definitions/...) until a concrete node."""
    seen = set()
    while isinstance(node, dict) and "$ref" in node:
        ref = node["$ref"]
        if ref in seen or not ref.startswith("#/"):
            return None
        seen.add(ref)
        cur = schema
        for token in ref[2:].split("/"):
            token = token.replace("~1", "/").replace("~0", "~")
            cur = cur.get(token) if isinstance(cur, dict) else None
            if cur is None:
                return None
        node = cur
    return node


def schema_slide_types(schema_path: Path):
    """Slide type consts declared in the schema's slides.items.oneOf."""
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    node = schema
    for key in ("properties", "slides", "items", "oneOf"):
        node = _resolve_ref(schema, node)
        node = node.get(key) if isinstance(node, dict) else None
        if node is None:
            return None
    types = set()
    for branch in node:
        branch = _resolve_ref(schema, branch) or {}
        const = (branch.get("properties", {}).get("type", {}) or {}).get("const")
        if const:
            types.add(const)
    return types or None


def native_dialog_advisory(html):
    body = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    body = re.sub(r"^[ \t]*//.*$", "", body, flags=re.M)
    hits = re.findall(r"(?<![A-Za-z_.$])(alert|confirm)\s*\(", body)
    return sorted(set(hits))


def check_content_parity(expected: dict, injected: dict) -> list:
    """Compare content.json against the injected COURSE object.

    Normalizes known build-time transforms (e.g. logo inlining to data: URI,
    brand defaults) so genuine content changes are caught without false positives.
    """
    diffs = []
    for k in ("slides", "quiz", "units", "glossary", "tenggatCheatSheet", "hintTips", "resources"):
        if k in expected and expected[k] != injected.get(k):
            if k == "slides":
                exp_len = len(expected[k])
                inj_len = len(injected.get(k, []))
                if exp_len != inj_len:
                    diffs.append(f"slides count mismatch: content.json has {exp_len}, HTML has {inj_len}")
                else:
                    for idx, (es, is_) in enumerate(zip(expected[k], injected[k])):
                        if es != is_:
                            diffs.append(f"slide {idx} ({es.get('type')}) differs")
                            break
            elif k == "quiz":
                diffs.append("quiz questions or config differ")
            else:
                diffs.append(f"'{k}' section differs")

    exp_course = dict(expected.get("course") or {})
    inj_course = dict(injected.get("course") or {})
    if str(inj_course.get("logo", "")).startswith("data:"):
        inj_course.pop("logo", None)
        exp_course.pop("logo", None)
    if str(inj_course.get("logoDark", "")).startswith("data:"):
        inj_course.pop("logoDark", None)
        exp_course.pop("logoDark", None)
    if "logoAlt" in inj_course and "logoAlt" not in exp_course:
        inj_course.pop("logoAlt", None)

    for k in set(exp_course) | set(inj_course):
        if exp_course.get(k) != inj_course.get(k):
            diffs.append(f"course.{k} differs: content.json={exp_course.get(k)!r} vs HTML={inj_course.get(k)!r}")

    return diffs


def verify_file(path: Path, args, node, expected_content, slide_types):
    html = path.read_text(encoding="utf-8", errors="replace")
    problems = []
    checks = 0

    # 1 + 4 — static DOM structure
    static = strip_scripts(html)
    checker = TagChecker()
    checker.feed(static)
    problems.extend(checker.problems)
    if checker.stack:
        problems.append("unclosed at EOF: " + ", ".join(f"{t}@L{p[0]}" for t, p in checker.stack))
    if checker.stray_gt:
        problems.append(f"{checker.stray_gt} stray '>' text node(s) in static DOM")
    checks += 1

    # 2 — JS syntax
    problems.extend(check_js(extract_scripts(html), node))
    checks += 1

    # 3 — required ids (static chrome + certificate contract + renderer-owned)
    missing = [i for i in REQUIRED_STATIC_IDS if not has_id(static, i)]
    if missing:
        problems.append("missing required ids in static chrome: " + ", ".join(missing))
    missing_cert = [i for i in REQUIRED_CERT_IDS if not has_id(html, i)]
    if missing_cert:
        problems.append(
            "missing certificate contract ids (printCertificate() cannot fill these): "
            + ", ".join(missing_cert)
        )
    missing_r = [i for i in RENDERER_IDS if not has_id(html, i)]
    if missing_r:
        problems.append("missing renderer ids: " + ", ".join(missing_r))
    checks += 1

    # 5 — renderer registry vs definitions vs schema
    reg = re.search(r"const SLIDE_RENDERERS\s*=\s*\{(.*?)\n\s*\};", html, re.S)
    if not reg:
        problems.append("SLIDE_RENDERERS registry not found")
    else:
        names = re.findall(r":\s*(render[A-Za-z0-9_]+)", reg.group(1))
        undef = [n for n in names if not re.search(rf"function\s+{n}\s*\(", html)]
        if undef:
            problems.append("SLIDE_RENDERERS references undefined: " + ", ".join(sorted(set(undef))))
        registered = set(re.findall(r"['\"]([A-Za-z0-9_]+)['\"]\s*:", reg.group(1)))
        if slide_types:
            absent = sorted(slide_types - registered)
            extra = sorted(registered - slide_types)
            if absent:
                problems.append("schema slide types with no renderer registered: " + ", ".join(absent))
            if extra:
                problems.append("registered renderers absent from the schema: " + ", ".join(extra))
    checks += 1

    # 6 — COURSE injected
    if re.search(r"let\s+COURSE\s*=\s*null\s*;", html):
        problems.append("COURSE was not injected (still `let COURSE = null;`)")
    elif not re.search(r"let\s+COURSE\s*=\s*\{", html):
        problems.append("COURSE literal not found in the built HTML")
    checks += 1

    # 7 — build placeholders
    found_tokens = set(PLACEHOLDER_RE.findall(html))
    unfilled = sorted(found_tokens & known_placeholders())
    if unfilled:
        problems.append(
            "unfilled build placeholders: " + ", ".join(unfilled)
            + " (rebuild with scripts/build_module.py)"
        )
    checks += 1

    # 9 — content parity
    if expected_content is not None:
        checks += 1
        matched = False
        if isinstance(expected_content, str):
            matched = (expected_content in html)
        elif isinstance(expected_content, dict):
            expected_literal = "let COURSE = " + json.dumps(expected_content, ensure_ascii=False, indent=2) + ";"
            if expected_literal in html:
                matched = True
            else:
                m = re.search(r"^\s*let\s+COURSE\s*=\s*(\{.*?\n\s*\});\s*$", html, re.MULTILINE | re.DOTALL)
                if m:
                    try:
                        injected = json.loads(m.group(1))
                        diffs = check_content_parity(expected_content, injected)
                        if not diffs:
                            matched = True
                        else:
                            problems.append(
                                "COURSE literal does not match the supplied --content file "
                                f"(the HTML is stale — rerun build_module.py): {'; '.join(diffs[:2])}"
                            )
                    except Exception as err:
                        problems.append(f"Failed to parse injected COURSE JSON: {err}")
                else:
                    problems.append("Injected COURSE object not found in HTML")
        if not matched and not problems:
            problems.append(
                "COURSE literal does not match the supplied --content file "
                "(the HTML is stale — rerun build_module.py)"
            )

    advisories = []
    dialogs = native_dialog_advisory(html)
    if dialogs:
        advisories.append(
            "native dialog call(s) present: " + ", ".join(f"{d}()" for d in dialogs)
            + " — the design system requires in-app notices"
        )
    stray_placeholders = sorted(found_tokens - known_placeholders())
    if stray_placeholders:
        advisories.append(
            "__NAME__ style text found (not a build placeholder — check whether it is "
            "intended content): " + ", ".join(stray_placeholders)
        )

    return problems, advisories, checks


def main():
    ap = argparse.ArgumentParser(description="Offline quality gate for built e-learning modules")
    ap.add_argument("html", nargs="+", help="Built module HTML file(s)")
    ap.add_argument("--content", default=None,
                    help="content.json used to build — enables COURSE literal parity checking")
    ap.add_argument("--schema", default=None, help="content.schema.json (default: skill assets/)")
    ap.add_argument("--node", default="node", help="Node.js executable (default: node)")
    args = ap.parse_args()

    node = args.node
    try:
        subprocess.run([node, "--version"], capture_output=True, text=True, check=False)
    except FileNotFoundError:
        print(f"ERROR: Node.js executable not found: {node}", file=sys.stderr)
        sys.exit(1)

    schema_path = Path(args.schema) if args.schema else SKILL_ROOT / "assets" / "content.schema.json"
    slide_types = schema_slide_types(schema_path) if schema_path.exists() else None
    if slide_types is None:
        print(f"WARN: slide-type parity skipped (schema not readable: {schema_path})", file=sys.stderr)

    expected_content = None
    if args.content:
        content_path = Path(args.content)
        if not content_path.exists():
            print(f"ERROR: --content not found: {content_path}", file=sys.stderr)
            sys.exit(1)
        try:
            expected_content = json.loads(content_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"ERROR: invalid JSON in {content_path}: {e}", file=sys.stderr)
            sys.exit(1)

    failed = False
    for arg in args.html:
        path = Path(arg)
        if not path.exists():
            print(f"✗ {arg}: not found")
            failed = True
            continue

        problems, advisories, checks = verify_file(path, args, node, expected_content, slide_types)
        if problems:
            failed = True
            print(f"✗ {path.name} — {len(problems)} problem(s) across {checks} checks")
            for p in problems:
                print(f"    - {p}")
        else:
            size_kb = len(path.read_bytes()) / 1024
            print(f"✓ {path.name} — clean ({size_kb:.0f} KB, {checks} checks)")
        for a in advisories:
            print(f"    ! advisory: {a}")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
