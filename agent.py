import sys
import json
from datetime import datetime
from pathlib import Path
from state import create_state
from steps import step1_parse_input, step3_analyze_signals, step4_market_assessment, step5_generate_brief
from tools import fetch_fda_data


def run_agent(user_input):
    print("=" * 55)
    print("  PHARMA DRUG INTELLIGENCE AGENT")
    print("=" * 55)
    print(f"\nQuery: {user_input}")

    state = create_state(user_input)

    state = step1_parse_input(state)

    drug = state["parsed_input"].get("search_term", state["parsed_input"].get("drug_name"))
    state["fda_data"] = fetch_fda_data(drug)

    if (state["fda_data"]["adverse_events_count"] == 0
            and state["fda_data"]["recalls_count"] == 0
            and state["fda_data"]["labels_count"] == 0):
        print("\n  !! No FDA data found for this drug.")
        print("  The analysis will proceed but results will be limited.")
        print("  Try common drugs like: metformin, ibuprofen, lisinopril, omeprazole")

    state = step3_analyze_signals(state)
    state = step4_market_assessment(state)
    state = step5_generate_brief(state)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    drug_slug = state["parsed_input"].get("drug_name", "drug").lower().replace(" ", "_")

    out_dir = Path("outputs") / drug_slug
    out_dir.mkdir(parents=True, exist_ok=True)

    brief_file = out_dir / f"brief_{timestamp}.md"
    with open(brief_file, "w", encoding="utf-8") as f:
        f.write(state["final_brief"])

    state_dump = dict(state)
    state_dump["final_brief"] = state_dump["final_brief"][:200] + "...(see brief md)"
    state_file = out_dir / f"state_{timestamp}.json"
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state_dump, f, indent=2, default=str)

    print(f"\n{'=' * 55}")
    print(f"  Brief saved to: {brief_file}")
    print(f"  State saved to: {state_file}")
    print(f"{'=' * 55}")

    return state


if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        print("\nPharma Drug Intelligence Agent")
        print("-" * 35)
        print("Enter a drug name or a question about a pharma drug.")
        print("Examples:")
        print("  metformin")
        print("  What are the safety concerns with Ozempic?")
        print("  Analyze Lipitor recall history")
        print()
        query = input("Your query: ").strip()
        if not query:
            print("No input. Exiting.")
            sys.exit(1)

    run_agent(query)
