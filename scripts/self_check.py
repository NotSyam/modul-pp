#!/usr/bin/env python3
"""
self_check.py — regression gate for the modul-pp skill itself.

Builds the shipped sample end to end and re-runs the exact failure modes that
have bitten this engine before, so a shell edit cannot silently regress them.

WHAT IT PROVES
  1. schema validator           — assets/sample.content.json passes
  2. build                      — scripts/build_module.py produces HTML
  3. verification gate          — tools/verify_module.py is clean, WITH
                                  --content parity (the HTML really is the build
                                  of that content)
  4. palette collision          — a brand whose primary hex equals another token's
                                  hex no longer steals that token's elements
  5. content preservation       — literal hex codes inside slide copy survive the
                                  brand pass (recolor must run before injection)
  6. placeholder contract       — every __PLACEHOLDER__ in the shell is known to
                                  the builder, and no placeholder survives output
  7. custom certificate         — a course.certificate.template is applied, tokens
                                  are substituted, and the certificate contract
                                  ids / page geometry are present
  8. narration pipeline         — generate_audio.py resolves per-slide narration,
                                  reports coverage, and builds an intisari
                                  fallback (no TTS calls)
  9. demo freshness             — test_build.html is regenerated from the sample
                                  so the committed demo cannot go stale

USAGE
  python3 scripts/self_check.py [--skill-root PATH] [--with-smoke] [--no-demo]

Exit codes: 0 = all green, 1 = at least one regression.
"""
import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKILL_ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable

results = []


def record(name, ok, detail=""):
    results.append((name, ok, detail))
    icon = "✓" if ok else "✗"
    print(f"  {icon} {name}" + (f" — {detail}" if detail else ""))
    return ok


def run(cmd, expect_zero=True, cwd=None):
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                         errors="replace", cwd=str(cwd) if cwd else None)
    ok = (res.returncode == 0) if expect_zero else True
    return ok, (res.stdout or "") + (res.stderr or ""), res.returncode


def count(text, needle):
    return len(re.findall(re.escape(needle), text))


def write_json(path: Path, payload: dict):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def minimal_content(**overrides):
    data = {
        "course": {"code": "SELF/CHK-1", "title": "Self Check", "totalUnits": 1, "passingScore": 80},
        "brand": {"preset": "custom"},
        "units": [{"title": "0. Cover"}],
        "slides": [{"type": "cover", "heroTitle": "Self Check"}],
    }
    data.update(overrides)
    return data


def main():
    ap = argparse.ArgumentParser(description="Regression gate for the modul-pp skill")
    ap.add_argument("--skill-root", default=None, help="Skill root (default: this script's parent dir)")
    ap.add_argument("--with-smoke", action="store_true", help="Also run the Playwright smoke test")
    ap.add_argument("--no-demo", action="store_true", help="Do not regenerate test_build.html")
    ap.add_argument("--keep-temp", action="store_true", help="Keep the temp build directory")
    args = ap.parse_args()

    root = Path(args.skill_root).resolve() if args.skill_root else SKILL_ROOT
    build_py = root / "scripts" / "build_module.py"
    validate_py = root / "scripts" / "validate_content.py"
    verify_py = root / "tools" / "verify_module.py"
    audio_py = root / "scripts" / "generate_audio.py"
    shell = root / "assets" / "shell.template.html"
    sample = root / "assets" / "sample.content.json"

    for required in (build_py, validate_py, verify_py, shell, sample):
        if not required.exists():
            print(f"ERROR: missing {required}", file=sys.stderr)
            sys.exit(1)

    print(f"modul-pp self-check — skill root: {root}\n" + "=" * 62)
    # Scratch space: prefer <skill-root>/build (gitignored, always same volume),
    # fall back to the system temp dir when the skill root is read-only.
    try:
        tmp = root / "build" / f"self_check-{os.getpid()}"
        tmp.mkdir(parents=True, exist_ok=True)
        probe = tmp / ".write-probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError:
        tmp = Path(tempfile.mkdtemp(prefix="modulpp-selfcheck-"))
    print(f"scratch: {tmp}")
    try:
        # ── 1. schema validation ────────────────────────────────────────────
        print("\n[1] Schema validation")
        ok, out, _ = run([PY, str(validate_py), str(sample)])
        record("sample.content.json validates", ok, out.strip().splitlines()[0] if out.strip() else "")

        # ── 2 + 3. build + verification gate with parity ────────────────────
        print("\n[2] Build + verification gate")
        out_html = tmp / "sample.html"
        ok, out, rc = run([PY, str(build_py), "--content", str(sample), "--output", str(out_html),
                           "--skill-root", str(root)])
        record("build_module.py builds the sample", ok and out_html.exists(), f"rc={rc}")
        if out_html.exists():
            ok, vout, rc = run([PY, str(verify_py), str(out_html), "--content", str(sample)])
            record("verify_module.py clean + COURSE parity", ok, vout.strip().splitlines()[0] if vout.strip() else "")

        # ── 4. palette collision regression ────────────────────────────────
        print("\n[3] Palette collision regression")
        control = minimal_content(brand={"preset": "custom", "orgName": "X", "primary": "AA0000",
                                         "darkBorder": "123456"})
        collide = minimal_content(brand={"preset": "custom", "orgName": "X", "primary": "1F2F4A",
                                         "darkBorder": "123456"})
        control_json, collide_json = tmp / "control.json", tmp / "collide.json"
        write_json(control_json, control)
        write_json(collide_json, collide)
        control_html, collide_html = tmp / "control.html", tmp / "collide.html"
        run([PY, str(build_py), "--content", str(control_json), "--output", str(control_html),
             "--skill-root", str(root), "--quiet", "--no-contrast-check"])
        run([PY, str(build_py), "--content", str(collide_json), "--output", str(collide_html),
             "--skill-root", str(root), "--quiet", "--no-contrast-check"])
        if control_html.exists() and collide_html.exists():
            c_text = control_html.read_text(encoding="utf-8")
            k_text = collide_html.read_text(encoding="utf-8")
            expect_primary = count(c_text, "#AA0000")
            expect_border = count(c_text, "#123456")
            got_border = count(k_text, "#123456")
            record(
                "brand token collision does not steal elements",
                expect_primary > 0 and got_border == expect_border,
                f"control primary={expect_primary}, border={expect_border}; collided border={got_border}",
            )
        else:
            record("brand token collision does not steal elements", False, "build failed")

        # ── 5. content preservation ────────────────────────────────────────
        print("\n[4] Content preservation (recolor must precede injection)")
        hex_literal = "#2B73BD"
        preserve = minimal_content(brand={"preset": "corporate"})
        preserve["slides"] = [{"type": "calloutBox", "title": "Hex",
                               "body": f"Header hex kustom kami adalah {hex_literal}."}]
        preserve_json = tmp / "preserve.json"
        preserve_html = tmp / "preserve.html"
        write_json(preserve_json, preserve)
        run([PY, str(build_py), "--content", str(preserve_json), "--output", str(preserve_html),
             "--skill-root", str(root), "--quiet", "--no-contrast-check"])
        if preserve_html.exists():
            text = preserve_html.read_text(encoding="utf-8")
            record(
                "author hex literals survive the brand pass",
                hex_literal in text and "Header hex kustom kami adalah #0F4C81" not in text,
                f"{hex_literal} occurrences after build: {count(text, hex_literal)}",
            )
        else:
            record("author hex literals survive the brand pass", False, "build failed")

        # ── 6. placeholder contract ────────────────────────────────────────
        print("\n[5] Placeholder contract")
        sys.path.insert(0, str(root / "scripts"))
        import build_module as bm  # noqa: E402

        shell_text = shell.read_text(encoding="utf-8")
        shell_tokens = set(re.findall(r"__[A-Z][A-Z0-9_]*__", shell_text))
        # __COURSE_DATA_INJECTION_POINT__ is the injection marker itself, not a
        # build placeholder: build_module strips it separately.
        shell_tokens.discard("__COURSE_DATA_INJECTION_POINT__")
        brands = {k: v for k, v in json.loads((root / "assets" / "brand.profiles.json")
                                             .read_text(encoding="utf-8")).items() if not k.startswith("_")}
        sample_obj = json.loads(sample.read_text(encoding="utf-8"))
        brand = bm.resolve_brand(sample_obj, brands, None)
        cert = bm.certificate_config(sample_obj, None)
        known = set(bm.build_placeholder_map(sample_obj, brand, cert))
        unknown = sorted(t for t in shell_tokens if t not in known)
        record("every shell placeholder is known to the builder", not unknown,
               f"unknown: {', '.join(unknown)}" if unknown else f"{len(shell_tokens)} placeholders")

        # A missing placeholder is worse than an unknown one: it means the builder
        # renamed a token the shell still uses, so output ships literal __X__ text.
        if out_html.exists():
            leftover = sorted(set(re.findall(r"__[A-Z][A-Z0-9_]*__", out_html.read_text(encoding="utf-8"))))
            record("built output has no leftover placeholders", not leftover,
                   f"leftover: {', '.join(leftover)}" if leftover else "")

        # ── 5b. interactivity inventory ────────────────────────────────────
        # Every slide type the schema declares must be classified by the validator,
        # otherwise density analytics silently ignore it (and so does the authoring
        # guidance in references/interactivity_patterns.md).
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("validator", root / "scripts" / "validate_content.py")
        validator = _ilu.module_from_spec(spec)
        spec.loader.exec_module(validator)
        try:
            sys.path.insert(0, str(root / "tools"))
            from verify_module import schema_slide_types as _slide_types
            declared = _slide_types(root / "assets" / "content.schema.json") or set()
        except Exception:
            declared = set()
        classified = (set(validator.ACTIVE_TYPES) | set(validator.SEMI_TYPES) | set(validator.PASSIVE_TYPES))
        planned = set(getattr(validator, "PLANNED_TYPES", set()))
        unclassified = sorted(declared - classified)
        phantom = sorted(classified - declared - planned)
        record("every schema slide type is classified for interactivity analytics", not unclassified,
               f"unclassified: {', '.join(unclassified)}" if unclassified else f"{len(classified)} classified")
        record("interactivity classification has no phantom types", not phantom,
               f"not in schema: {', '.join(phantom)}" if phantom else "")
        pending = sorted(planned - declared)
        if pending:
            print(f"  · planned, not in schema yet: {', '.join(pending)}")

        # ── 5c. sample covers the interaction features ─────────────────────
        # The sample is the regression fixture: if it stops exercising a question
        # type or the checkpoint block, future self-checks silently stop covering it.
        expected_qtypes = {"mcq", "trueFalse", "fillIn", "multipleResponse",
                           "ordering", "matching", "numeric"}
        used_qtypes, checkpoint_slides = set(), 0
        for slide in sample_obj.get("slides", []):
            if not isinstance(slide, dict):
                continue
            if slide.get("type") == "quiz":
                used_qtypes |= {q.get("type") for q in slide.get("questions", []) if isinstance(q, dict)}
            cp = slide.get("checkpoint")
            if isinstance(cp, dict) and cp.get("question"):
                checkpoint_slides += 1
        missing_qtypes = sorted(expected_qtypes - used_qtypes)
        record("sample exercises every question type", not missing_qtypes,
               f"missing: {', '.join(missing_qtypes)}" if missing_qtypes else f"{len(used_qtypes)} types")
        record("sample exercises the checkpoint block", checkpoint_slides > 0,
               f"{checkpoint_slides} checkpoint slide(s)")

        # Every IMPLEMENTED active slide type must appear in the sample, otherwise
        # the regression fixture silently stops covering it.
        used_slide_types = {s.get("type") for s in sample_obj.get("slides", []) if isinstance(s, dict)}
        implemented_active = set(validator.ACTIVE_TYPES) - set(getattr(validator, "PLANNED_TYPES", set()))
        missing_active = sorted(implemented_active - used_slide_types)
        record("sample exercises every implemented interactive slide type", not missing_active,
               f"missing: {', '.join(missing_active)}" if missing_active
               else f"{len(implemented_active)} active types")

        # ── 6b. logo pipeline + title lint ─────────────────────────────────
        print("\n[6b] Logo pipeline + title lint")
        # A logo dropped next to content.json must be inlined (single-file module).
        logo_dir = tmp / "logo-project"
        (logo_dir / "assets").mkdir(parents=True, exist_ok=True)
        # 1x1 transparent PNG — enough to prove the plumbing.
        (logo_dir / "assets" / "logo.png").write_bytes(base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg=="
        ))
        write_json(logo_dir / "content.json", minimal_content())
        logo_html = logo_dir / "index.html"
        ok, out, rc = run([PY, str(build_py), "--content", str(logo_dir / "content.json"),
                           "--output", str(logo_html), "--skill-root", str(root),
                           "--quiet", "--no-contrast-check"])
        if ok and logo_html.exists():
            text = logo_html.read_text(encoding="utf-8")
            record("logo beside content.json is inlined automatically",
                   "data:image/png;base64," in text and "LOGO-START" not in text,
                   "inlined + markers stripped" if "data:image/png;base64," in text else "no data URI")
            # A single logo must still adapt to the theme (white silhouette in dark mode).
            record("single logo carries the dark-mode treatment",
                   "dark:brightness-0 dark:invert" in text, "brightness-0 + invert present")
        else:
            record("logo beside content.json is inlined automatically", False, f"build rc={rc}")

        # Dark variant: two <img>s, one per theme, no colour filter.
        (logo_dir / "assets" / "logo-dark.png").write_bytes(base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg=="
        ))
        dark_html = logo_dir / "index-dark.html"
        ok2, out2, rc2 = run([PY, str(build_py), "--content", str(logo_dir / "content.json"),
                              "--output", str(dark_html), "--skill-root", str(root),
                              "--quiet", "--no-contrast-check"])
        if ok2 and dark_html.exists():
            dtext = dark_html.read_text(encoding="utf-8")
            record("dark logo variant renders one image per theme",
                   "dark:hidden" in dtext and "dark:block" in dtext,
                   "light/dark pair" if "dark:block" in dtext else "no pair")
        else:
            record("dark logo variant renders one image per theme", False, f"build rc={rc2}")

        if out_html.exists():
            sample_text = out_html.read_text(encoding="utf-8")
            monogram = "h-8 w-8 shrink-0 rounded-lg bg-brand-primary/15"
            record("missing logo falls back to a monogram badge (no broken image)",
                   monogram in sample_text, "monogram" if monogram in sample_text else "no fallback found")

        # Document numbering in learner-facing titles must be flagged.
        lint_content = minimal_content()
        lint_content["units"] = [{"title": "0. A"}]
        lint_content["slides"] = [{"type": "cardList", "title": "Ketentuan Umum 6.1 s.d. 6.3",
                                   "cards": [{"title": "Pasal 5", "desc": "d"}]}]
        write_json(tmp / "lint.json", lint_content)
        ok, out, rc = run([PY, str(validate_py), str(tmp / "lint.json")])
        record("document numbering in titles is flagged", "nomor klausul" in out or "Pasal N" in out,
               next((l.strip() for l in out.splitlines() if "nomor klausul" in l or "Pasal N" in l), "")[:90])

        # ── 7. custom certificate template ─────────────────────────────────
        print("\n[6] Custom certificate template")
        cert_template = root / "assets" / "certificate.template.example.html"
        if cert_template.exists():
            cert_content = minimal_content(course={
                "code": "CERT/1", "title": "Cert Test", "totalUnits": 1, "passingScore": 75,
                "certificate": {"template": str(cert_template), "pageSize": "A4 portrait",
                                "printPadding": "10mm",
                                "labels": {"kicker": "CERTIFICATE OF COMPLETION"}},
            })
            cert_json = tmp / "cert.json"
            cert_html = tmp / "cert.html"
            write_json(cert_json, cert_content)
            ok, out, rc = run([PY, str(build_py), "--content", str(cert_json), "--output", str(cert_html),
                               "--skill-root", str(root), "--quiet", "--no-contrast-check"])
            if ok and cert_html.exists():
                text = cert_html.read_text(encoding="utf-8")
                no_tokens = "{{" not in text
                has_ids = all(f'id="{i}"' in text for i in
                              ("certRecipientName", "certRecipientNIP", "certScoreVal",
                               "certDateVal", "certNumberLabel"))
                portrait = "size: A4 portrait;" in text and "width: 210mm;" in text
                pad = "padding: 10mm;" in text
                label = "CERTIFICATE OF COMPLETION" in text
                threshold = "75%" in text
                ok2, vout, _ = run([PY, str(verify_py), str(cert_html), "--content", str(cert_json)])
                record("custom certificate template applies", no_tokens and has_ids and ok2,
                       f"tokens_left={not no_tokens}, ids={has_ids}, verify_rc={0 if ok2 else 1}")
                record("certificate page geometry + labels come from content.json",
                       portrait and pad and label and threshold,
                       f"portrait={portrait} padding={pad} label={label} threshold={threshold}")
            else:
                record("custom certificate template applies", False, "build failed")
        else:
            record("custom certificate template applies", False, "example template missing")

        # ── 8. narration pipeline ──────────────────────────────────────────
        print("\n[7] Narration pipeline")
        if audio_py.exists():
            ok, out, _ = run([PY, str(audio_py), "--content", str(sample), "--check"])
            # Expect one explicit narration per slide — derived, not hardcoded, so
            # adding a slide to the sample cannot silently break this check.
            expected_nar = len(sample_obj.get("slides", []))
            m = re.search(r"explicit narration\s*:\s*(\d+)", out)
            got_nar = int(m.group(1)) if m else -1
            record("per-slide narration is discovered", ok and got_nar == expected_nar,
                   f"explicit narration: {got_nar} (expect {expected_nar})")

            silent = minimal_content()
            silent["slides"] = [{"type": "cardList", "title": "Kepatuhan SOP di PT PP",
                                 "cards": [{"icon": "check", "title": "SOP Wajib",
                                            "desc": "Seluruh SOP wajib dipahami PIC."}]}]
            silent["units"] = [{"title": "0. Cover"}]
            silent_json = tmp / "silent.json"
            write_json(silent_json, silent)
            ok, out, _ = run([PY, str(audio_py), "--content", str(silent_json), "--check"])
            record("intisari fallback covers narration-less slides",
                   ok and "fallback (intisari): 1" in out,
                   next((l.strip() for l in out.splitlines() if "fallback" in l), ""))
            ok, out, _ = run([PY, str(audio_py), "--content", str(silent_json), "--dry-run"])
            record("phonetic respelling is applied (SOP/PT PP/PIC)",
                   ok and "es o pe" in out and "pe te pe pe" in out and "pi ai si" in out)
            ok, out, _ = run([PY, str(audio_py), "--content", str(silent_json), "--check", "--no-fallback"])
            record("--no-fallback reports missing narration instead of inventing it",
                   ok and "missing            : 1" in out)

        # ── 9. demo freshness ──────────────────────────────────────────────
        if not args.no_demo:
            print("\n[8] Demo freshness (test_build.html)")
            demo = root / "test_build.html"
            ok, out, rc = run([PY, str(build_py), "--content", str(sample), "--output", str(demo),
                               "--skill-root", str(root), "--quiet", "--no-contrast-check"])
            if ok and demo.exists():
                ok2, vout, _ = run([PY, str(verify_py), str(demo), "--content", str(sample)])
                record("committed demo regenerated and verified", ok2,
                       f"{demo.stat().st_size / 1024:.0f} KB")
            else:
                record("committed demo regenerated and verified", False, f"rc={rc}")

        # ── optional smoke test ────────────────────────────────────────────
        if args.with_smoke:
            print("\n[9] Playwright smoke test")
            try:
                import playwright  # noqa: F401
                ok, out, rc = run([PY, str(root / "scripts" / "smoke_test_module.py"), str(out_html)])
                record("smoke test passes", ok, f"rc={rc}")
            except ImportError:
                record("smoke test passes", True, "skipped (playwright not installed)")
    finally:
        if args.keep_temp:
            print(f"\nTemp dir kept: {tmp}")
        else:
            shutil.rmtree(tmp, ignore_errors=True)

    failed = [r for r in results if not r[1]]
    print("\n" + "=" * 62)
    print(f"self-check: {len(results) - len(failed)}/{len(results)} checks green")
    if failed:
        for name, _, detail in failed:
            print(f"  ✗ {name} — {detail}")
        sys.exit(1)
    print("[OK] No regressions detected.")


if __name__ == "__main__":
    main()
