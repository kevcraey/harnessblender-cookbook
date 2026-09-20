#!/usr/bin/env node
// Meet wat afwerken.py niet kan zien: geometrie.
//
//     node scripts/controleer.js <presentatie.html> [--json] [--viewport 1280x720 …]
//
// Opent het bestand in headless Chrome via het DevTools-protocol en meet per
// slide of er inhoud buiten het canvas valt, en per figuur of elk label binnen
// zijn box en binnen de SVG blijft. Geen npm-dependencies: Node's ingebouwde
// fetch en WebSocket praten rechtstreeks met Chrome.
//
// Standaard drie vensters: 1280x720 (laptop), 1920x1080 (beamer) en 1440x900
// (breed venster, lage slide). Een slide die bij één maat past kan bij een
// andere wel overlopen: de tekst schaalt met de breedte, de hoogte niet.
//
// Exit 0 = niets gevonden. Exit 1 = bevindingen. Exit 2 = kon niet meten.

const { spawn } = require("node:child_process");
const { mkdtempSync, rmSync, existsSync } = require("node:fs");
const { tmpdir } = require("node:os");
const { join, resolve } = require("node:path");

const POORT = 19222; // hoog en projectuniek; 9222 botst met alles
const VENSTERS = ["1280x720", "1920x1080", "1440x900"];
const CHROME = [
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/Applications/Chromium.app/Contents/MacOS/Chromium",
  "/usr/bin/google-chrome",
  "/usr/bin/chromium",
].find(existsSync);

// Draait in de pagina. Alles via getBoundingClientRect: dat is na transform,
// dus een gedraaid label telt als wat je ziet, niet als wat er in de bron staat.
const METING = `(async () => {
  await document.fonts.ready;
  await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  const bevindingen = [];
  const slides = [...document.querySelectorAll('.slide')];

  slides.forEach((slide, i) => {
    const nr = i + 1;
    const canvas = slide.querySelector('.canvas');
    if (!canvas) return;
    const over = Math.round(canvas.scrollHeight - canvas.clientHeight);
    const overBreed = Math.round(canvas.scrollWidth - canvas.clientWidth);
    if (over > 1) bevindingen.push({ slide: nr, soort: 'overflow', detail: over + 'px inhoud valt onder de slide weg' });
    if (overBreed > 1) bevindingen.push({ slide: nr, soort: 'overflow', detail: overBreed + 'px inhoud valt rechts weg' });

    canvas.querySelectorAll('svg.fig').forEach(svg => {
      const svgR = svg.getBoundingClientRect();
      // Zwart zit niet in het Flux-palet: dat betekent een class die nergens
      // gedefinieerd is, meestal een figuur in een deck uit een oudere template.
      svg.querySelectorAll('rect, path, text').forEach(el => {
        const f = getComputedStyle(el).fill;
        if (f === 'rgb(0, 0, 0)') {
          bevindingen.push({ slide: nr, soort: 'ongestijld', detail: '<' + el.tagName + ' class="' + el.getAttribute('class') + '"> valt terug op zwart' });
        }
      });
      const boxen = [...svg.querySelectorAll('rect')].map(r => r.getBoundingClientRect());
      svg.querySelectorAll('text').forEach(t => {
        const b = t.getBoundingClientRect();
        const tekst = (t.textContent || '').trim().slice(0, 32);
        if (b.width === 0) return;
        if (b.left < svgR.left - 1 || b.right > svgR.right + 1 || b.top < svgR.top - 1 || b.bottom > svgR.bottom + 1) {
          bevindingen.push({ slide: nr, soort: 'buiten-figuur', detail: '"' + tekst + '" valt buiten de SVG' });
          return;
        }
        const mx = (b.left + b.right) / 2, my = (b.top + b.bottom) / 2;
        const host = boxen.find(r => mx >= r.left && mx <= r.right && my >= r.top && my <= r.bottom);
        if (!host) return; // vrijstaand label, niets om tegen te toetsen
        const marge = 4;
        const uit = Math.round(Math.max(b.right - (host.right - marge), (host.left + marge) - b.left));
        if (uit > 0) bevindingen.push({ slide: nr, soort: 'label-te-breed', detail: '"' + tekst + '" steekt ' + uit + 'px buiten zijn box' });
      });
    });
  });

  return JSON.stringify({
    slides: slides.length,
    figuren: document.querySelectorAll('svg.fig').length,
    viewport: innerWidth + 'x' + innerHeight,
    bevindingen
  });
})()`;

async function wacht(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function doelZoeken() {
  for (let poging = 0; poging < 50; poging++) {
    try {
      const res = await fetch(`http://127.0.0.1:${POORT}/json/list`);
      const targets = await res.json();
      const page = targets.find((t) => t.type === "page" && t.url.startsWith("file://"));
      if (page && page.webSocketDebuggerUrl) return page;
    } catch {
      // Chrome staat nog niet klaar
    }
    await wacht(100);
  }
  return null;
}

async function meet(ws) {
  return new Promise((klaar, mis) => {
    const sock = new WebSocket(ws);
    const tijd = setTimeout(() => mis(new Error("geen antwoord van Chrome")), 20000);
    sock.addEventListener("open", () => {
      sock.send(JSON.stringify({
        id: 1,
        method: "Runtime.evaluate",
        params: { expression: METING, awaitPromise: true, returnByValue: true },
      }));
    });
    sock.addEventListener("message", (ev) => {
      const bericht = JSON.parse(ev.data);
      if (bericht.id !== 1) return;
      clearTimeout(tijd);
      sock.close();
      const r = bericht.result;
      if (r.exceptionDetails) return mis(new Error(r.exceptionDetails.text));
      klaar(JSON.parse(r.result.value));
    });
    sock.addEventListener("error", () => { clearTimeout(tijd); mis(new Error("websocket-fout")); });
  });
}

function vensters(argv) {
  const uit = [];
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--viewport" && argv[i + 1]) uit.push(argv[i + 1]);
  }
  return uit.length ? uit : VENSTERS;
}

async function meetVenster(bestand, venster) {
  const [b, h] = venster.split("x");
  const profiel = mkdtempSync(join(tmpdir(), "presentatie-controle-"));
  const chrome = spawn(CHROME, [
    "--headless=new",
    "--disable-gpu",
    "--hide-scrollbars",
    "--no-first-run",
    "--no-default-browser-check",
    `--window-size=${b},${h}`,
    `--remote-debugging-port=${POORT}`,
    `--user-data-dir=${profiel}`,
    "file://" + resolve(bestand),
  ], { stdio: "ignore" });
  try {
    const doel = await doelZoeken();
    if (!doel) throw new Error("Chrome opende de pagina niet");
    return await meet(doel.webSocketDebuggerUrl);
  } finally {
    chrome.kill();
    try { rmSync(profiel, { recursive: true, force: true }); } catch {}
  }
}

(async () => {
  const bestand = process.argv[2];
  const alsJson = process.argv.includes("--json");
  if (!bestand || !existsSync(bestand)) {
    console.error("gebruik: node scripts/controleer.js <presentatie.html> [--json]");
    process.exit(2);
  }
  if (!CHROME) {
    console.error("FOUT: geen Chrome of Chromium gevonden.");
    process.exit(2);
  }

  const metingen = [];
  let fouten = 0;
  try {
    for (const venster of vensters(process.argv)) {
      const r = await meetVenster(bestand, venster);
      metingen.push({ venster, ...r });
      fouten += r.bevindingen.length;
    }
  } catch (e) {
    console.error("FOUT: " + e.message);
    process.exit(2);
  }

  if (alsJson) {
    console.log(JSON.stringify({ bestand, metingen }, null, 2));
  } else {
    console.log(bestand);
    console.log(`  slides:   ${metingen[0].slides}`);
    console.log(`  figuren:  ${metingen[0].figuren}`);
    for (const m of metingen) {
      if (m.bevindingen.length === 0) {
        console.log(`  ${m.venster} (viewport ${m.viewport}): in orde`);
      } else {
        console.log(`  ${m.venster} (viewport ${m.viewport}):`);
        for (const b of m.bevindingen) console.log(`    slide ${b.slide} — ${b.soort}: ${b.detail}`);
      }
    }
  }
  process.exit(fouten === 0 ? 0 : 1);
})();
