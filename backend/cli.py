import argparse
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from langchain_core.messages import HumanMessage
from app.graph import app_graph
from app.rag import initialize_rag

def main():
    parser = argparse.ArgumentParser(description="SRE Agent CLI")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive chat mode")
    parser.add_argument("query", nargs="*", help="Single query to execute")
    args = parser.parse_args()

    # Initialize Knowledge Base
    initialize_rag()

    if args.interactive:
        print("\n🚀 SRE Agent CLI (Interactive Mode)")
        print("Type 'exit' or 'quit' to stop.\n")

        chat_history = []

        while True:
            try:
                user_input = input("User: ")
                if user_input.lower() in ["exit", "quit"]:
                    break

                chat_history.append(HumanMessage(content=user_input))

                print("Agent: ", end="", flush=True)

                # Using stream_mode="updates" to get node updates
                for event in app_graph.stream({"messages": chat_history}, stream_mode="updates"):
                    # Event is a dict of {NodeName: {state_update}}
                    for node, values in event.items():
                        if "messages" in values:
                            # get the last message
                            last_msg = values["messages"][-1]

                            # Update local history so the next turn remembers this
                            chat_history.append(last_msg)

                            if hasattr(last_msg, "content"):
                                chunk = last_msg.content
                                print(f"\n[{node}]: {chunk}", end="")

                print("\n")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\nError: {e}")

    elif args.query:
        query = " ".join(args.query)
        print(f"Executing: {query}")

        chat_history = [HumanMessage(content=query)]

        for event in app_graph.stream({"messages": chat_history}, stream_mode="updates"):
            for node, values in event.items():
                 if "messages" in values:
                    last_msg = values["messages"][-1]
                    if hasattr(last_msg, "content"):
                         print(f"\n[{node}]: {last_msg.content}")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
