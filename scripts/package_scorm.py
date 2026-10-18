#!/usr/bin/env python3
"""
package_scorm.py — SCORM 1.2 & 2004 LMS Packaging Helper for Modul PP

Bundles a standalone e-learning HTML module and its assets into a standard,
LMS-compliant SCORM .zip package with valid imsmanifest.xml metadata.
Ready for deployment to Moodle, SAP SuccessFactors, Canvas, Blackboard, Totara, etc.

USAGE:
  python scripts/package_scorm.py --html <path-to-html> [options]

OPTIONS:
  --html PATH           Path to the compiled HTML module (required)
  --output PATH         Path to write the output .zip file (default: same folder as HTML, <name>_scorm.zip)
  --content PATH        Path to content.json (optional, used to extract course title, code, and passing score)
  --version {1.2,2004}  SCORM standard version to target (default: 1.2)
  --audio-dir PATH      Path to optional audio directory to bundle into the package
  --assets-dir PATH     Path to optional assets directory to bundle into the package
  --title TEXT          Override course title in the manifest
  --identifier TEXT     Override package identifier (default: sanitized course code or timestamp)

EXAMPLES:
  # Package an HTML module into SCORM 1.2 zip
  python scripts/package_scorm.py --html dist/sop_module.html --content my_sop.content.json

  # Package with audio files into custom output path
  python scripts/package_scorm.py --html dist/sop_module.html --audio-dir ./audio --output dist/sop_scorm_v1.zip
"""

import argparse
import json
import os
import re
import sys
import time
import zipfile
from pathlib import Path

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass



def extract_course_literal(html_text: str):
    """Parse the injected `let COURSE = {...};` literal with brace matching.

    Regex sniffing for the first `"title": "..."` in the file picks up whatever
    object happens to come first, which is why the old fallback could report the
    wrong course title. This walks the JSON literal properly instead.
    """
    match = re.search(r"let\s+COURSE\s*=\s*\{", html_text)
    if not match:
        return None
    start = html_text.index("{", match.start())
    depth = 0
    in_string = False
    escaped = False
    for i in range(start, len(html_text)):
        ch = html_text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(html_text[start:i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def extract_metadata_from_html(html_path: Path):
    """Fallback metadata extractor if content.json is not supplied."""
    title = "Interactive E-Learning Course"
    code = "COURSE_001"
    passing_score = 80

    try:
        content = html_path.read_text(encoding="utf-8")
        course = extract_course_literal(content)
        if isinstance(course, dict):
            course_block = course.get("course") or {}
            title = course_block.get("title", title)
            code = course_block.get("code", code)
            passing_score = course_block.get("passingScore", passing_score)
        else:
            # Last-resort regex sniffing when the COURSE literal is unparseable.
            m_title = re.search(r'["\']title["\']\s*:\s*["\']([^"\']+)["\']', content)
            if m_title:
                title = m_title.group(1)
            m_code = re.search(r'["\']code["\']\s*:\s*["\']([^"\']+)["\']', content)
            if m_code:
                code = m_code.group(1)
            m_pass = re.search(r'["\']passingScore["\']\s*:\s*(\d+)', content)
            if m_pass:
                passing_score = int(m_pass.group(1))
    except Exception:
        pass

    return title, code, passing_score


def generate_manifest_scorm12(package_id: str, title: str, passing_score: int, files: list) -> str:
    escaped_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    file_elements = "\n".join([f'      <file href="{f}"/>' for f in files])

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="{package_id}" version="1.0"
          xmlns="http://www.imsproject.org/xsd/imscp_rootv1p1p2"
          xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_rootv1p2"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://www.imsproject.org/xsd/imscp_rootv1p1p2 imscp_rootv1p1p2.xsd
                              http://www.imsglobal.org/xsd/imsmd_rootv1p2p2 imsmd_rootv1p2p2.xsd
                              http://www.adlnet.org/xsd/adlcp_rootv1p2 adlcp_rootv1p2.xsd">
  <metadata>
    <schema>ADL SCORM</schema>
    <schemaversion>1.2</schemaversion>
  </metadata>
  <organizations default="org_{package_id}">
    <organization identifier="org_{package_id}">
      <title>{escaped_title}</title>
      <item identifier="item_{package_id}" identifierref="res_{package_id}">
        <title>{escaped_title}</title>
        <adlcp:masteryscore>{passing_score}</adlcp:masteryscore>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="res_{package_id}" type="webcontent" adlcp:scormtype="sco" href="index.html">
{file_elements}
    </resource>
  </resources>
</manifest>
"""


def generate_manifest_scorm2004(package_id: str, title: str, passing_score: int, files: list) -> str:
    escaped_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    file_elements = "\n".join([f'      <file href="{f}"/>' for f in files])
    scaled_score = f"{passing_score / 100:.2f}"

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="{package_id}" version="1.0"
          xmlns="http://www.imsglobal.org/xsd/imscp_v1p1"
          xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_v1p3"
          xmlns:adlseq="http://www.adlnet.org/xsd/adlseq_v1p3"
          xmlns:adlnav="http://www.adlnet.org/xsd/adlnav_v1p3"
          xmlns:imsss="http://www.imsglobal.org/xsd/imsss"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://www.imsglobal.org/xsd/imscp_v1p1 imscp_v1p1.xsd
                              http://www.adlnet.org/xsd/adlcp_v1p3 adlcp_v1p3.xsd
                              http://www.imsglobal.org/xsd/imsss imsss_v1p0.xsd">
  <metadata>
    <schema>ADL SCORM</schema>
    <schemaversion>2004 3rd Edition</schemaversion>
  </metadata>
  <organizations default="org_{package_id}">
    <organization identifier="org_{package_id}">
      <title>{escaped_title}</title>
      <item identifier="item_{package_id}" identifierref="res_{package_id}">
        <title>{escaped_title}</title>
        <imsss:sequencing>
          <imsss:objectives>
            <imsss:primaryObjective objectiveID="PRIMARY_OBJ">
              <imsss:minNormalizedMeasure>{scaled_score}</imsss:minNormalizedMeasure>
            </imsss:primaryObjective>
          </imsss:objectives>
        </imsss:sequencing>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="res_{package_id}" type="webcontent" adlcp:scormType="sco" href="index.html">
{file_elements}
    </resource>
  </resources>
</manifest>
"""


def package_scorm(args):
    html_path = Path(args.html).resolve()
    if not html_path.exists():
        print(f"[!] Error: HTML file not found: {html_path}", file=sys.stderr)
        sys.exit(1)

    title, code, passing_score = extract_metadata_from_html(html_path)

    # If content.json is supplied, override with precise values
    if args.content:
        content_path = Path(args.content).resolve()
        if content_path.exists():
            try:
                cdata = json.loads(content_path.read_text(encoding="utf-8"))
                course_info = cdata.get("course", {})
                title = course_info.get("title", title)
                code = course_info.get("code", code)
                passing_score = course_info.get("passingScore", passing_score)
            except Exception as e:
                print(f"[!] Warning reading content.json: {e}", file=sys.stderr)

    if args.title:
        title = args.title

    # Sanitize identifier
    raw_id = args.identifier or code or f"module_{int(time.time())}"
    package_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", raw_id).strip("_") or "SCORM_PACKAGE"

    # Determine output zip path
    if args.output:
        out_zip = Path(args.output).resolve()
    else:
        out_zip = html_path.parent / f"{html_path.stem}_scorm_{args.version}.zip"

    out_zip.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n📦 Modul PP SCORM Packager")
    print(f"====================================")
    print(f"Source HTML : {html_path.name}")
    print(f"Course Title: {title}")
    print(f"Course Code : {code}")
    print(f"Pass Score  : {passing_score}%")
    print(f"SCORM Ver   : {args.version}")
    print(f"Target Zip  : {out_zip}\n")

    files_in_manifest = ["index.html"]
    files_to_zip = []  # list of tuples: (source_path, zip_internal_path)

    # 1. Main HTML module -> index.html
    files_to_zip.append((html_path, "index.html"))

    # 2. Audio directory
    # The engine looks for ./audio/unit_<slideIndex>.mp3, so anything else in the
    # folder is bundled but never played — say so instead of shipping dead weight.
    if args.audio_dir:
        audio_dir = Path(args.audio_dir).resolve()
        if audio_dir.exists() and audio_dir.is_dir():
            matched, unmatched = [], []
            for af in sorted(audio_dir.glob("*.mp3")):
                (matched if re.fullmatch(r"unit_\d+\.mp3", af.name) else unmatched).append(af)
                arc_name = f"audio/{af.name}"
                files_to_zip.append((af, arc_name))
                files_in_manifest.append(arc_name)
            print(f"[*] Added {len(matched) + len(unmatched)} audio file(s) from: {audio_dir}")
            if unmatched:
                print("[!] Warning: these files do not follow the ./audio/unit_<N>.mp3 convention "
                      "and the engine will never request them:")
                for af in unmatched[:10]:
                    print(f"      - {af.name}")
        else:
            print(f"[!] Warning: Audio directory not found: {audio_dir}")
    else:
        # Pre-flight: does the module reference local audio that is not bundled?
        try:
            referenced = set(re.findall(r"\./audio/(unit_\d+\.mp3)", html_path.read_text(encoding="utf-8")))
        except OSError:
            referenced = set()
        if referenced:
            print(f"[i] Note: the module can use {len(referenced)} narration file(s) "
                  f"({', '.join(sorted(referenced)[:3])}…). Pass --audio-dir to bundle them, "
                  "otherwise the 45-second fallback simulator plays instead.")

    # 3. Assets directory
    if args.assets_dir:
        assets_dir = Path(args.assets_dir).resolve()
        if assets_dir.exists() and assets_dir.is_dir():
            for ast in sorted(assets_dir.rglob("*")):
                if ast.is_file():
                    rel_p = ast.relative_to(assets_dir)
                    arc_name = f"assets/{rel_p.as_posix()}"
                    files_to_zip.append((ast, arc_name))
                    files_in_manifest.append(arc_name)
            print(f"[*] Added assets from: {assets_dir}")

    # 4. Generate imsmanifest.xml content
    if args.version == "2004":
        manifest_xml = generate_manifest_scorm2004(package_id, title, passing_score, files_in_manifest)
    else:
        manifest_xml = generate_manifest_scorm12(package_id, title, passing_score, files_in_manifest)

    # 5. Build ZIP file
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        # Write imsmanifest.xml
        zf.writestr("imsmanifest.xml", manifest_xml.encode("utf-8"))
        print("    ✓ Created: imsmanifest.xml")

        # Write all files
        for src, arc in files_to_zip:
            zf.write(src, arc)
            print(f"    ✓ Bundled: {arc}")

    zip_size_kb = out_zip.stat().st_size / 1024
    print(f"\n✓ Successfully created SCORM package: {out_zip} ({zip_size_kb:.1f} KB)")
    print(f"  Standard: SCORM {args.version}")
    print(f"  Entry   : index.html")
    print(f"  Ready for LMS upload (Moodle, SAP SuccessFactors, Canvas, Blackboard, Totara).")


def main():
    parser = argparse.ArgumentParser(description="Package Modul PP module into LMS SCORM package")
    parser.add_argument("--html", required=True, help="Path to compiled single-file HTML module")
    parser.add_argument("--output", default=None, help="Output path for the SCORM .zip package")
    parser.add_argument("--content", default=None, help="Path to content.json for metadata")
    parser.add_argument("--version", choices=["1.2", "2004"], default="1.2", help="SCORM standard (default: 1.2)")
    parser.add_argument("--audio-dir", default=None, help="Directory containing audio mp3 files")
    parser.add_argument("--assets-dir", default=None, help="Directory containing logo and external images")
    parser.add_argument("--title", default=None, help="Override course title in manifest")
    parser.add_argument("--identifier", default=None, help="Override SCORM package identifier")
    args = parser.parse_args()

    package_scorm(args)


if __name__ == "__main__":
    main()
