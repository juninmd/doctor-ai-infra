from playwright.sync_api import sync_playwright
import os

def verify_dashboard():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto("http://localhost:5174")

            # Expect the title
            page.wait_for_selector("text=Infra Manager 2026", timeout=10000)
            print("Title found.")

            # Check for Dashboard elements
            # Look for the GlassCard header we added
            page.wait_for_selector("text=LIVE INFRASTRUCTURE STATUS", timeout=10000)
            print("Dashboard found.")

            # Check for grid layout
            # We can't easily check CSS grid via text, but if the element is visible, good.

        except Exception as e:
            print(f"Verification failed: {e}")
        finally:
            # Ensure dir exists
            if not os.path.exists("verification"):
                os.makedirs("verification")
            page.screenshot(path="verification/dashboard_screenshot.png")
            browser.close()

if __name__ == "__main__":
    verify_dashboard()
