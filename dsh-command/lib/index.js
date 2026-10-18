/**
 * dsh-command-modul-pp — slash command `/modul-pp` for the DeepSeek Harness.
 *
 * Typing `/modul-pp <request>` injects a user message that instructs the agent to
 * load the `modul-pp` skill and follow it end to end (build content.json →
 * validate → build → run the verification gate).
 *
 * Registered through the DSH command adapter, mirroring the shape of
 * @deepseek-ai/dsh-command-goal.
 *
 * @module dsh-command-modul-pp
 */
import { createUserMessage } from "@deepseek-ai/dsh-llm";

const name = "command-modul-pp";
const inject = ["commands"];

const SKILL_NAME = "modul-pp";
const USAGE = "Usage: /modul-pp <topik atau deskripsi modul>";

/** Prompt handed to the agent, which makes the skill invocation explicit. */
function buildPrompt(request) {
	return [
		`Gunakan skill \`${SKILL_NAME}\` untuk tugas ini.`,
		"",
		"Langkah wajib:",
		`1. Panggil tool \`skill\` dengan name \`${SKILL_NAME}\`, lalu ikuti seluruh instruksinya.`,
		"2. Bangun content.json sesuai assets/content.schema.json (units[] dan slides[] harus sama panjang).",
		"3. Jalankan ketiga gate sebelum melaporkan selesai:",
		"   - scripts/validate_content.py <content.json>",
		"   - scripts/build_module.py --content <content.json> --output <out.html> --validate",
		"   - tools/verify_module.py <out.html>",
		"",
		"Permintaan pengguna:",
		request,
	].join("\n");
}

/** Register `/modul-pp` on every composed command adapter. */
function apply(ctx) {
	ctx.commands.register({
		name: SKILL_NAME,
		description: "bangun modul e-learning interaktif dari dokumen, SOP, atau outline",
		input: {
			hint: "<topik atau deskripsi modul>",
			attachments: true,
		},
		handler: (invocation) => {
			const request = invocation.rawInput.trim();
			const attachments = invocation.attachments ?? [];

			if (request.length === 0 && attachments.length === 0) {
				return { kind: "error", text: `Deskripsi modul masih kosong. ${USAGE}` };
			}

			invocation.agent.followup(
				createUserMessage({
					content: [
						...attachments,
						{ type: "text", text: buildPrompt(request.length > 0 ? request : "(lihat dokumen terlampir)") },
					],
					source: { kind: "user" },
				}),
			);

			return {
				kind: "success",
				text: `Menjalankan skill ${SKILL_NAME}${attachments.length > 0 ? ` dengan ${attachments.length} lampiran` : ""}…`,
			};
		},
	});
}

export { apply, inject, name };
