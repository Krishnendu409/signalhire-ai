const puppeteer = require('puppeteer');
const fs = require('fs');

const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

async function run() {
    console.log("Starting browser...");
    const browser = await puppeteer.launch({ headless: "new" });
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 800 });

    if (!fs.existsSync('screenshots')) {
        fs.mkdirSync('screenshots');
    }

    // 1. Landing Page Evidence
    console.log("Capturing Landing Page...");
    await page.goto("http://localhost:3000/", { waitUntil: 'networkidle0' });
    await page.screenshot({ path: `screenshots/0_landing_page.png`, fullPage: true });

    // 2. Upload Button & Job Creation
    console.log("Testing Upload and Job Creation...");
    await page.goto("http://localhost:3000/new", { waitUntil: 'networkidle0' });
    const jdText = "Role: Search Engineer\nSkills: Python, React\nExperience: 5+ years";
    await page.type("textarea", jdText);
    await page.click('button'); // Start Investigation
    
    // 3. Workspace Loading
    console.log("Waiting for Workspace...");
    await page.waitForFunction("window.location.href.includes('/workspace')", { timeout: 60000 });
    await delay(3000); // Wait for data to populate
    await page.screenshot({ path: `screenshots/1_workspace.png`, fullPage: true });

    // 4. Reports Page
    console.log("Testing Reports Page...");
    await page.goto("http://localhost:3000/reports", { waitUntil: 'networkidle0' });
    await delay(2000);
    await page.screenshot({ path: `screenshots/2_reports.png`, fullPage: true });

    console.log("Evidence collection complete!");
    await browser.close();
}

run().catch(console.error);
