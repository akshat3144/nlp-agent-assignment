import httpx

FDA_BASE = "https://api.fda.gov"


def search_adverse_events(drug_name, limit=10):
    url = f"{FDA_BASE}/drug/event.json"
    params = {
        "search": f'patient.drug.medicinalproduct:"{drug_name}"',
        "limit": limit
    }
    try:
        resp = httpx.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            return resp.json().get("results", [])
        return []
    except Exception as e:
        print(f"  adverse events request failed: {e}")
        return []


def search_recalls(drug_name, limit=5):
    url = f"{FDA_BASE}/drug/enforcement.json"
    params = {
        "search": f'reason_for_recall:"{drug_name}"+openfda.brand_name:"{drug_name}"',
        "limit": limit
    }
    try:
        resp = httpx.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            return resp.json().get("results", [])
        return []
    except Exception as e:
        print(f"  recalls request failed: {e}")
        return []


def search_drug_labels(drug_name, limit=3):
    url = f"{FDA_BASE}/drug/label.json"
    params = {
        "search": f'openfda.brand_name:"{drug_name}"',
        "limit": limit
    }
    try:
        resp = httpx.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            return resp.json().get("results", [])
        return []
    except Exception as e:
        print(f"  labels request failed: {e}")
        return []


def fetch_fda_data(drug_name):
    print(f"\n[Step 2] Querying openFDA for '{drug_name}'...")

    adverse = search_adverse_events(drug_name)
    recalls = search_recalls(drug_name)
    labels = search_drug_labels(drug_name)

    ae_summary = []
    for ae in adverse:
        reactions = []
        if "patient" in ae and "reaction" in ae["patient"]:
            reactions = [r.get("reactionmeddrapt", "") for r in ae["patient"]["reaction"]]
        drugs = []
        if "patient" in ae and "drug" in ae["patient"]:
            drugs = [d.get("medicinalproduct", "") for d in ae["patient"]["drug"][:3]]
        ae_summary.append({
            "serious": ae.get("serious", ""),
            "reactions": reactions,
            "drugs_involved": drugs
        })

    recall_summary = []
    for r in recalls:
        recall_summary.append({
            "reason": r.get("reason_for_recall", ""),
            "classification": r.get("classification", ""),
            "status": r.get("status", ""),
            "distribution": r.get("distribution_pattern", ""),
            "date": r.get("recall_initiation_date", "")
        })

    label_summary = []
    for l in labels:
        label_summary.append({
            "brand_name": l.get("openfda", {}).get("brand_name", [""])[0],
            "indications": (l.get("indications_and_usage", [""])[0])[:500],
            "warnings": (l.get("warnings", [""])[0])[:500] if l.get("warnings") else "",
            "boxed_warning": (l.get("boxed_warning", [""])[0])[:300] if l.get("boxed_warning") else ""
        })

    result = {
        "drug_searched": drug_name,
        "adverse_events_count": len(adverse),
        "adverse_events": ae_summary,
        "recalls_count": len(recalls),
        "recalls": recall_summary,
        "labels_count": len(labels),
        "labels": label_summary
    }

    print(f"  found {len(adverse)} adverse events, {len(recalls)} recalls, {len(labels)} labels")
    return result
