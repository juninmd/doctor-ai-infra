from playwright.sync_api import sync_playwright, Page, expect
import json
import time

def verify_tool_calls(page: Page):
    print("Navigating to localhost:5173...")
    page.goto("http://localhost:5173")

    # Mock the /chat endpoint
    def handle_chat(route):
        print("Intercepted /chat request")
        # Create a stream of events
        events = [
            {"type": "activity", "agent": "Supervisor"},
            {"type": "activity", "agent": "K8s_Specialist"},
            {"type": "tool_call", "agent": "K8s_Specialist", "tool": "list_k8s_pods", "args": {"namespace": "default"}},
            {"type": "message", "agent": "K8s_Specialist", "content": "I checked the pods and they are fine."},
            {"type": "final"}
        ]

        # Convert to NDJSON
        response_body = "\n".join(json.dumps(e) for e in events)

        route.fulfill(
            status=200,
            content_type="application/x-ndjson",
            body=response_body
        )

    page.route("**/chat", handle_chat)

    # Interact
    print("Filling input...")
    page.get_by_placeholder("Describe the infrastructure issue...").fill("check my pods")
    print("Clicking submit...")
    page.get_by_role("button").click()

    # Verify
    print("Verifying UI elements...")
    # Check if K8s Specialist appears in the Thinking Process
    # Open the accordion if needed? It defaults to open if processing.

    expect(page.get_by_text("K8s Specialist")).to_be_visible()

    # Check if tool call is visible
    expect(page.get_by_text("list_k8s_pods")).to_be_visible()
    expect(page.get_by_text('{"namespace":"default"}')).to_be_visible()

    # Take screenshot
    time.sleep(2) # Wait for animation
    page.screenshot(path="verification_tool_calls.png")
    print("Screenshot saved to verification_tool_calls.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            verify_tool_calls(page)
            print("Verification successful!")
        except Exception as e:
            print(f"Verification failed: {e}")
            page.screenshot(path="verification_error.png")
            raise
        finally:
            browser.close()
