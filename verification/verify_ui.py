from playwright.sync_api import sync_playwright
import time

def verify_chat_ui():
    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            print("Navigating to http://localhost:3000")
            page.goto("http://localhost:3000")

            # Wait for title or a key element
            print("Waiting for input...")
            page.wait_for_selector("input[placeholder='Describe your infrastructure issue...']", timeout=10000)

            # Type something
            page.fill("input[placeholder='Describe your infrastructure issue...']", "Hello, check my pods.")

            # Take screenshot of the whole page
            print("Taking screenshot...")
            page.screenshot(path="verification/chat_ui.png")
            print("Screenshot taken at verification/chat_ui.png")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_chat_ui()
