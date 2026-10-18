# `/modul-pp` — DSH slash command for the modul-pp skill

A tiny [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) command plugin.
Typing **`/modul-pp <permintaan>`** in the DSH chat injects a user message that tells the agent to
load the `modul-pp` skill and run it end to end (build `content.json` → validate → build → verify).

> A skill on its own **cannot** define a slash command — DSH skills only contribute a `name` and a
> `description` to the agent's catalog. Slash commands are a separate plugin system
> (`@deepseek-ai/dsh-commands`). That is why this lives outside the skill folder, in its own package.

## What it does

```
/modul-pp Buat modul onboarding 12 slide dari dokumen SOP terlampir
```

→ registers a follow-up user message containing the request plus an explicit instruction to invoke
the `modul-pp` skill, then returns immediately. Attachments (PDF/DOCX/MD) sent with the command are
forwarded to the agent ahead of the text.

## Install

The command plugin must live where the DSH profile can resolve it, and must be listed in the
profile's patch layer.

**1. Copy the package into the profile's module resolution path**

```powershell
$profile = "$env:USERPROFILE\.dsh\profiles"
Copy-Item ".\dsh-command" "$profile\node_modules\dsh-command-modul-pp" -Recurse -Force
```

**2. Register it in the profile patch layer**

Add this entry to `$env:USERPROFILE\.dsh\profiles\desktop\cordis.patch.yml`:

```yaml
- id: command-modul-pp
  name: "dsh-command-modul-pp"
```

**3. Restart DSH**

The profile plugin tree is composed at startup, so the command appears only after a restart.
Then type `/` in the chat — `modul-pp` shows up in the command list.

## Uninstall

Remove the `command-modul-pp` entry from `cordis.patch.yml`, delete
`$env:USERPROFILE\.dsh\profiles\node_modules\dsh-command-modul-pp`, and restart.

## Notes

- `inject = ["commands"]` declares the capability this plugin needs; the DSH loader wires it in.
- The handler never runs the skill itself — it delegates by scheduling a normal user turn, so the
  work appears in the transcript exactly like a hand-typed request.
- `@deepseek-ai/dsh-llm` is imported for `createUserMessage`; it resolves from the profile's
  `node_modules`, which is why the package has no `dependencies` of its own.
