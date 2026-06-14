import asyncio
from playwright.async_api import async_playwright
import os
import json

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()

        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        
        jds = {
            "search": "Role: Search Engineer\nSkills: FAISS, Qdrant, Learning-to-Rank, Python\nExperience: Production ML infrastructure",
            "frontend": "Role: Frontend Engineer\nSkills: React, Next.js, TypeScript, Tailwind CSS\nExperience: 5+ years building web applications",
            "sales": "Role: Sales Manager\nSkills: B2B SaaS, quota attainment, CRM, forecasting\nExperience: 5+ years in enterprise software sales"
        }

        os.makedirs("screenshots", exist_ok=True)

        for name, text in jds.items():
            print(f"--- Processing {name} ---")
            
            # Go to new investigation
            await page.goto("http://localhost:3000/new")
            await page.wait_for_load_state("networkidle")
            
            # Screenshot Upload
            await page.screenshot(path=f"screenshots/1_{name}_upload.png")
            
            # Fill out JD
            await page.fill("textarea", text)
            
            # Click run
            await page.click("text=Run Live Pipeline")
            
            # Screenshot Processing
            await page.wait_for_timeout(1000)
            await page.screenshot(path=f"screenshots/2_{name}_processing.png")
            
            # Wait for workspace page (which means status=COMPLETED)
            print("Waiting for workspace redirect...")
            try:
                await page.wait_for_url("**/workspace?id=*", timeout=120000)
            except Exception as e:
                print(f"Failed to load workspace for {name}. Error: {e}")
                await page.screenshot(path=f"screenshots/ERROR_{name}_workspace.png")
                continue
                
            await page.wait_for_load_state("networkidle")
            
            # Wait for candidates to load on workspace
            await page.wait_for_timeout(2000)
            
            # Screenshot Workspace
            await page.screenshot(path=f"screenshots/3_{name}_workspace.png", full_page=True)
            
            # Click Clear Selection if needed
            # (First let's select a candidate, then clear it to verify)
            cards = await page.locator(".group.relative.border").all()
            if cards:
                await cards[0].click()
                await page.wait_for_timeout(1000)
                await page.screenshot(path=f"screenshots/4_{name}_candidate_details.png", full_page=True)
                
                # Check Clear Selection
                clear_btn = page.locator("text=Clear Selection")
                if await clear_btn.count() > 0:
                    await clear_btn.click()
                    await page.wait_for_timeout(1000)
                    await page.screenshot(path=f"screenshots/5_{name}_clear_selection.png", full_page=True)
                
            # Screenshot Reports
            await page.goto("http://localhost:3000/reports")
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(2000)
            await page.screenshot(path=f"screenshots/6_{name}_reports.png", full_page=True)
            
            print(f"Completed {name}")

        await browser.close()
        
        with open("screenshots/console_logs.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(console_logs))

if __name__ == "__main__":
    asyncio.run(run())
