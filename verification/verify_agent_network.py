from playwright.sync_api import sync_playwright, expect

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    # Mock the streaming response
    def handle_chat(route):
        response_body = (
            '{"type": "activity", "agent": "Supervisor"}\n'
            '{"type": "activity", "agent": "K8s_Specialist"}\n'
            '{"type": "message", "content": "Checking pods...", "agent": "K8s_Specialist"}\n'
            '{"type": "final"}\n'
        )

        route.fulfill(
            status=200,
            content_type="application/x-ndjson",
            body=response_body
        )

    page.route("**/chat", handle_chat)

    try:
        page.goto("http://localhost:3000")

        # Check if header is visible
        expect(page.get_by_role("heading", name="INFRA_AGENT_NET")).to_be_visible()

        # Check if the Supervisor node is visible in the visualizer
        expect(page.get_by_text("SUPERVISOR")).to_be_visible()

        # Check if K8s node is visible
        expect(page.get_by_text("Kubernetes")).to_be_visible()

        # Fill input and send
        page.get_by_placeholder("Initialize infrastructure analysis...").fill("Check my pods")
        page.locator("form button[type='submit']").click()

        # Wait for the message to appear in the chat
        expect(page.get_by_text("Checking pods...")).to_be_visible()

        # Take screenshot
        page.screenshot(path="verification_agent_network.png")
        print("Verification successful, screenshot saved.")

    except Exception as e:
        print(f"Verification failed: {e}")
        page.screenshot(path="verification_error.png")
        raise e

    finally:
        browser.close()

if __name__ == "__main__":
    with sync_playwright() as p:
        run(p)
