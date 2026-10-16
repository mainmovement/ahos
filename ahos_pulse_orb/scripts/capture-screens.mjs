import { mkdir } from 'node:fs/promises';
import { chromium } from 'playwright';

const baseURL = process.env.PULSE_ORB_URL ?? 'http://127.0.0.1:3000/orb-demo';
const out = new URL('../docs/screens/', import.meta.url);
await mkdir(out, { recursive: true });
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1 });
  await page.goto(baseURL, { waitUntil: 'networkidle' });
  await page.waitForSelector('[data-particle-texture]');
  await page.waitForTimeout(1200);

  const counter = await page.evaluate(() => (window).__pulseOrbRendererCreations ?? 0);
  await page.getByRole('button', { name: 'همه پاک' }).click();
  await page.waitForTimeout(800);
  await page.screenshot({ path: new URL('calm-1600x900.png', out).pathname, fullPage: true });

  // Fifty distinct prop updates; the WebGL renderer/GPGPU scene must stay mounted.
  await page.getByRole('button', { name: '50 prop updates (test)' }).click();
  await page.getByText('50 prop updates complete').waitFor();
  const afterChurn = await page.evaluate(() => (window).__pulseOrbRendererCreations ?? 0);
  if (counter !== afterChurn) throw new Error(`Renderer recreated: before=${counter}, after=${afterChurn}`);

  await page.getByRole('button', { name: 'انفجار رد دروازه' }).click();
  await page.waitForTimeout(800);
  await page.screenshot({ path: new URL('breach-1600x900.png', out).pathname, fullPage: true });

  await page.getByRole('button', { name: /Morph:/ }).click();
  await page.waitForTimeout(2500);
  await page.screenshot({ path: new URL('map-1600x900.png', out).pathname, fullPage: true });
  console.log(`Screenshots saved in docs/screens. Texture=${await page.locator('[data-particle-texture]').getAttribute('data-particle-texture')}; renderer creations=${afterChurn}`);
} finally {
  await browser.close();
}
