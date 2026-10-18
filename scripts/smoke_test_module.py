"""Smoke test the built e-learning module with Playwright.

Opens the HTML file via file://, captures console errors + page errors, walks
EVERY slide through the renderer, and verifies the interactive subsystems that
a static HTML parser cannot see (navigation, quiz, tree canvas, modals,
certificate contract).

This is an OPTIONAL, browser-dependent check. It requires `playwright` plus a
Chromium build (pip install playwright && playwright install chromium) and
therefore cannot run in a locked-down/headless-less environment. When a browser
is unavailable, use the dependency-free gate instead:

  python3 tools/verify_module.py --content <content.json> <html_path>

USAGE
  python3 scripts/smoke_test_module.py <html_path> [--timeout MS]

Exit codes: 0 = clean, 1 = errors found, 2 = bad invocation / missing deps.
"""
import argparse
import sys
from pathlib import Path

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def load_playwright():
    try:
        from playwright.sync_api import sync_playwright
        return sync_playwright
    except ImportError:
        print(
            "ERROR: the 'playwright' package is not installed.\n"
            "       pip install playwright && playwright install chromium\n"
            "       Offline alternative: python3 tools/verify_module.py <html>",
            file=sys.stderr,
        )
        sys.exit(2)


def find_local_chromium():
    """Locate an already-downloaded Chromium when the bundled revision is missing.

    Playwright pins an exact browser build (e.g. `.../chromium-1248/`), so a
    machine that already has a slightly older ms-playwright cache fails to launch
    even though a perfectly usable Chromium is sitting right there. Reuse the
    newest cached build instead of forcing a ~150 MB download.
    """
    import glob
    import os

    patterns = [
        os.path.expandvars(r"%LOCALAPPDATA%\ms-playwright\chromium-*\chrome-win64\chrome.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\ms-playwright\chromium-*\chrome-win\chrome.exe"),
        os.path.expanduser("~/.cache/ms-playwright/chromium-*/chrome-linux/chrome"),
        os.path.expanduser("~/Library/Caches/ms-playwright/chromium-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium"),
    ]
    found = []
    for pattern in patterns:
        found.extend(glob.glob(pattern))

    def revision(path):
        for part in Path(path).parts:
            if part.startswith("chromium-"):
                try:
                    return int(part.split("-")[1])
                except (IndexError, ValueError):
                    return 0
        return 0

    return sorted(found, key=revision)[-1] if found else None


def launch_browser(p, executable=None):
    """Launch headless Chromium, falling back to any cached build if needed."""
    try:
        return p.chromium.launch(headless=True, args=["--no-sandbox"])
    except Exception as first_error:
        exe = executable or find_local_chromium()
        if not exe:
            raise first_error
        print(f"  (bundled Chromium missing — reusing {exe})")
        return p.chromium.launch(headless=True, args=["--no-sandbox"], executable_path=exe)


def slides_of_type(page, type_name):
    """Indices of slides whose type matches — never hardcode sample indices."""
    return page.evaluate(
        "(t) => COURSE.slides.map((s, i) => s.type === t ? i : -1).filter(i => i >= 0)",
        type_name,
    )


def main():
    ap = argparse.ArgumentParser(description="Playwright smoke test for a built Modul PP module")
    ap.add_argument("html", help="Path to the built HTML module")
    ap.add_argument("--timeout", type=int, default=30000, help="Navigation timeout in ms")
    ap.add_argument("--settle", type=int, default=350, help="Per-slide settle time in ms")
    ap.add_argument("--executable-path", default=None,
                    help="Chromium executable to use when Playwright's pinned build is absent")
    args = ap.parse_args()

    sync_playwright = load_playwright()

    html_path = Path(args.html).resolve()
    if not html_path.exists():
        print(f"ERROR: {html_path} not found", file=sys.stderr)
        sys.exit(2)

    url = html_path.as_uri()
    print(f"Loading: {url}")

    errors = []
    warnings = []
    logs = []

    with sync_playwright() as p:
        browser = launch_browser(p, args.executable_path)
        page = browser.new_page()
        page.on("console", lambda msg: (
            errors.append(f"[{msg.type}] {msg.text}") if msg.type == "error"
            else warnings.append(f"[{msg.type}] {msg.text}") if msg.type == "warning"
            else logs.append(f"[{msg.type}] {msg.text}")
        ))
        page.on("pageerror", lambda err: errors.append(f"[PAGEERROR] {err}"))

        page.goto(url, wait_until="networkidle", timeout=args.timeout)
        page.wait_for_timeout(1200)

        # ── Static chrome ───────────────────────────────────────────────────
        checks = [
            ("#topHeader", "Top header"),
            ("#courseSidebar", "Sidebar"),
            ("#slideBody", "Slide body"),
            ("#bottomPlaybar", "Bottom playbar"),
            ("#seekBar", "Seekbar"),
            ("#btnNextSlide", "Next button"),
            ("#btnPrevSlide", "Prev button"),
            ("#slideCounterText", "Slide counter"),
            ("#overallPercentage", "Progress %"),
            ("#outlineNavList", "Outline list"),
            ("#notesTextContainer", "Notes container"),
            ("#captionText", "Caption text"),
            ("#certificatePrintArea", "Certificate print area"),
        ]
        print("\n=== DOM element checks ===")
        for sel, name in checks:
            present = page.locator(sel).count() > 0
            print(f"  {'✓' if present else '✗ MISSING'} {sel} ({name})")
            if not present:
                errors.append(f"missing DOM element {sel} ({name})")

        # ── COURSE object ───────────────────────────────────────────────────
        print("\n=== COURSE object check ===")
        slide_types = []
        if not page.evaluate("typeof COURSE !== 'undefined' && COURSE !== null"):
            print("  ✗ COURSE is not loaded")
            errors.append("COURSE object not loaded")
        else:
            n_units = page.evaluate("COURSE.units.length")
            n_slides = page.evaluate("COURSE.slides.length")
            slide_types = page.evaluate("COURSE.slides.map(s => s.type)")
            print(f"  ✓ units={n_units} slides={n_slides}")
            if n_units != n_slides:
                errors.append(f"units.length ({n_units}) != slides.length ({n_slides})")
            # Unlock scripted navigation: goToSlide() reads both flags live.
            page.evaluate("COURSE.course.devMode = true; COURSE.course.enableGatingTimer = false;")
            print("  ✓ gating disabled for scripted navigation (devMode=true, enableGatingTimer=false)")

        # ── Walk every slide ────────────────────────────────────────────────
        print("\n=== Slide render walk (all slides) ===")
        if slide_types:
            for idx, stype in enumerate(slide_types):
                try:
                    page.evaluate("(i) => goToSlide(i)", idx)
                    page.wait_for_timeout(args.settle)
                    body = page.locator("#slideBody").inner_text()
                    problem = None
                    if "Unknown slide type" in body:
                        problem = "renderer reported 'Unknown slide type'"
                    elif "cannot read" in body.lower():
                        problem = "renderer error text visible"
                    elif len(body.strip()) < 12:
                        problem = "slide rendered (almost) empty"
                    if problem:
                        errors.append(f"slide {idx} ({stype}): {problem}")
                        print(f"  ✗ {idx:>2} {stype:<20} {problem}")
                    else:
                        print(f"  ✓ {idx:>2} {stype:<20} {len(body)} chars")
                except Exception as e:
                    errors.append(f"slide {idx} ({stype}): goToSlide threw {e}")
                    print(f"  ✗ {idx:>2} {stype:<20} goToSlide threw: {e}")

        # ── Quiz slide ──────────────────────────────────────────────────────
        print("\n=== Quiz slide test ===")
        quiz_idx = slides_of_type(page, "quiz") if slide_types else []
        if not quiz_idx:
            print("  – no quiz slide in this module, skipped")
        else:
            q = quiz_idx[0]
            try:
                page.evaluate("(i) => goToSlide(i)", q)
                page.wait_for_timeout(args.settle)
                has_container = page.locator("#quizContainer").count() > 0
                print(f"  ✓ quiz at slide {q}, #quizContainer present: {has_container}")
                if not has_container:
                    errors.append("quiz slide rendered without #quizContainer")
                ask = page.evaluate("(i) => COURSE.slides[i].askParticipantInfo !== false", q)
                identity = page.locator("#participantNameInput").count() > 0
                print(f"  ✓ askParticipantInfo={ask} → identity card present: {identity}")
                if ask and not identity:
                    errors.append("identity card missing although askParticipantInfo is not false")
                if not ask and identity:
                    errors.append("identity card rendered although askParticipantInfo=false")
            except Exception as e:
                errors.append(f"quiz slide test failed: {e}")
                print(f"  ✗ quiz slide test failed: {e}")

        # ── Tree canvas ─────────────────────────────────────────────────────
        print("\n=== Tree canvas test ===")
        tree_idx = slides_of_type(page, "treeCanvas") if slide_types else []
        if not tree_idx:
            print("  – no treeCanvas slide in this module, skipped")
        else:
            t = tree_idx[0]
            try:
                page.evaluate("(i) => goToSlide(i)", t)
                page.wait_for_timeout(args.settle + 300)
                nodes = page.locator(".flow-card-node").count()
                col3 = page.locator("#treeCanvasInner .col-span-3").count()
                col6 = page.locator("#treeCanvasInner .col-span-6").count()
                fases = page.locator("#treeCanvasInner [id^='fase-']").count()
                print(f"  ✓ treeCanvas at slide {t}: nodes={nodes}, col-span-3={col3}, col-span-6={col6}, fases={fases}")
                if col3 == 0 or col6 == 0:
                    errors.append("treeCanvas: 3-column layout not rendered (col-span-3/col-span-6 missing)")
                if fases == 0:
                    errors.append("treeCanvas: phase containers (#fase-N) not rendered")
            except Exception as e:
                errors.append(f"treeCanvas slide test failed: {e}")
                print(f"  ✗ treeCanvas test failed: {e}")

        # ── Header logo + card balance ──────────────────────────────────────
        print("\n=== Header logo + card balance ===")
        logo_state = page.evaluate("""() => {
          const header = document.getElementById('topHeader');
          const imgs = Array.from(header.querySelectorAll('img'));
          const mono = header.querySelector('.h-8.w-8.rounded-lg');
          const themed = imgs.some(i => (i.className || '').includes('dark:brightness-0')
                                      || (i.className || '').includes('dark:block')
                                      || (i.className || '').includes('dark:hidden'));
          return {
            images: imgs.length,
            monogram: !!mono,
            themeAdaptive: themed,
            src: imgs.length ? imgs[0].getAttribute('src').slice(0, 24) : null
          };
        }""")
        print(f"  ✓ header logo: images={logo_state['images']} monogram={logo_state['monogram']} "
              f"theme-adaptive={logo_state['themeAdaptive']} src={logo_state['src']}")
        if not (logo_state["images"] or logo_state["monogram"]):
            errors.append("header shows neither a logo image nor a monogram fallback")
        if logo_state["images"] and not logo_state["themeAdaptive"]:
            errors.append("header logo has no dark-mode treatment (not theme-adaptive)")

        # Odd card counts must not leave a hole: the lone card is centred.
        balance = page.evaluate("""() => {
          const certIdx = COURSE.slides.findIndex(s => s.type === 'summaryCertificate');
          const idx = certIdx === -1 ? COURSE.slides.length : certIdx;
          COURSE.slides.splice(idx, 0, {
            type: 'cardList', columns: 2, title: 'Balance test',
            cards: [{title:'a',desc:'d'}, {title:'b',desc:'d'}, {title:'c',desc:'d'}]
          });
          COURSE.units.splice(idx, 0, {title: 'Balance', duration: '00:10'});
          goToSlide(idx);
          const grid = document.querySelector('.cardgrid');
          if (!grid) return { missing: true };
          const kids = Array.from(grid.children);
          const last = kids[kids.length - 1].getBoundingClientRect();
          const box = grid.getBoundingClientRect();
          return {
            cards: kids.length,
            leftGap: Math.round(last.left - box.left),
            rightGap: Math.round(box.right - last.right),
            cols: grid.getAttribute('data-cols')
          };
        }""")
        if balance.get("missing"):
            errors.append("card grid did not render a .cardgrid container")
            print("  ✗ .cardgrid not found")
        else:
            delta = abs(balance["leftGap"] - balance["rightGap"])
            print(f"  ✓ odd card row ({balance['cards']} cards, cols={balance['cols']}): "
                  f"left gap={balance['leftGap']}px right gap={balance['rightGap']}px")
            if delta > 4:
                errors.append(f"card grid last row is not centred (left {balance['leftGap']} vs right {balance['rightGap']})")

        # ── Question engine (7 types) ───────────────────────────────────────
        print("\n=== Question engine test ===")
        grading = page.evaluate("""() => {
          const multiQ = {type:'multipleResponse', options:['a','b','c'], correctIndexes:[0,2]};
          const orderQ = {type:'ordering', items:['a','b','c']};
          const matchQ = {type:'matching', pairs:[{left:'x',right:'1'},{left:'y',right:'2'}]};
          const numQ = {type:'numeric', answer:100, tolerance:5};
          return {
            multi_ok: isAnswerCorrect(multiQ, [2,0]),
            multi_extra: isAnswerCorrect(multiQ, [0,1,2]),
            multi_missing: isAnswerCorrect(multiQ, [0]),
            order_ok: isAnswerCorrect(orderQ, [0,1,2]),
            order_bad: isAnswerCorrect(orderQ, [1,0,2]),
            order_partial: isAnswerCorrect(orderQ, [0,1]),
            match_ok: isAnswerCorrect(matchQ, [0,1]),
            match_swapped: isAnswerCorrect(matchQ, [1,0]),
            match_partial: isAnswerCorrect(matchQ, [0,null]),
            num_exact: isAnswerCorrect({type:'numeric', answer:3}, '3'),
            num_comma: isAnswerCorrect({type:'numeric', answer:2.5, tolerance:0.1}, '2,45'),
            num_wrong: isAnswerCorrect({type:'numeric', answer:3}, '4'),
            num_tolerance: isAnswerCorrect(numQ, '104'),
            unanswered_order: isAnswered(orderQ, [0,1]),
            answered_order: isAnswered(orderQ, [0,1,2]),
            answered_multi_empty: isAnswered(multiQ, [])
          };
        }""")
        expectations = {
            "multi_ok": True, "multi_extra": False, "multi_missing": False,
            "order_ok": True, "order_bad": False, "order_partial": False,
            "match_ok": True, "match_swapped": False, "match_partial": False,
            "num_exact": True, "num_comma": True, "num_wrong": False, "num_tolerance": True,
            "unanswered_order": False, "answered_order": True, "answered_multi_empty": False,
        }
        for name, expected in expectations.items():
            got = grading.get(name)
            ok = got == expected
            print(f"  {'✓' if ok else '✗'} {name} = {got} (expect {expected})")
            if not ok:
                errors.append(f"question grading: {name} expected {expected}, got {got}")

        rendered = page.evaluate("""() => {
          const ctx = {target:'quiz', index:0};
          return {
            multi: renderQuestionInput({type:'multipleResponse', options:['a','b']}, undefined, ctx).includes('role="checkbox"'),
            order: renderQuestionInput({type:'ordering', items:['a','b']}, undefined, ctx).includes('Urutan Anda'),
            match: renderQuestionInput({type:'matching', pairs:[{left:'x',right:'1'},{left:'y',right:'2'}]}, undefined, ctx).includes('<select'),
            numeric: renderQuestionInput({type:'numeric', answer:1}, undefined, ctx).includes('type="number"')
          };
        }""")
        for name, ok in rendered.items():
            print(f"  {'✓' if ok else '✗'} render {name}: {ok}")
            if not ok:
                errors.append(f"question renderer missing for {name}")

        # ── In-slide checkpoint (formative) ─────────────────────────────────
        print("\n=== Checkpoint test ===")
        cp_idx = page.evaluate("() => COURSE.slides.findIndex(s => s.checkpoint && s.checkpoint.question)")
        if cp_idx < 0:
            print("  – no checkpoint in this module, skipped")
        else:
            page.evaluate("(i) => goToSlide(i)", cp_idx)
            page.wait_for_timeout(args.settle)
            has_panel = page.locator("#checkpointPanel").count() > 0
            print(f"  ✓ checkpoint at slide {cp_idx}, panel present: {has_panel}")
            if not has_panel:
                errors.append("checkpoint panel not mounted")
            else:
                result = page.evaluate("""(i) => {
                  const q = COURSE.slides[i].checkpoint.question;
                  const target = 'cp:' + i;
                  const correct = (() => {
                    switch (q.type) {
                      case 'mcq': return q.correctIndex;
                      case 'trueFalse': return q.correctBool;
                      case 'fillIn': return (q.acceptedAnswers || [''])[0];
                      case 'multipleResponse': return (q.correctIndexes || []).slice();
                      case 'ordering': return (q.correctOrder && q.correctOrder.length) ? q.correctOrder.slice() : q.items.map((_, k) => k);
                      case 'matching': return q.pairs.map((_, k) => k);
                      case 'numeric': return String(q.answer);
                      default: return null;
                    }
                  })();
                  // Empty answer must be rejected before grading.
                  answerStore(target).set(0, q.type === 'multipleResponse' || q.type === 'ordering' ? [] : '');
                  checkCheckpoint(target);
                  const rejectedEmpty = state.checkpointResult[target] === undefined;
                  // Correct answer must complete it and release the gate.
                  answerStore(target).set(0, correct);
                  checkCheckpoint(target);
                  return {
                    rejectedEmpty: rejectedEmpty,
                    result: state.checkpointResult[target],
                    panelDone: document.getElementById('checkpointPanel').innerText.includes('Selesai'),
                    slideCompleted: state.completedSlides.has(i),
                    scoreUntouched: state.quizScore === 0 && state.quizAttemptCount === 0
                  };
                }""", cp_idx)
                print(f"  ✓ empty answer rejected before grading: {result['rejectedEmpty']}")
                print(f"  ✓ correct answer → result={result['result']}, panel done={result['panelDone']}")
                print(f"  ✓ slide gate released: {result['slideCompleted']}")
                print(f"  ✓ formative: score/attempts untouched: {result['scoreUntouched']}")
                if not result["rejectedEmpty"]:
                    errors.append("checkpoint graded an empty answer")
                if result["result"] != "ok" or not result["panelDone"]:
                    errors.append("checkpoint did not report success after the correct answer")
                if not result["slideCompleted"]:
                    errors.append("checkpoint success did not release the slide gate")
                if not result["scoreUntouched"]:
                    errors.append("checkpoint leaked into quizScore/quizAttemptCount — formative boundary broken")

        # ── Hotspot image: explore mode ─────────────────────────────────────
        print("\n=== Hotspot image test (explore) ===")
        hs_idx = slides_of_type(page, "hotspotImage")
        if not hs_idx:
            print("  – no hotspotImage slide in this module, skipped")
        else:
            h = hs_idx[0]
            page.evaluate("(i) => goToSlide(i)", h)
            page.wait_for_timeout(args.settle)
            pins = page.locator("[data-hotspot-pin]").count()
            expected_pins = page.evaluate("(i) => (COURSE.slides[i].hotspots || []).length", h)
            print(f"  ✓ slide {h}: {pins} pin(s) (expect {expected_pins})")
            if pins != expected_pins or pins == 0:
                errors.append(f"hotspotImage rendered {pins} pins, expected {expected_pins}")

            page.locator("[data-hotspot-pin]").first.click()
            page.wait_for_timeout(200)
            detail = page.locator("#hotspotDetail").inner_text()
            progress = page.locator("#hotspotProgress").inner_text().strip()
            title1 = page.evaluate("(i) => (COURSE.slides[i].hotspots[0].title || '')", h)
            print(f"  ✓ click pin 1 → progress '{progress}', detail shows title: {title1 in detail}")
            if title1 and title1 not in detail:
                errors.append("hotspotImage detail panel did not show the hotspot title")

            page.locator("[data-hotspot-pin]").nth(1).focus()
            page.keyboard.press("Enter")
            page.wait_for_timeout(200)
            progress2 = page.locator("#hotspotProgress").inner_text().strip()
            print(f"  ✓ keyboard Enter on pin 2 → '{progress2}'")
            if progress2 == progress:
                errors.append("hotspotImage keyboard activation did not register")

            for k in range(2, pins):
                page.locator("[data-hotspot-pin]").nth(k).click()
                page.wait_for_timeout(120)
            hs_state = page.evaluate("""(i) => ({
              found: ((state.hotspots || {})[String(i)] || {}).found.length,
              completed: state.completedSlides.has(i),
              detail: document.getElementById('hotspotDetail').innerText,
              score: state.quizScore,
              attempts: state.quizAttemptCount
            })""", h)
            print(f"  ✓ all pins opened: found={hs_state['found']}, slide completed={hs_state['completed']}")
            print(f"  ✓ complete note shown: {'Semua titik sudah dibuka' in hs_state['detail']}")
            print(f"  ✓ formative: score={hs_state['score']} attempts={hs_state['attempts']}")
            if hs_state["found"] != expected_pins:
                errors.append("hotspotImage did not record every opened pin")
            if not hs_state["completed"]:
                errors.append("hotspotImage completion did not release the slide gate")
            if "Semua titik sudah dibuka" not in hs_state["detail"]:
                errors.append("hotspotImage completion note missing")
            if hs_state["score"] != 0 or hs_state["attempts"] != 0:
                errors.append("hotspotImage leaked into the quiz score/attempts")

            # ── Hotspot image: find mode (synthetic slide, keeps the sample small) ──
            print("\n=== Hotspot image test (find mode) ===")
            find_idx = page.evaluate("""() => {
              const src = COURSE.slides.find(s => s.type === 'hotspotImage').src;
              // Insert BEFORE the certificate slide: goToSlide() intentionally blocks
              // navigation to the certificate (and anything after it) until the quiz passes.
              const certIdx = COURSE.slides.findIndex(s => s.type === 'summaryCertificate');
              const idx = certIdx === -1 ? COURSE.slides.length : certIdx;
              COURSE.slides.splice(idx, 0, {
                type: 'hotspotImage', mode: 'find', title: 'Find test', lead: 'Klik target.',
                src: src, alt: 'test', wrongNote: 'Bukan titik yang dimaksud.',
                hotspots: [
                  {id: 'c1', x: 30, y: 30, title: 'Target', correct: true},
                  {id: 'c2', x: 70, y: 70, title: 'Decoy'}
                ]
              });
              COURSE.units.splice(idx, 0, {title: 'Find test', duration: '00:10'});
              goToSlide(idx);
              return idx;
            }""")
            page.wait_for_timeout(args.settle)
            find = page.evaluate("""(idx) => {
              const pins = document.querySelectorAll('[data-hotspot-pin]');
              const decoy = document.querySelector('[data-hotspot-pin="c2"]');
              if (!decoy) return {pins: pins.length, missing: true};
              decoy.click();
              const st1 = (state.hotspots || {})[String(idx)] || {};
              const afterDecoy = {
                found: (st1.found || []).length,
                wrong: (st1.wrong || []).length,
                detail: document.getElementById('hotspotDetail').innerText,
                label: decoy.getAttribute('data-wrong')
              };
              document.querySelector('[data-hotspot-pin="c1"]').click();
              const st2 = (state.hotspots || {})[String(idx)] || {};
              return {
                pins: pins.length,
                afterDecoy: afterDecoy,
                afterCorrect: {
                  found: (st2.found || []).length,
                  completed: state.completedSlides.has(idx),
                  progress: document.getElementById('hotspotProgress').innerText
                }
              };
            }""", find_idx)
            if find.get("missing"):
                errors.append("find-mode synthetic slide did not render its pins")
                print(f"  ✗ pins rendered: {find['pins']}")
            else:
                print(f"  ✓ {find['pins']} pin(s), decoy click → found={find['afterDecoy']['found']} "
                      f"wrong={find['afterDecoy']['wrong']} flagged={find['afterDecoy']['label']}")
                print(f"  ✓ decoy feedback shown: {'Bukan titik' in find['afterDecoy']['detail']}")
                print(f"  ✓ correct click → found={find['afterCorrect']['found']}, "
                      f"completed={find['afterCorrect']['completed']}, progress='{find['afterCorrect']['progress'].strip()}'")
                if find["pins"] != 2:
                    errors.append("find-mode slide did not render both pins")
                if find["afterDecoy"]["found"] != 0 or find["afterDecoy"]["wrong"] != 1:
                    errors.append("find mode counted a decoy as found")
                if "Bukan titik" not in find["afterDecoy"]["detail"]:
                    errors.append("find mode did not explain the decoy pick")
                if find["afterCorrect"]["found"] != 1 or not find["afterCorrect"]["completed"]:
                    errors.append("find mode did not complete after the correct hotspot")

        # ── Branching scenario (formative decision tree) ────────────────────
        print("\n=== Branching scenario test ===")
        br_idx = slides_of_type(page, "branchingScenario")
        if not br_idx:
            print("  – no branchingScenario slide in this module, skipped")
        else:
            b = br_idx[0]
            page.evaluate("(i) => goToSlide(i)", b)
            page.wait_for_timeout(args.settle)
            branch = page.evaluate("""(i) => {
              const def = COURSE.slides[i];
              const stage = () => document.getElementById('branchingStage');
              const buttons = () => Array.from(document.querySelectorAll('#branchingStage [role="group"] button'));
              const startNode = def.nodes.find(n => n.id === def.start) || {};
              const out = {
                startTitle: startNode.title || '',
                rendered: stage().innerText,
                choiceCount: buttons().length,
                expectedChoices: (startNode.choices || []).length
              };
              const wrongIdx = (startNode.choices || []).findIndex(c => c.correct !== true);
              const rightIdx = (startNode.choices || []).findIndex(c => c.correct === true);
              out.hasWrong = wrongIdx >= 0;
              out.hasRight = rightIdx >= 0;

              if (wrongIdx >= 0) {
                buttons()[wrongIdx].click();
                const st = state.branching[String(i)] || {};
                out.afterWrong = {
                  text: stage().innerText,
                  completed: state.completedSlides.has(i),
                  done: !!st.done,
                  correct: !!st.correct
                };
                restartBranching(i);
                const st2 = state.branching[String(i)] || {};
                out.afterRestart = { picks: (st2.picks || []).length, done: !!st2.done, node: st2.node };
              }
              if (rightIdx >= 0) {
                buttons()[rightIdx].click();
                const st3 = state.branching[String(i)] || {};
                out.afterRight = {
                  completed: state.completedSlides.has(i),
                  correct: !!st3.correct,
                  text: stage().innerText,
                  score: state.quizScore,
                  attempts: state.quizAttemptCount
                };
              }
              return out;
            }""", b)

            print(f"  ✓ start node '{branch['startTitle']}' with {branch['choiceCount']} choice(s) "
                  f"(expect {branch['expectedChoices']})")
            if branch["choiceCount"] != branch["expectedChoices"] or branch["choiceCount"] == 0:
                errors.append("branchingScenario did not render the start node's choices")
            if branch["startTitle"] and branch["startTitle"] not in branch["rendered"]:
                errors.append("branchingScenario start node title missing from the stage")

            if branch.get("hasWrong"):
                w = branch["afterWrong"]
                print(f"  ✓ wrong path → done={w['done']} correct={w['correct']} "
                      f"slide completed={w['completed']} (must be False)")
                if not w["done"] or w["correct"] or w["completed"]:
                    errors.append("branchingScenario wrong path did not end as a failure")
                r = branch["afterRestart"]
                print(f"  ✓ restart → picks={r['picks']} done={r['done']} node={r['node']}")
                if r["picks"] != 0 or r["done"]:
                    errors.append("branchingScenario restart did not reset the walk")

            if branch.get("hasRight"):
                good = branch["afterRight"]
                print(f"  ✓ correct path → correct={good['correct']} slide completed={good['completed']}")
                print(f"  ✓ formative: score={good['score']} attempts={good['attempts']}")
                if not good["correct"] or not good["completed"]:
                    errors.append("branchingScenario correct path did not complete the exercise")
                if good["score"] != 0 or good["attempts"] != 0:
                    errors.append("branchingScenario leaked into the quiz score/attempts")

        # ── Drag-drop set: click-to-place (primary) + HTML5 drag ────────────
        print("\n=== Drag-drop set test ===")
        dd_idx = slides_of_type(page, "dragDropSet")
        if not dd_idx:
            print("  – no dragDropSet slide in this module, skipped")
        else:
            d = dd_idx[0]
            page.evaluate("(i) => goToSlide(i)", d)
            page.wait_for_timeout(args.settle)

            info = page.evaluate("""(i) => {
              const def = COURSE.slides[i];
              return {
                items: (def.items || []).length,
                buckets: (def.buckets || []).length,
                pool: document.querySelectorAll('#ddPool [data-dd-item]').length,
                bucketEls: document.querySelectorAll('[data-dd-bucket]').length,
                firstItem: (def.items || [])[0] || null
              };
            }""", d)
            print(f"  ✓ {info['items']} item(s), {info['buckets']} bucket(s); pool={info['pool']} "
                  f"buckets rendered={info['bucketEls']}")
            if info["pool"] != info["items"] or info["bucketEls"] != info["buckets"]:
                errors.append("dragDropSet did not render the pool/buckets")

            # --- HTML5 drag path (mouse users) ---
            first = info["firstItem"]
            if first:
                page.locator(f'[data-dd-item="{first["id"]}"]').drag_to(
                    page.locator(f'[data-dd-bucket="{first["bucket"]}"]'))
                page.wait_for_timeout(250)
                dragged = page.evaluate("(i) => (state.dragdrop[String(i)] || {}).placed || {}", d)
                print(f"  ✓ HTML5 drag '{first['id']}' → bucket '{first['bucket']}': "
                      f"placed={dragged.get(str(first['id']))}")
                if dragged.get(str(first["id"])) != str(first["bucket"]):
                    errors.append("dragDropSet HTML5 drag did not place the item")

            # --- click-to-place path (keyboard / touch) with a deliberate mistake ---
            page.evaluate("(i) => resetDragSet(i)", d)
            page.wait_for_timeout(150)

            def place(item_id, bucket_id):
                page.locator(f'[data-dd-item="{item_id}"]').first.click()
                page.locator(f'[data-dd-bucket="{bucket_id}"] button').last.click()
                page.wait_for_timeout(120)

            def bucket_of(item_id):
                return page.evaluate("""(a) => {
                  const [i, id] = a;
                  return ((state.dragdrop[String(i)] || {}).placed || {})[id] || null;
                }""", [d, item_id])

            # Put the first item in the WRONG bucket, then check → must not complete.
            wrong_bucket = page.evaluate("""(i) => {
              const def = COURSE.slides[i];
              const it = def.items[0];
              const other = def.buckets.find(b => b.id !== it.bucket) || def.buckets[0];
              return other.id;
            }""", d)
            place(first["id"], wrong_bucket)
            print(f"  ✓ click-to-place '{first['id']}' → '{bucket_of(first['id'])}' (deliberately wrong)")
            page.locator("#ddFeedback").wait_for(state="attached")

            # Place the remaining items correctly, then check with one wrong.
            remaining = page.evaluate("(i) => COURSE.slides[i].items.slice(1).map(it => [it.id, it.bucket])", d)
            for item_id, bucket_id in remaining:
                place(item_id, bucket_id)
            page.evaluate("(i) => checkDragSet(i)", d)
            page.wait_for_timeout(200)
            partial = page.evaluate("""(i) => ({
              results: (state.dragdrop[String(i)] || {}).results || {},
              completed: state.completedSlides.has(i),
              feedback: document.getElementById('ddFeedback').innerText,
              score: state.quizScore,
              attempts: state.quizAttemptCount
            })""", d)
            print(f"  ✓ check with one wrong → completed={partial['completed']} "
                  f"feedback='{partial['feedback'].strip()[:48]}'")
            if partial["completed"]:
                errors.append("dragDropSet completed even though one item was in the wrong bucket")
            if partial["results"].get(str(first["id"])) is not False:
                errors.append("dragDropSet did not flag the misplaced item")
            if not partial["feedback"].strip():
                errors.append("dragDropSet produced no feedback after checking")

            # Correct the mistake: click the placed chip to return it, then place it right.
            page.locator(f'[data-dd-item="{first["id"]}"]').first.click()
            page.wait_for_timeout(120)
            place(first["id"], first["bucket"])
            page.evaluate("(i) => checkDragSet(i)", d)
            page.wait_for_timeout(200)
            done = page.evaluate("""(i) => ({
              completed: state.completedSlides.has(i),
              feedback: document.getElementById('ddFeedback').innerText,
              score: state.quizScore,
              attempts: state.quizAttemptCount
            })""", d)
            print(f"  ✓ all correct → completed={done['completed']}, feedback='{done['feedback'].strip()[:48]}'")
            print(f"  ✓ formative: score={done['score']} attempts={done['attempts']}")
            if not done["completed"]:
                errors.append("dragDropSet did not complete when every item was correct")
            if done["score"] != 0 or done["attempts"] != 0:
                errors.append("dragDropSet leaked into the quiz score/attempts")

        # ── Summative quiz end-to-end (mixed question types) ────────────────
        print("\n=== Summative quiz end-to-end ===")
        quiz_idx = slides_of_type(page, "quiz")
        if not quiz_idx:
            print("  – no quiz slide in this module, skipped")
        else:
            q = quiz_idx[0]
            page.evaluate("(i) => goToSlide(i)", q)
            page.wait_for_timeout(args.settle)
            outcome = page.evaluate("""(i) => {
              const qs = getCurrentQuizQuestions();
              const correctFor = (q) => {
                switch (q.type) {
                  case 'mcq': return q.correctIndex;
                  case 'trueFalse': return q.correctBool;
                  case 'fillIn': return (q.acceptedAnswers || [''])[0];
                  case 'multipleResponse': return (q.correctIndexes || []).slice();
                  case 'ordering': return (q.correctOrder && q.correctOrder.length) ? q.correctOrder.slice() : q.items.map((_, k) => k);
                  case 'matching': return q.pairs.map((_, k) => k);
                  case 'numeric': return String(q.answer);
                  default: return null;
                }
              };
              state.participantName = 'Peserta Uji';
              state.participantNIP = '12345678';
              qs.forEach((qq, qi) => { state.userAnswers[qi] = correctFor(qq); });
              const types = qs.map(qq => qq.type);
              submitQuizEvaluation();
              return {
                total: qs.length,
                types: types,
                score: state.quizScore,
                passed: state.quizPassed,
                completed: state.quizCompleted,
                attempt: state.quizAttemptCount,
                reviewRendered: (document.getElementById('slideBody').innerText || '').length > 40
              };
            }""", q)
            print(f"  ✓ {outcome['total']} questions, types: {', '.join(sorted(set(outcome['types'])))}")
            print(f"  ✓ score={outcome['score']} passed={outcome['passed']} completed={outcome['completed']} attempt={outcome['attempt']}")
            print(f"  ✓ review screen rendered: {outcome['reviewRendered']}")
            if outcome["score"] != 100 or not outcome["passed"]:
                errors.append(
                    f"all-correct quiz scored {outcome['score']} (expected 100) — a question type is "
                    "graded wrong or answers are lost"
                )
            if not outcome["completed"]:
                errors.append("quiz submission did not set quizCompleted")
            if not outcome["reviewRendered"]:
                errors.append("quiz review screen did not render")

        # ── Certificate contract ────────────────────────────────────────────
        print("\n=== Certificate contract test ===")
        cert_ids = page.evaluate(
            "() => ['certRecipientName','certRecipientNIP','certScoreVal','certDateVal','certNumberLabel']"
            ".map(id => !!document.getElementById(id))"
        )
        print(f"  ✓ certificate nodes resolve: {cert_ids}")
        if not all(cert_ids):
            errors.append("certificate contract ids missing at runtime")
        try:
            page.evaluate("() => { window.print = () => {}; printCertificate(); }")
            print("  ✓ printCertificate() executed without throwing (window.print stubbed)")
        except Exception as e:
            errors.append(f"printCertificate() threw: {e}")
            print(f"  ✗ printCertificate() threw: {e}")

        # ── Modals ──────────────────────────────────────────────────────────
        print("\n=== Modal tests ===")
        for fn, modal in (("openTenggatModal", "modalTenggat"),
                          ("openTerminologiModal", "modalTerminologi"),
                          ("openHintModal", "modalHint")):
            try:
                page.evaluate(f"() => {fn}()")
                page.wait_for_timeout(200)
                is_open = page.evaluate(f"() => document.getElementById('{modal}').open")
                print(f"  ✓ {fn}() → {modal}.open = {is_open}")
                page.evaluate(f"() => document.getElementById('{modal}').close()")
            except Exception as e:
                print(f"  – {fn}() skipped/failed: {e}")

        browser.close()

    # Missing-asset console errors are benign for offline/sample builds.
    missing_assets = [e for e in errors if "ERR_FILE_NOT_FOUND" in e]
    errors = [e for e in errors if "ERR_FILE_NOT_FOUND" not in e]
    warnings.extend(
        f"[benign] {e} — referenced asset not bundled (expected for sample/offline builds)"
        for e in missing_assets
    )

    print("\n=== Summary ===")
    print(f"Errors:   {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    if errors:
        print("\n--- ERRORS ---")
        for e in errors[:15]:
            print(f"  {e}")
    if warnings:
        print("\n--- WARNINGS (non-fatal) ---")
        for w in warnings[:10]:
            print(f"  {w}")
    sys.exit(0 if not errors else 1)


if __name__ == "__main__":
    main()
