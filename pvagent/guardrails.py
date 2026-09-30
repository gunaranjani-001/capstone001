"""Guardrails: every check is traced as a `guardrail` span so it shows up in traceability."""
import re

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PHONE = re.compile(r"\+\d[\d\s-]{8,}\d|\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b")
CATEGORIES = ["Unassessable", "Unlikely", "Possible", "Probable", "Certain"]


def contains_pii(text):
    return bool(EMAIL.search(text) or PHONE.search(text))


class Guardrails:
    def __init__(self, tracer, governance):
        self.tracer = tracer
        self.gov = governance

    def check(self, rule, ok, message):
        with self.tracer.span("guardrail", rule) as sp:
            sp["status"] = "ok" if ok else "blocked"
            sp["attrs"].update(passed=bool(ok), message=message)
        return bool(ok)

    def check_causality(self, category, complete, has_positive_rechallenge, evidence_ids):
        """Return (final_category, list_of_rules_triggered). A model may propose, guardrails dispose."""
        triggered = []
        if not complete:
            self.check("G-C3 no-assessment-without-minimum-data", False, f"{category} -> Unassessable (missing ICH E2D elements)")
            return "Unassessable", ["G-C3"]
        self.check("G-C3 no-assessment-without-minimum-data", True, "minimum data present")
        if category == "Certain" and not has_positive_rechallenge:
            self.check("G-C1 certain-needs-positive-rechallenge", False, "Certain -> Probable")
            category = "Probable"
            triggered.append("G-C1")
        else:
            self.check("G-C1 certain-needs-positive-rechallenge", True, f"{category} permitted")
        if category != "Unassessable" and not evidence_ids:
            self.check("G-C2 conclusion-must-cite-evidence", False, f"{category} -> Unassessable (no evidence cited)")
            category = "Unassessable"
            triggered.append("G-C2")
        else:
            self.check("G-C2 conclusion-must-cite-evidence", True, f"{len(evidence_ids)} evidence items cited")
        return category, triggered
