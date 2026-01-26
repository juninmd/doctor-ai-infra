from playwright.sync_api import sync_playwright, expect
import time

def test_frontend(page):
    # Mock the chat endpoint
    def handle_chat(route):
        response_body = (
            '{"type": "activity", "agent": "Supervisor"}\n'
            '{"type": "activity", "agent": "K8s_Specialist"}\n'
            '{"type": "message", "agent": "K8s_Specialist", "content": "I am checking the pods now. Everything looks healthy."}\n'
            '{"type": "final"}\n'
        )
        route.fulfill(
            status=200,
            content_type="application/x-ndjson",
            body=response_body
        )

    page.route("**/chat", handle_chat)

    # Go to app
    page.goto("http://localhost:5173")

    # Check title
    expect(page.get_by_role("heading", name="SRE Intelligent Agent")).to_be_visible()

    # Type a message
    page.get_by_placeholder("Describe the infrastructure issue...").fill("Check my pods")

    # Click send
    # The button has a Send icon, might not have text. Using locator with class or role button
    page.get_by_role("button").click()

    # Wait for response
    expect(page.get_by_text("I am checking the pods now")).to_be_visible()

    # Expand thinking process (it auto expands, but ensuring it is visible)
    # The thinking process shows "K8s Specialist"
    expect(page.get_by_text("K8s Specialist")).to_be_visible()

    # Take screenshot
    time.sleep(1) # Wait for animations
    page.screenshot(path="verification/frontend_chat.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            test_frontend(page)
            print("Verification successful")
        except Exception as e:
            print(f"Verification failed: {e}")
            page.screenshot(path="verification/frontend_error.png")
            raise e
        finally:
            browser.close()
