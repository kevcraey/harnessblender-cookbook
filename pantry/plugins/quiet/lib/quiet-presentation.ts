// Quiet presentation policy, kept free of the engine.
//
// This module owns the decisions ../hooks/register.ts applies through `$`: where the
// Quiet preference lives and how its value reads, and which assistant text is a
// mid-turn working note rather than a genuine reply. Genuine user prompts, genuine
// agent responses, and the working presentation stay visible; tool rows, tool groups,
// and classified working notes hide. Everything here is pure so tests run it under Node.
//
// Ported from Firstmate's Calm mode (https://github.com/kunchenguid/firstmate).
import {
  QUIET_PRESERVE_MIN_CHARS,
  quietTextIsSubstantive,
} from "./quiet-preservation.ts";

export { QUIET_PRESERVE_MIN_CHARS } from "./quiet-preservation.ts";

/** The preference file, one per user home: `~/.claude/quiet`. */
export function quietPreferencePath(home: string | undefined): string | undefined {
  const trimmed = home?.replace(/[\\/]+$/, "");
  return trimmed ? `${trimmed}/.claude/quiet` : undefined;
}

/** Whether a stored preference reads as Quiet on; absent or unrecognized reads as off. */
export function parseQuietPreference(stored: string | undefined): boolean {
  return stored !== undefined && stored.trim() === "on";
}

/** The exact file content written for a choice. */
export function serializeQuietPreference(active: boolean): string {
  return active ? "on\n" : "off\n";
}

/** The shape of one `turn.step` result this policy reads. */
export type QuietStepOutcome = {
  readonly stopReason: string | null;
  readonly toolUses: readonly unknown[];
};

/**
 * Whether text from a model step is a mid-turn working note: the model did not end
 * its response there, because it stopped to call tools, or ran out of tokens while
 * calling them. Short single-line narration stays a note; substantive text is a final
 * reply even when the step also called tools.
 */
export function stepTextIsWorkingNote(step: QuietStepOutcome, text: string): boolean {
  const midTurn =
    step.stopReason === "tool_use" ||
    (step.stopReason === "max_tokens" && step.toolUses.length > 0);
  return midTurn && !quietTextIsSubstantive(text);
}

/** A trimmed text key that retains whether the raw row contained a newline. */
export function workingNoteKey(text: string): string {
  const trimmedText = text.trim();
  if (trimmedText === "") return "";
  return text.includes("\n") ? `${trimmedText}\n` : trimmedText;
}

/** The shape of one `$.session.messages()` row this policy reads. */
export type QuietSessionRow = {
  readonly role: "user" | "assistant";
  readonly text: string;
  readonly toolUses: readonly unknown[];
};

/**
 * The structurally identified working notes and final replies in a restored transcript.
 * The stored transcript keeps each content block as its own row, so assistant text is a
 * working note when its own row called tools, or when a tool-calling assistant row
 * follows it before the next user row. Substantive text in either position is preserved
 * as a final reply, matching the live classifier.
 */
export function classifyRestoredTranscript(rows: readonly QuietSessionRow[]): {
  workingNotes: string[];
  finalReplies: string[];
} {
  const notes = new Set<string>();
  const finalReplies = new Set<string>();
  for (let index = 0; index < rows.length; index += 1) {
    const row = rows[index]!;
    if (row.role !== "assistant") continue;
    const key = workingNoteKey(row.text);
    if (key === "") continue;
    let followedByToolCall = row.toolUses.length > 0;
    for (let later = index + 1; later < rows.length && rows[later]!.role === "assistant"; later += 1) {
      if (rows[later]!.toolUses.length > 0) {
        followedByToolCall = true;
        break;
      }
    }
    if (followedByToolCall && quietTextIsSubstantive(row.text)) finalReplies.add(key);
    else if (followedByToolCall) notes.add(key);
    else finalReplies.add(key);
  }
  for (const key of finalReplies) notes.delete(key);
  return { workingNotes: [...notes], finalReplies: [...finalReplies] };
}
