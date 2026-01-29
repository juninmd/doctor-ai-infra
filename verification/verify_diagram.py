import time
from playwright.sync_api import sync_playwright

def verify_mermaid(page):
    # Mock the chat endpoint
    def handle_chat(route):
        # Respond with a stream of events
        # 1. Activity
        # 2. Message with Mermaid code
        # 3. Final

        response_body = (
            '{"type": "activity", "agent": "Topology_Specialist", "content": "Generating diagram..."}\n'
            '{"type": "message", "agent": "Topology_Specialist", "content": "Here is the diagram:\\n\\n```mermaid\\ngraph TD;\\n    A[Client] --> B[Load Balancer];\\n    B --> C[Service];\\n    class C tier1;\\n    classDef tier1 fill:#f9f,stroke:#333,stroke-width:2px;\\n```"}\n'
            '{"type": "final"}\n'
        )
        route.fulfill(
            status=200,
            content_type="text/plain",
            body=response_body
        )

    page.route("**/chat", handle_chat)

    page.goto("http://localhost:5173")

    # Type in input
    page.fill("input[type='text']", "Show me architecture")
    page.click("button[type='submit']")

    # Wait for diagram
    page.wait_for_selector(".mermaid-chart", timeout=10000)

    # Wait a bit for render
    time.sleep(2)

    # Take screenshot
    page.screenshot(path="verification/mermaid_diagram.png")
    print("Screenshot saved to verification/mermaid_diagram.png")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    try:
        verify_mermaid(page)
    except Exception as e:
        print(f"Error: {e}")
        page.screenshot(path="verification/error.png")
    finally:
        browser.close()
