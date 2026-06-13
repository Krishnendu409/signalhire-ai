const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
  console.log("Launching browser...");
  const browser = await puppeteer.launch({ headless: "new", args: ['--no-sandbox'] });
  const page = await browser.newPage();
  
  const logs = [];
  const network = [];

  page.on('console', msg => logs.push(`[CONSOLE] ${msg.type().toUpperCase()}: ${msg.text()}`));
  page.on('request', request => network.push(`[REQ] ${request.method()} ${request.url()}`));
  page.on('response', response => network.push(`[RES] ${response.status()} ${response.url()}`));

  try {
    console.log("Navigating to /new...");
    await page.goto('http://localhost:3000/new', { waitUntil: 'networkidle2' });
    
    console.log("Filling JD text...");
    await page.waitForSelector('textarea');
    await page.type('textarea', '\nAdded explicit need for Pinecone and Vector DBs.');

    console.log("Clicking Run Live Pipeline...");
    // Find the button with "Run Live Pipeline"
    const [button] = await page.$x("//button[contains(., 'Run Live Pipeline')]");
    if (button) {
      await button.click();
    } else {
      throw new Error("Could not find Run Live Pipeline button");
    }

    console.log("Waiting for navigation to workspace...");
    await page.waitForNavigation({ timeout: 60000, waitUntil: 'networkidle2' });
    console.log(`Current URL: ${page.url()}`);

    console.log("Waiting for candidates to load...");
    await page.waitForSelector('h2', { timeout: 10000 });
    
    const candidateTitles = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('h2')).map(h => h.innerText);
    });
    console.log(`Found candidates: ${candidateTitles.slice(0, 5).join(', ')}...`);

    console.log("Taking screenshot...");
    await page.screenshot({ path: 'workspace_e2e.png' });

    console.log("E2E Test Passed Successfully.");
  } catch (e) {
    console.error(`E2E Test Failed: ${e.message}`);
  } finally {
    fs.writeFileSync('e2e_logs.txt', logs.join('\n') + '\n\n' + network.join('\n'));
    await browser.close();
  }
})();
