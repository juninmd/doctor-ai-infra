from playwright.sync_api import Page, expect, sync_playwright
import time

def verify_chat_ui(page: Page):
    # 1. Go to home page
    page.goto("http://localhost:3000")

    # 2. Check title
    expect(page.get_by_text("Infra Agent Manager")).to_be_visible()

    # 3. Check Input and Send
    input_field = page.get_by_placeholder("Describe your infrastructure issue...")
    expect(input_field).to_be_visible()

    # 4. Type a message
    input_field.fill("Hello, are you there?")

    # 5. Click Send
    # Use generic locator for submit button since it has no text, only icon
    page.locator("button[type='submit']").click()

    # 6. Verify message appears in chat
    expect(page.get_by_text("Hello, are you there?")).to_be_visible()

    # 7. Wait a bit for potential response (even error)
    try:
        expect(page.get_by_text("Sorry, I encountered an error")).to_be_visible(timeout=10000)
    except:
        pass

    # 8. Screenshot
    page.screenshot(path="/home/jules/verification/chat_ui.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            verify_chat_ui(page)
        finally:
            browser.close()
