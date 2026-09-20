// The Quiet policy for deciding whether mid-turn assistant text is substantive.

/** The minimum trimmed text length preserved from a mid-turn assistant message. */
export const QUIET_PRESERVE_MIN_CHARS = 240;

/** Whether mid-turn assistant text is substantive enough to remain visible. */
export function quietTextIsSubstantive(text: string): boolean {
  return text.includes("\n") || text.trim().length >= QUIET_PRESERVE_MIN_CHARS;
}
