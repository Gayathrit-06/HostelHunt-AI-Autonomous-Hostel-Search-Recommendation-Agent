import sys
import warnings

# Suppress all deprecation warnings globally
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

from langchain_core.messages import HumanMessage
from config import validate_config
from agent import agent_executor

def run_cli():
    print("=" * 55)
    print("  🏠 HostelMate — Agentic AI Hostel Search Agent ")
    print("=" * 55)
    print("Type 'exit' or 'quit' to stop.\n")

    try:
        validate_config()
    except ValueError as e:
        print(f"Startup Error: {e}")
        sys.exit(1)

    while True:
        try:
            user_input = input("\nUser > ").strip()
            
            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit"]:
                print("\nExiting HostelMate. Goodbye!")
                break

            print("\n[HostelMate is searching...]\n")

            # Send input as a HumanMessage object
            response = agent_executor.invoke(
                {"messages": [HumanMessage(content=user_input)]}
            )

            # Read result content safely
            final_message = response["messages"][-1].content
            
            print("-" * 55)
            print(f"HostelMate:\n\n{final_message.strip()}")
            print("-" * 55)

        except KeyboardInterrupt:
            print("\nSession interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")

if __name__ == "__main__":
    run_cli()

# Updated main.py loop with conversation history
history = []

while True:
    user_input = input("\nUser > ").strip()
    if user_input.lower() in ["exit", "quit"]:
        break

    history.append(HumanMessage(content=user_input))
    
    response = agent_executor.invoke({"messages": history})
    
    final_message = response["messages"][-1]
    history.append(final_message)  # Save response to history
    
    print("-" * 55)
    print(f"HostelMate:\n\n{final_message.content.strip()}")
    print("-" * 55)