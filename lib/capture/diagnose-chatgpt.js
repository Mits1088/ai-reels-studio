/**
 * Quick diagnostic — opens ChatGPT and screenshots what we see,
 * lists all input elements found on the page.
 */
const { chromium } = require("playwright");
const path = require("path");
const fs = require("fs");

const CHROME_USER_DATA = process.env.CHROME_USER_DATA ||
  path.join(process.env.USERPROFILE || "C:/Users/no_1_", "AppData/Local/Google/Chrome/User Data");

(async () => {
  console.log("Launching Chrome with profile:", CHROME_USER_DATA);

  const context = await chromium.launchPersistentContext(CHROME_USER_DATA, {
    channel: "chrome",
    headless: false,
    viewport: { width: 540, height: 960 },
    args: ["--no-sandbox"],
  });

  const page = await context.newPage();

  console.log("Navigating to chatgpt.com...");
  await page.goto("https://chatgpt.com/", { timeout: 30000, waitUntil: "domcontentloaded" });
  await page.waitForTimeout(3000);

  const url = page.url();
  console.log("Current URL:", url);

  // Screenshot what we see
  const shotPath = path.join("D:/Reel generation/projects/chatgpt-secret-codes/screenshots", "diag-chatgpt.png");
  fs.mkdirSync(path.dirname(shotPath), { recursive: true });
  await page.screenshot({ path: shotPath, fullPage: false });
  console.log("Screenshot saved:", shotPath);

  // List all input/textarea elements
  const inputs = await page.evaluate(() => {
    return Array.from(document.querySelectorAll("textarea, input, [contenteditable]"))
      .map(el => ({
        tag: el.tagName,
        id: el.id,
        placeholder: el.getAttribute("placeholder"),
        testid: el.getAttribute("data-testid"),
        visible: el.offsetParent !== null,
      }));
  });
  console.log("\nInput elements found:", JSON.stringify(inputs, null, 2));

  // Check page title and body text snippet
  const title = await page.title();
  const bodySnippet = await page.locator("body").textContent().then(t => t.slice(0, 300)).catch(() => "");
  console.log("\nPage title:", title);
  console.log("Body snippet:", bodySnippet);

  await context.close();
  console.log("\nDone.");
})();
