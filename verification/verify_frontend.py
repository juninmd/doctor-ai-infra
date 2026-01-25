from playwright.sync_api import sync_playwright, expect

def run(playwright):
    print("Launching browser...")
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    # Mock the API response
    print("Setting up API mock...")
    page.route("**/api/chat", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='{"response": "I have checked the system.", "steps": [{"type": "human", "content": "Hello"}, {"type": "ai", "content": "Thinking...", "tool_calls": [{"name": "list_k8s_pods", "args": {"namespace": "default"}}]}, {"type": "tool", "content": "Pod frontend-123 is CrashLoopBackOff"}, {"type": "ai", "content": "I have checked the system."}]}'
    ))

    print("Navigating to localhost:3000...")
    page.goto("http://localhost:3000")

    # Check title
    expect(page.get_by_text("Infra Agent Manager")).to_be_visible()

    # Type message
    print("Typing message...")
    page.get_by_placeholder("Describe your infrastructure issue...").fill("Hello")
    page.get_by_role("button").click()

    # Wait for response
    print("Waiting for response...")
    expect(page.get_by_text("I have checked the system.")).to_be_visible()

    # Check Accordion (View Process)
    print("Checking accordion...")
    page.get_by_text("View Process").click()

    # Check if tool call is visible
    expect(page.get_by_text("list_k8s_pods")).to_be_visible()

    print("Taking screenshot...")
    page.screenshot(path="verification/frontend_screenshot.png")
    browser.close()
    print("Done.")

if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)
