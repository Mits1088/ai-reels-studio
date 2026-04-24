/**
 * Capture HTML templates as PNG screenshots using Playwright.
 * Usage: node lib/capture/capture-templates.js
 */

const { chromium } = require("playwright");
const path = require("path");
const fs = require("fs");

const ROOT = path.join(__dirname, "..", "..");
const TEMPLATES_DIR = path.join(ROOT, "lib", "capture", "templates");
const OUT_DIR = path.join(ROOT, "remotion", "public");

const captures = [
  {
    template: "claude-agentic-task.html",
    out: "claude-agentic-task.png",
    width: 540,
    height: 960,
    waitFor: 1200,
  },
  {
    template: "claude-code-terminal.html",
    out: "claude-code-terminal.png",
    width: 540,
    height: 960,
    waitFor: 800,
  },
];

(async () => {
  const browser = await chromium.launch();

  for (const c of captures) {
    const templatePath = path.join(TEMPLATES_DIR, c.template);
    const outPath = path.join(OUT_DIR, c.out);

    console.log(`Capturing: ${c.template} → ${c.out}`);

    const page = await browser.newPage();
    await page.setViewportSize({ width: c.width, height: c.height });

    const fileUrl = `file:///${templatePath.replace(/\\/g, "/")}`;
    await page.goto(fileUrl, { waitUntil: "networkidle" });

    // Extra wait for fonts / animations to settle
    await page.waitForTimeout(c.waitFor);

    await page.screenshot({ path: outPath, fullPage: false });
    await page.close();

    const stat = fs.statSync(outPath);
    console.log(`  ✓ Saved ${outPath} (${Math.round(stat.size / 1024)}KB)`);
  }

  await browser.close();
  console.log("Done.");
})();
