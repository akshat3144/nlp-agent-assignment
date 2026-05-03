# Pharma Drug Intelligence Agent

A multi-step LLM agent that takes a drug name or pharma-related query, pulls real FDA data, and generates a structured market intelligence brief.

## What It Does

The agent runs a 5-step pipeline:

1. **Parse Input** (LLM) — Takes the user's raw query and extracts the drug name, focus area, and search terms
2. **Fetch FDA Data** (Tool) — Queries three openFDA endpoints for adverse events, recalls, and drug labeling data
3. **Analyze Signals** (LLM) — Classifies the raw FDA data into safety signals with severity ratings and pattern identification
4. **Market Assessment** (LLM) — Evaluates competitive and market implications based on the signal analysis
5. **Generate Brief** (LLM) — Produces a structured Markdown intelligence brief combining all previous steps

Each step depends on the outputs of previous steps. The agent maintains a shared state dictionary that accumulates results as the chain progresses.

## Setup

```bash
pip install -r requirements.txt
```

Set your Groq API key:

```bash
# Linux/Mac
export GROQ_API_KEY="your-key-here"

# Windows
set GROQ_API_KEY=your-key-here
```

Or create a `.env` file in the project root:

```
GROQ_API_KEY=your-key-here
```

You can get a free key from https://console.groq.com

No other API keys are needed — openFDA is free and keyless.

## Running

Interactive mode:

```bash
python agent.py
```

With a direct query:

```bash
python agent.py metformin
python agent.py "What are the safety concerns with Ozempic?"
python agent.py "Analyze Lipitor recall activity"
```

## Output

Each run creates a subfolder under `outputs/[drug_name]/` containing:

- `brief_[timestamp].md` — the final intelligence brief
- `state_[timestamp].json` — the full chain state for inspection

Example:

```
outputs/
└── semaglutide/
    ├── brief_20260501_221453.md
    └── state_20260501_221453.json
```

## Project Structure

```
├── agent.py              # entry point, orchestrates the chain
├── steps.py              # LLM step functions (parse, analyze, assess, generate)
├── tools.py              # openFDA API calls (adverse events, recalls, labels)
├── state.py              # shared state dictionary
├── config.py             # Groq API client setup
├── requirements.txt      # dependencies
│
└── outputs/              # generated at runtime, gitignored
    └── [drug_name]/
        ├── brief_[timestamp].md
        └── state_[timestamp].json
```

## Chain Dependencies

```
User Input
    │
    ▼
[Step 1: Parse] ──────────────────────────┐
    │                                     │
    ▼                                     │
[Step 2: FDA API] ─── drug name from S1   │
    │                                     │
    ▼                                     │
[Step 3: Signals] ─── FDA data (S2)       │
    │                + parsed input (S1)  │
    ▼                                     │
[Step 4: Market] ──── signals (S3)        │
    │                + parsed input (S1)  │
    ▼                                     │
[Step 5: Brief] ───── everything (S1-S4) ─┘
```

No step can run without the ones before it. Step 3 needs the FDA data from Step 2. Step 4 needs the signal analysis from Step 3. Step 5 needs everything.

## Error Handling

- If the Groq API fails at any step, the agent falls back to a default structure and continues the chain
- If openFDA returns no data (drug not found), the agent warns the user but still runs the analysis with a note about limited data
- If the user provides a vague query, Step 1 does its best to extract a drug name and defaults to a general analysis
