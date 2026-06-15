const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
  const browser = await puppeteer.launch({ headless: "new", args: ['--no-sandbox'] });
  const page = await browser.newPage();
  
  page.on('console', msg => console.log(`[BROWSER]: ${msg.text()}`));

  try {
    console.log("Navigating to /new...");
    await page.goto('http://localhost:3000/new', { waitUntil: 'networkidle2' });
    
    console.log("Entering JD...");
    await page.waitForSelector('textarea', {timeout: 5000});
    await page.type('textarea', 'Software Engineer, Python, React, AWS');

    console.log("Uploading dummy resume...");
    fs.writeFileSync('dummy.pdf', 'dummy content for resume');
    const fileInput = await page.$('input[type="file"]');
    if (fileInput) {
        await fileInput.uploadFile('dummy.pdf');
    }

    console.log("Clicking Run Live Pipeline...");
    const buttons = await page.$$('button');
    let runBtn = null;
    for (const b of buttons) {
        const text = await page.evaluate(el => el.innerText, b);
        if (text.includes('Run Live Pipeline') || text.includes('Process')) {
            runBtn = b;
            break;
        }
    }
    
    if (runBtn) {
        await runBtn.click();
        console.log("Waiting for workspace to load...");
        await page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 30000 }).catch(e => console.log("Navigation timeout, proceeding anyway"));
    }

    console.log(`Current URL: ${page.url()}`);
    
    console.log("Checking buttons on the page...");
    const workspaceButtons = await page.$$('button');
    console.log(`Found ${workspaceButtons.length} buttons.`);
    
    for (let i = 0; i < workspaceButtons.length; i++) {
        const b = workspaceButtons[i];
        const text = await page.evaluate(el => el.innerText, b);
        const className = await page.evaluate(el => el.className, b);
        console.log(`Button [${i}]: "${text.replace(/\n/g, ' ')}" (Class: ${className})`);
    }

  } catch (e) {
    console.error(`Error during check: ${e.message}`);
  } finally {
    await browser.close();
  }
})();
