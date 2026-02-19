import argparse
import sys
import os
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.graph import app_graph

# Ensure we can import from app
# Add 'backend' directory to sys.path so 'app' module can be found
sys.path.append(os.path.dirname(__file__))
# Add project root to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

def print_stream(stream):
    for event in stream:
        for key, value in event.items():
            if key == "Supervisor":
                print(f"\n🤖 **Supervisor:** Routing to -> {value.get('next')}")
            elif "messages" in value:
                # Value is the state update, typically {"messages": [LogMessage]}
                last_msg = value["messages"][-1]
                if isinstance(last_msg, (AIMessage, SystemMessage)):
                    sender = key.replace("_", " ")
                    content = last_msg.content
                    print(f"\n🔧 **{sender}:**\n{content}")
            else:
                # Other updates
                print(f"\nEvent: {key} -> {value}")

def run_interactive():
    print("🚀 **SRE Agent CLI (2026 Edition)**")
    print("Type 'exit' or 'quit' to leave.\n")

    # Maintain conversation history if desired, but for now reset per query is safer for graph state
    # or we can pass previous state. Let's start fresh for now.

    while True:
        try:
            user_input = input("\n👤 **You:** ")
            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye! 👋")
                break

            if not user_input.strip():
                continue

            print("Thinking... 🧠")
            inputs = {"messages": [HumanMessage(content=user_input)]}

            # Run the graph
            # thread_id allows conversation persistence if we use checkpointer
            config = {"configurable": {"thread_id": "cli-session"}}

            # Using .stream() to get updates
            print_stream(app_graph.stream(inputs, config=config))

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def run_single_shot(query):
    print(f"🚀 Processing: {query}")
    inputs = {"messages": [HumanMessage(content=query)]}
    config = {"configurable": {"thread_id": "cli-oneshot"}}
    print_stream(app_graph.stream(inputs, config=config))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SRE Agent CLI")
    parser.add_argument("-i", "--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("query", nargs="*", help="Query to run (if not interactive)")

    args = parser.parse_args()

    if args.interactive:
        run_interactive()
    elif args.query:
        query = " ".join(args.query)
        run_single_shot(query)
    else:
        # Default to interactive if no args
        run_interactive()
