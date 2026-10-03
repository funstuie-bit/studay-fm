// Capture only public pages in a disposable browser. Never use an owner profile.
const { chromium } = require(process.env.STUDAY_PLAYWRIGHT_MODULE || 'playwright');
const path = require('node:path');

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: process.env.STUDAY_BROWSER_EXECUTABLE || '/Applications/Chromium.app/Contents/MacOS/Chromium' });
  const pages = [
    ['home', 'hero.png', 1440, 1100],
    ['home', 'receiver-mobile.png', 390, 844],
    ['presenters', 'receiver-presenters.png', 1440, 1100],
    ['diary', 'receiver-diary.png', 1440, 1100],
  ];
  try {
    for (const [route, filename, width, height] of pages) {
      const context = await browser.newContext({ viewport: { width, height }, timezoneId: 'America/Los_Angeles', reducedMotion: 'reduce' });
      const page = await context.newPage();
      await page.goto(`https://studayfm.com/#${route}`, { waitUntil: 'domcontentloaded' });
      await page.locator('img:visible').first().waitFor({ state: 'visible' });
      await page.waitForTimeout(2500);
      await page.locator('img:visible').evaluateAll(images => Promise.race([
        Promise.all(images.filter(image => image.getBoundingClientRect().top < innerHeight).map(image => image.decode().catch(() => {}))),
        new Promise(resolve => setTimeout(resolve, 10000)),
      ]));
      await page.screenshot({ path: path.join(__dirname, '..', 'docs', 'images', filename) });
      console.log(`${filename}: ${await page.title()}; overflow=${await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)}`);
      await context.close();
    }
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
