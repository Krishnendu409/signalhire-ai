const puppeteer = require('puppeteer');
const fs = require('fs');

const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

async function run() {
    const browser = await puppeteer.launch({ headless: "new" });
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 800 });

    const consoleLogs = [];
    page.on('console', msg => consoleLogs.push(`[${msg.type()}] ${msg.text()}`));
    page.on('pageerror', err => consoleLogs.push(`[error] ${err.toString()}`));

    const jds = {
        "search": "Role: Search Engineer\nSkills: FAISS, Qdrant, Learning-to-Rank, Python\nExperience: Production ML infrastructure",
        "frontend": "Role: Frontend Engineer\nSkills: React, Next.js, TypeScript, Tailwind CSS\nExperience: 5+ years building web applications",
        "sales": "Role: Sales Manager\nSkills: B2B SaaS, quota attainment, CRM, forecasting\nExperience: 5+ years in enterprise software sales"
    };

    if (!fs.existsSync('screenshots')) {
        fs.mkdirSync('screenshots');
    }

    for (const [name, text] of Object.entries(jds)) {
        console.log(`--- Processing ${name} ---`);
        
        await page.goto("http://localhost:3000/new", { waitUntil: 'networkidle0' });
        await page.screenshot({ path: `screenshots/1_${name}_upload.png` });
        
        await page.type("textarea", text);
        
        // Wait for button to be available
        await page.waitForSelector('button');
        await page.click('button');
        
        await delay(1000);
        await page.screenshot({ path: `screenshots/2_${name}_processing.png` });
        
        console.log(`Waiting for workspace redirect for ${name}...`);
        try {
            await page.waitForFunction("window.location.href.includes('/workspace')", { timeout: 300000 });
        } catch (e) {
            console.log(`Failed to load workspace for ${name}. Error: ${e}`);
            await page.screenshot({ path: `screenshots/ERROR_${name}_workspace.png` });
            continue;
        }
        
        await delay(2000);
        await page.screenshot({ path: `screenshots/3_${name}_workspace.png`, fullPage: true });
        
        // Test Candidate cards exist
        const cards = await page.$$('.group.relative.border');
        if (cards.length > 0) {
            await cards[0].click();
            await delay(1000);
            await page.screenshot({ path: `screenshots/4_${name}_candidate_details.png`, fullPage: true });
            
            const clearBtn = await page.$x("//button[contains(text(), 'Clear Selection')]");
            if (clearBtn.length > 0) {
                await clearBtn[0].click();
                await delay(1000);
                await page.screenshot({ path: `screenshots/5_${name}_clear_selection.png`, fullPage: true });
            }
        }
        
        await page.goto("http://localhost:3000/reports", { waitUntil: 'networkidle0' });
        await delay(2000);
        await page.screenshot({ path: `screenshots/6_${name}_reports.png`, fullPage: true });
        
        console.log(`Completed ${name}`);
    }

    await browser.close();
    fs.writeFileSync('screenshots/console_logs.txt', consoleLogs.join('\n'));
}

run().catch(console.error);
