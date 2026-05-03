import json
from config import client, MODEL


def call_grok(system_prompt, user_prompt, expect_json=False):
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3
    )
    text = resp.choices[0].message.content.strip()

    if expect_json:
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1])
        return json.loads(text)

    return text


def step1_parse_input(state):
    print("\n[Step 1] Parsing user input...")

    system = (
        "You are a pharma query parser. Extract structured information from the user's "
        "question about a pharmaceutical drug or company.\n\n"
        "Return ONLY a valid JSON object with these fields:\n"
        "- drug_name: the primary drug mentioned (use generic name if possible)\n"
        "- company: manufacturer if mentioned, otherwise \"unknown\"\n"
        "- focus_area: one of \"safety\", \"efficacy\", \"market\", \"regulatory\", \"general\"\n"
        "- search_term: clean drug name for FDA API lookup (just the drug name, nothing else)\n"
        "- query_summary: one sentence describing what the user wants to know\n\n"
        "If the user just provides a drug name with no specific question, "
        "set focus_area to \"general\" and query_summary to a general analysis request."
    )
    user = f"User query: {state['user_input']}"

    try:
        parsed = call_grok(system, user, expect_json=True)
        state["parsed_input"] = parsed
        print(f"  drug: {parsed.get('drug_name', '?')}")
        print(f"  focus: {parsed.get('focus_area', '?')}")
    except Exception as e:
        print(f"  parsing failed ({e}), falling back to raw input")
        name = state["user_input"].strip()
        state["parsed_input"] = {
            "drug_name": name,
            "company": "unknown",
            "focus_area": "general",
            "search_term": name,
            "query_summary": f"General analysis of {name}"
        }

    return state


def step3_analyze_signals(state):
    print("\n[Step 3] Analyzing safety signals...")

    fda = state["fda_data"]
    drug = state["parsed_input"]["drug_name"]

    system = (
        "You are a pharmaceutical safety analyst. Given FDA data for a drug, "
        "identify and classify the key safety signals.\n\n"
        "Return ONLY valid JSON with:\n"
        "- overall_risk_level: one of \"critical\", \"high\", \"moderate\", \"low\"\n"
        "- key_findings: list of 3-5 one-sentence findings\n"
        "- adverse_event_patterns: list of objects with \"reaction\", "
        "\"frequency\" (common/uncommon/rare), \"severity\" (serious/non-serious)\n"
        "- recall_assessment: one paragraph on recall history and what it implies\n"
        "- label_concerns: list of strings noting any concerning label language\n"
        "- data_quality_note: one sentence on data availability and confidence\n\n"
        "Be honest about data limitations. If the data is sparse, say so and "
        "set the risk level accordingly. Do not speculate beyond what the data shows."
    )

    fda_str = json.dumps(fda, indent=2, default=str)
    user = f"Drug: {drug}\n\nFDA Data:\n{fda_str}"

    try:
        analysis = call_grok(system, user, expect_json=True)
        state["signal_analysis"] = analysis
        print(f"  risk level: {analysis.get('overall_risk_level', '?')}")
        print(f"  findings: {len(analysis.get('key_findings', []))}")
    except Exception as e:
        print(f"  signal analysis failed: {e}")
        state["signal_analysis"] = {
            "overall_risk_level": "unknown",
            "key_findings": ["Analysis could not be completed"],
            "adverse_event_patterns": [],
            "recall_assessment": "Unable to assess",
            "label_concerns": [],
            "data_quality_note": "Analysis failed due to an error"
        }

    return state


def step4_market_assessment(state):
    print("\n[Step 4] Assessing market impact...")

    drug = state["parsed_input"]["drug_name"]
    company = state["parsed_input"].get("company", "unknown")
    signals = state["signal_analysis"]

    system = (
        "You are a pharmaceutical market analyst. Given a drug's safety signal analysis, "
        "assess the market and competitive implications.\n\n"
        "Return ONLY valid JSON with:\n"
        "- market_impact: one of \"severe\", \"significant\", \"moderate\", \"minimal\"\n"
        "- competitive_positioning: 2-3 sentences on market position effects\n"
        "- prescriber_impact: 2-3 sentences on how prescribing behavior might shift\n"
        "- patient_impact: 1-2 sentences on patient-level implications\n"
        "- regulatory_risk: object with \"level\" (high/moderate/low) and \"explanation\" (one sentence)\n"
        "- opportunities: list of 2-3 strategic opportunities\n"
        "- threats: list of 2-3 key threats\n"
        "- recommended_actions: list of 3-4 objects each with \"action\", \"owner\", \"timeframe\"\n\n"
        "Ground your assessment in the signal analysis provided. "
        "Do not invent data that was not in the input."
    )

    context = {
        "drug": drug,
        "company": company,
        "risk_level": signals.get("overall_risk_level"),
        "key_findings": signals.get("key_findings"),
        "recall_assessment": signals.get("recall_assessment"),
        "adverse_event_patterns": signals.get("adverse_event_patterns", [])
    }
    user = f"Signal analysis for market assessment:\n{json.dumps(context, indent=2)}"

    try:
        assessment = call_grok(system, user, expect_json=True)
        state["market_assessment"] = assessment
        print(f"  market impact: {assessment.get('market_impact', '?')}")
    except Exception as e:
        print(f"  market assessment failed: {e}")
        state["market_assessment"] = {
            "market_impact": "unknown",
            "competitive_positioning": "Could not be assessed.",
            "prescriber_impact": "Unknown",
            "patient_impact": "Unknown",
            "regulatory_risk": {"level": "unknown", "explanation": "Assessment failed"},
            "opportunities": [],
            "threats": [],
            "recommended_actions": []
        }

    return state


def step5_generate_brief(state):
    print("\n[Step 5] Generating intelligence brief...")

    drug = state["parsed_input"]["drug_name"]
    company = state["parsed_input"].get("company", "unknown")
    focus = state["parsed_input"].get("focus_area", "general")
    query = state["parsed_input"].get("query_summary", "")
    fda = state["fda_data"]
    signals = state["signal_analysis"]
    market = state["market_assessment"]

    system = (
        "You are a senior pharmaceutical strategy consultant. Write a market intelligence "
        "brief in clean Markdown format.\n\n"
        "Write from a neutral analyst perspective. Use the data provided, do not make up facts.\n\n"
        "Structure:\n\n"
        "# Drug Intelligence Brief: [Drug Name]\n\n"
        "## Executive Summary\n"
        "2-3 paragraphs: what was found, risk level, key takeaway.\n\n"
        "## Key Findings\n"
        "Bullet points of the most important discoveries.\n\n"
        "## Safety Signal Analysis\n"
        "Adverse event patterns, recall history, label concerns with severity notes.\n\n"
        "## Market & Competitive Impact\n"
        "Market position, prescriber behavior, patient outcomes.\n\n"
        "## Risk Assessment\n"
        "Table with risk categories (regulatory, reputational, clinical, financial) and ratings.\n\n"
        "## Recommended Actions\n"
        "Numbered list with owner (brand team / medical affairs / regulatory) and timeframe.\n\n"
        "## Data Sources\n"
        "List FDA endpoints queried and data coverage.\n\n"
        "---\n"
        "*Generated by Pharma Intelligence Agent | Data from openFDA*\n\n"
        "Keep it thorough but concise. Every sentence should add value."
    )

    brief_input = {
        "drug": drug,
        "company": company,
        "focus_area": focus,
        "query": query,
        "fda_coverage": {
            "adverse_events": fda["adverse_events_count"],
            "recalls": fda["recalls_count"],
            "labels": fda["labels_count"]
        },
        "signal_analysis": signals,
        "market_assessment": market
    }
    user = f"Generate the intelligence brief from this data:\n\n{json.dumps(brief_input, indent=2, default=str)}"

    try:
        brief = call_grok(system, user)
        state["final_brief"] = brief
        print(f"  brief generated ({len(brief)} characters)")
    except Exception as e:
        print(f"  brief generation failed: {e}")
        state["final_brief"] = f"# Brief Generation Failed\n\nError: {e}"

    return state
