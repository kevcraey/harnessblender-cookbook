// Quiet: the hooks module of the `quiet` plugin.
//
// A conversation-only transcript presentation for Claude Code, ported from Firstmate's
// Calm mode (https://github.com/kunchenguid/firstmate, docs/calm.md). Claude Code loads
// this module through its early-access function-hooks surface, which is off by default
// and enabled with `CLAUDE_CODE_ENABLE_FUNCTION_HOOKS=1`; without that the module never
// loads and every drawing stays exactly as Claude Code draws it.
//
// This file is the only place the engine interface `$` is touched: the geometry lives in
// ../lib/quiet-working-ship-sprite.ts, the Raster packing in ../lib/quiet-ship-raster.ts,
// and every visibility decision in ../lib/quiet-presentation.ts, so the policy is
// testable under Node and the engine glue under `claude plugin test`. Nothing here
// rewrites a message: `ui.render` changes drawings and leaves the stored transcript,
// model context, and session storage alone.
//
// Presentation while Quiet is on: the stock working row (`Spinner`) becomes a two-row
// sailboat, repainted through `$.ui.blit` on the sprite's own tick; `ToolUse`,
// `ToolResult`, and `ToolGroup` rows draw as zero-height boxes; an `AssistantMessage`
// block recorded as a mid-turn working note draws as zero height. Quiet off returns
// every drawing to the engine. A toggle invalidates every hooked drawing, so rows
// already on screen redraw. The boat is painted in Claude Code's own theme colors: the
// family is read from the `theme` setting at load and re-read when a `config.set`
// changes it.
//
// Loading is lazy and cached within a session: a resumed transcript or a hot reload can
// draw restored rows before `session.start`, so every hook awaits that session's load of
// the preference and restored working notes rather than trusting a stale "off".
// Each `session.start` clears presentation classifications and reloads the new session.
import type { EngineInterface, Register, RenderElement, RenderInput } from "claude-code";
import {
  QUIET_WORKING_SHIP_TICK_MS,
  createQuietWorkingShipSprite,
} from "../lib/quiet-working-ship-sprite.ts";
import {
  QUIET_SHIP_RASTER_KEY,
  QUIET_SHIP_RASTER_PALETTES,
  quietShipPaletteFamily,
  quietShipRasterColumns,
  packQuietShipRasterCells,
  type QuietShipRasterPalette,
} from "../lib/quiet-ship-raster.ts";
import {
  quietPreferencePath,
  parseQuietPreference,
  classifyRestoredTranscript,
  serializeQuietPreference,
  stepTextIsWorkingNote,
  workingNoteKey,
} from "../lib/quiet-presentation.ts";

/** The slash command the plugin serves. */
const QUIET_COMMAND = "quiet";

// One module environment holds one Quiet state; a hot reload starts a fresh one.
let quiet = false;
let preferencePath: string | undefined;
let loading: Promise<void> | undefined;
let ticker: { cancel(): void } | undefined;
const workingNotes = new Set<string>();
const finalReplies = new Set<string>();
const sprite = createQuietWorkingShipSprite();
let palette: QuietShipRasterPalette = QUIET_SHIP_RASTER_PALETTES.light;
// Every Spinner site currently drawing the boat, by its requestId, with the mounted
// Raster size a blit must repeat exactly.
const sites = new Map<string, { columns: number; rows: number }>();

async function readPreference($: EngineInterface, path: string): Promise<string | undefined> {
  try {
    return await $.fs.read(path);
  } catch {
    return undefined;
  }
}

/** The `theme` setting's current value, or undefined when the menu cannot be read. */
async function readTheme($: EngineInterface): Promise<unknown> {
  try {
    return (await $.config.list()).find((row) => row.key === "theme")?.value;
  } catch {
    return undefined;
  }
}

async function load($: EngineInterface): Promise<void> {
  preferencePath = quietPreferencePath(await $.env.get("HOME"));
  quiet = preferencePath !== undefined && parseQuietPreference(await readPreference($, preferencePath));
  palette = QUIET_SHIP_RASTER_PALETTES[quietShipPaletteFamily(await readTheme($))];
  try {
    const restored = classifyRestoredTranscript(await $.session.messages());
    for (const note of restored.workingNotes) workingNotes.add(note);
    for (const reply of restored.finalReplies) finalReplies.add(reply);
  } catch {
    // A transcript that cannot be read leaves restored narration visible; nothing else changes.
  }
  if (ticker === undefined) {
    ticker = $.clock.every(QUIET_WORKING_SHIP_TICK_MS, () => {
      void repaintShip($);
    });
  }
  $.ui.invalidate("ui.render");
}

function ensureLoaded($: EngineInterface): Promise<void> {
  if (loading === undefined) loading = load($);
  return loading;
}

async function resetSession($: EngineInterface): Promise<void> {
  if (loading !== undefined) await loading.catch(() => undefined);
  quiet = false;
  preferencePath = undefined;
  loading = undefined;
  workingNotes.clear();
  finalReplies.clear();
  sites.clear();
  sprite.reset();
  palette = QUIET_SHIP_RASTER_PALETTES.light;
  await ensureLoaded($);
}

/** One scheduler tick: advance the sprite, then repaint every mounted boat in place. */
async function repaintShip($: EngineInterface): Promise<void> {
  if (!quiet || sites.size === 0) return;
  sprite.tick();
  for (const [requestId, site] of sites) {
    const packed = packQuietShipRasterCells(sprite.frame(site.columns), site.columns, palette);
    const result = await $.ui.blit({
      requestId,
      key: QUIET_SHIP_RASTER_KEY,
      cells: packed.cells,
      columns: site.columns,
      rows: site.rows,
    });
    // A denied blit means the site no longer shows this plugin's Raster (the turn
    // settled, or a resize redrew it); forget it until the next Spinner drawing.
    if (result.deny !== undefined && sites.get(requestId) === site) sites.delete(requestId);
  }
}

/** A zero-height drawing: the row contributes nothing to the transcript's layout. */
function hiddenRow($: EngineInterface, e: RenderInput): RenderElement {
  const { Box } = $.ui.resolve(e);
  return Box({ display: "none" });
}

export const register: Register = (on) => {
  on("session.start", async ($, e, next) => {
    await resetSession($);
    await $.command.register({
      name: QUIET_COMMAND,
      description: "Toggle the Quiet transcript presentation and working ship.",
    });
    return next(e);
  });

  on("command.run", { command: QUIET_COMMAND }, async ($, e, next) => {
    await ensureLoaded($);
    const active = !quiet;
    // Persist before changing live presentation, so a failed write leaves the current
    // choice unchanged rather than claiming persistence.
    try {
      if (preferencePath === undefined) throw new Error("no HOME to store the preference in");
      await $.fs.write(preferencePath, serializeQuietPreference(active));
    } catch (error) {
      const reason = error instanceof Error ? error.message : String(error);
      $.ui.toast(`Quiet unchanged: could not save ${preferencePath ?? "the preference"} (${reason})`);
      return {};
    }
    quiet = active;
    if (!quiet) sites.clear();
    $.ui.invalidate("ui.render");
    $.ui.toast(active ? "Quiet on" : "Quiet off");
    // No `text`: the toggle leaves no output row in the transcript.
    return {};
  });

  // Follow a theme change: the next drawing and every later blit use the new family.
  on("config.set", { key: "theme" }, async ($, e, next) => {
    const result = await next(e);
    if (result.deny === undefined) {
      const chosen = QUIET_SHIP_RASTER_PALETTES[quietShipPaletteFamily(result.value)];
      if (chosen !== palette) {
        palette = chosen;
        if (quiet) $.ui.invalidate("ui.render");
      }
    }
    return result;
  });

  // Record mid-turn narration as it streams: the text blocks of a model step that
  // stopped to call tools. Subagent steps never draw in the main transcript.
  on("turn.step", async function* ($, e, next) {
    const stream = next(e);
    const blocks = new Map<number, string>();
    for await (const chunk of stream) {
      if (chunk.kind === "text") blocks.set(chunk.index, (blocks.get(chunk.index) ?? "") + chunk.text);
      yield chunk;
    }
    const result = await stream.result;
    if (e.agentId === undefined) {
      let changed = false;
      for (const text of [...blocks.values(), result.answer]) {
        const key = workingNoteKey(text);
        if (key === "") continue;
        if (stepTextIsWorkingNote(result, text)) {
          if (finalReplies.has(key) || workingNotes.has(key)) continue;
          workingNotes.add(key);
          changed = true;
        } else {
          if (!finalReplies.has(key)) {
            finalReplies.add(key);
            changed = true;
          }
          if (workingNotes.delete(key)) changed = true;
        }
      }
      if (changed && quiet) $.ui.invalidate("ui.render");
    }
    return result;
  });

  on("ui.render", { component: "Spinner" }, async ($, e, next) => {
    await ensureLoaded($);
    if (!quiet || e.surface !== "terminal") {
      sites.delete(e.requestId);
      return next(e);
    }
    const columns = quietShipRasterColumns(e.viewport?.columns);
    const packed = packQuietShipRasterCells(sprite.frame(columns), columns, palette);
    sites.set(e.requestId, { columns, rows: packed.rows });
    const { Box, Raster } = $.ui.resolve(e);
    return Box({
      flexDirection: "column",
      children: Raster({ key: QUIET_SHIP_RASTER_KEY, columns, rows: packed.rows, cells: packed.cells }),
    });
  });

  on("ui.render", { component: "ToolUse" }, async ($, e, next) => {
    await ensureLoaded($);
    return quiet ? hiddenRow($, e) : next(e);
  });
  on("ui.render", { component: "ToolResult" }, async ($, e, next) => {
    await ensureLoaded($);
    return quiet ? hiddenRow($, e) : next(e);
  });
  on("ui.render", { component: "ToolGroup" }, async ($, e, next) => {
    await ensureLoaded($);
    return quiet ? hiddenRow($, e) : next(e);
  });

  on("ui.render", { component: "AssistantMessage" }, async ($, e, next) => {
    await ensureLoaded($);
    const key = workingNoteKey(e.props.text);
    return quiet && workingNotes.has(key) && !finalReplies.has(key) ? hiddenRow($, e) : next(e);
  });
};
