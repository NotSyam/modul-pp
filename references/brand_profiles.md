# Brand Profiles

The skill ships with **4 preset brand profiles** + a **custom** option for full inline control. At build time, `build_module.py` resolves the brand block from `content.json` and applies the brand's hex color tokens to the Tailwind config + CSS rules in the shell template.

## How brand resolution works

```python
final_brand = preset_defaults | inline_overrides | CLI_preset_override
```

1. Start with the **preset** (`brand.preset` in content.json, looked up in `assets/brand.profiles.json`).
2. Overlay any **inline fields** from `brand` block in content.json (everything except `preset`).
3. If `--brand-preset <NAME>` is passed on the CLI, that overrides `brand.preset` in content.json.

So inline fields override preset fields. CLI overrides the preset name.

## The 4 presets

### `ptpp` — PT PP (Persero) Tbk (DEFAULT)

The default preset, and the only one that reproduces the reference module's exact palette. `build_module.py` falls back to `ptpp` when `content.json` has no `brand` block. The original `upstream/index_tree_canvas.html` was built for this brand.

```json
{
  "orgName": "PT PP (Persero) Tbk",
  "orgDivision": "Human Capital Management & Quality Assurance",
  "signatory": "SVP - Operation Control & SCC",
  "certTitle": "Standard Operating Procedure",
  "certRegPrefix": "PP/HCM-QA/C1-050",
  "primary": "2B73BD",          // Primary Blue
  "primaryHover": "205c99",
  "secondary": "5A89B8",        // Steel Blue
  "accent": "38BDF8",           // Vivid Sky Blue (dark-mode accent)
  "iceBg": "F0F4F7",            // Soft Ice White
  "darkBg": "09111E",           // Deep Slate
  "darkSurface": "111C2E",
  "darkBorder": "1F2F4A",
  "darkSubtle": "16233B"
}
```

**When to use**: Indonesian SOE / construction / infrastructure modules. Also the mandatory choice whenever the module must be visually faithful to the reference design system.

---

### `corporate` — Generic Corporate Learning

Neutral corporate blue palette — note that `primary` is `0F4C81`, a **different blue** from the reference palette. Use only when the user explicitly wants a non-reference corporate identity.

```json
{
  "orgName": "Corporate Learning",
  "orgDivision": "Learning & Development",
  "signatory": "Director of Learning & Development",
  "certTitle": "Professional Development Module",
  "certRegPrefix": "CORP/LD",
  "primary": "0F4C81",          // Deep corporate blue
  "primaryHover": "0B3D66",
  "secondary": "4A7BA8",
  "accent": "38BDF8",
  "iceBg": "F4F7FA",
  "darkBg": "0B1426",
  "darkSurface": "13203A",
  "darkBorder": "1F2F4A",
  "darkSubtle": "1A2842"
}
```

**When to use**: Corporate training, internal L&D, professional development or generic SOP modules where the user has accepted a palette that departs from the reference UI.

---

### `education` — Academic / School

Forest green palette. Use for academic course modules, faculty resources, K-12 / higher-ed continuing education.

```json
{
  "orgName": "Learning Academy",
  "orgDivision": "Faculty of Continuing Education",
  "signatory": "Academic Director",
  "certTitle": "Course Completion",
  "certRegPrefix": "EDU/CCE",
  "primary": "2E7D32",          // Forest green
  "primaryHover": "1B5E20",
  "secondary": "6FA073",
  "accent": "A5D6A7",
  "iceBg": "F5F9F5",
  "darkBg": "0E1F0E",
  "darkSurface": "16291A",
  "darkBorder": "1F3A22",
  "darkSubtle": "1A2D1C"
}
```

**When to use**: Schools, universities, faculty/academic departments, K-12, MOOC-style courses.

---

### `tech-startup` — Engineering Playbook

Vibrant violet + pink accent. Use for tech startup onboarding, engineering playbooks, dev team training.

```json
{
  "orgName": "Startup Lab",
  "orgDivision": "Engineering Enablement",
  "signatory": "VP of Engineering",
  "certTitle": "Engineering Playbook Module",
  "certRegPrefix": "ENG/PLAY",
  "primary": "6D28D9",          // Violet
  "primaryHover": "5B21B6",
  "secondary": "A78BFA",
  "accent": "F472B6",           // Pink accent
  "iceBg": "F8F5FC",
  "darkBg": "150B22",
  "darkSurface": "1E1133",
  "darkBorder": "2D1B47",
  "darkSubtle": "1F1238"
}
```

**When to use**: Tech startups, dev teams, engineering onboarding, product playbook modules.

---

## Custom brand (full inline control)

If the user wants a brand that doesn't fit any preset, use `preset: "custom"` and define every field inline. To stay faithful to the reference design system, use the reference palette values:

```json
{
  "brand": {
    "preset": "custom",
    "orgName": "Acme Corp",
    "orgDivision": "People Operations",
    "signatory": "VP of People Ops",
    "certTitle": "Internal Training Module",
    "certRegPrefix": "ACME/PEOPS",
    "primary": "2B73BD",
    "primaryHover": "205c99",
    "secondary": "5A89B8",
    "accent": "38BDF8",
    "iceBg": "F0F4F7",
    "darkBg": "09111E",
    "darkSurface": "111C2E",
    "darkBorder": "1F2F4A",
    "darkSubtle": "16233B"
  }
}
```

**Rules for custom brand**:
- All hex colors are 6 digits WITHOUT the `#` prefix (the build script adds it)
- All fields are required when `preset: "custom"` (the preset is empty, nothing to fall back to)
- The hex codes appear in BOTH the Tailwind config block AND in the `<style>` block CSS rules — the build script replaces every occurrence in the template
- **No brown/beige/tan accents.** A `custom` brand only satisfies the UI parity requirement when it reuses the reference palette values above; any other palette is a deliberate departure the user must accept.

## How colors get applied

The shell template (`assets/shell.template.html`) was built from a PT PP original, so it contains hardcoded PT PP hex values everywhere:
- Tailwind config (`tailwind.config.theme.extend.colors.brand.*`)
- CSS custom properties (`--progress` gradient on `#seekBar`)
- Light theme override rules (`body:not(.dark) #topHeader { background-color: #FFFFFF }`)
- Shadow / ring color RGBA references (`rgba(43, 115, 189, 0.6)` etc.)

The build script's `apply_color_tokens()` function does a simple string replace of every PT PP hex code with the brand's hex code. This works for the Tailwind config + CSS hex references, but **does NOT touch RGBA references** (`rgba(43, 115, 189, 0.6)` is preserved). This is intentional — the shadow / ring color tints derived from PT PP's primary blue remain subtle, and changing them per-brand would require converting hex → RGB + applying alpha per-occurrence.

If you want to also override the RGBA references, edit the brand profile (add inline fields `primaryRgb` etc.) and extend `apply_color_tokens()` in `build_module.py` to handle those. For most use cases, the simple hex replacement is enough — the visual identity comes through the Tailwind colors and CSS background fills.

## Adding a new preset

To add a new preset (e.g., `banking`, `healthcare`):

1. Edit `assets/brand.profiles.json` and add a new key under `profiles` with all required fields.
2. Update `assets/content.schema.json`'s `brand.preset` enum to include the new name.
3. Update this doc (`references/brand_profiles.md`) with the new preset's hex palette + when to use.
4. Update `SKILL.md`'s trigger phrase list if the new preset warrants new trigger keywords.

Example addition to `brand.profiles.json`:
```json
"banking": {
  "orgName": "Bank Learning Center",
  "orgDivision": "Compliance & Risk Management",
  "signatory": "Chief Compliance Officer",
  "certTitle": "Compliance Training Module",
  "certRegPrefix": "BANK/CRM",
  "primary": "1E3A8A",
  "primaryHover": "1E40AF",
  "secondary": "3B82F6",
  "accent": "93C5FD",
  "iceBg": "EFF6FF",
  "darkBg": "0F172A",
  "darkSurface": "1E293B",
  "darkBorder": "334155",
  "darkSubtle": "1E293B"
}
```

## Picking a preset — quick guide

**Default: `ptpp`** — the only preset that carries the reference module's exact palette (`primary 2B73BD`, `primaryHover 205c99`, `secondary 5A89B8`, `accent 38BDF8`, `iceBg F0F4F7`, `darkBg 09111E`, `darkSurface 111C2E`, `darkBorder 1F2F4A`, `darkSubtle 16233B`).

Choosing `corporate`, `education` or `tech-startup` deliberately overrides the palette and therefore **departs from the reference UI**; only `ptpp` (or `custom` with those exact hex values) satisfies the UI parity requirement.

| User context | Pick |
|--------------|------|
| Default / must match the reference UI | `ptpp` |
| Indonesian SOE / construction | `ptpp` |
| Generic corporate training (accepts palette drift) | `corporate` |
| School / academic / K-12 / higher-ed | `education` |
| Tech startup / engineering team | `tech-startup` |
| Specific brand identity needed | `custom` (define inline) |
| User has their own brand guidelines | `custom` + ask them for hex codes |

If unsure, ask the user: "Which brand preset fits best — ptpp (default, matches the reference design), corporate, education, tech-startup, or custom (you provide hex colors)?" Mention that any non-`ptpp` choice changes the visual identity from the reference module.
