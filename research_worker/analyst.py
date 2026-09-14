"""Fixed deterministic research interpreter. No host objects. No generated code."""

from __future__ import annotations

from typing import Any

from research_worker.research_task import (
    AGENT_ID,
    AUTHORITY_CLASS,
    EPISTEMIC_CLASS,
    PRODUCTION_CLASS,
    PROTOCOL_VERSION,
    validate_research_task,
)


def interpret_research_task(task: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    validated = validate_research_task(task)
    _ = context.get("context_id")
    observations: list[dict[str, Any]] = []
    claims: list[dict[str, Any]] = []
    hypotheses: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    provenance_refs: list[dict[str, Any]] = []
    uncertainty: list[dict[str, Any]] = []
    statement_items: list[dict[str, Any]] = []

    for item in validated["supplied_items"]:
        provenance = item["provenance_ref"] if item["provenance_ref"] else "UNKNOWN"
        if provenance == "UNKNOWN":
            uncertainty.append({"target_id": item["item_id"], "label": "UNVERIFIED"})
        provenance_refs.append(
            {
                "item_id": item["item_id"],
                "item_type": item["item_type"],
                "provenance_ref": provenance,
            }
        )
        if item["item_type"] == "OBSERVATION":
            observations.append(
                {
                    "observation_id": item["item_id"],
                    "text": item["text"],
                    "provenance_ref": provenance,
                    "epistemic_class": EPISTEMIC_CLASS,
                }
            )
            statement_items.append(item)
        elif item["item_type"] == "EVIDENCE":
            statement_items.append(item)
        elif item["item_type"] == "CLAIM":
            claims.append(
                {
                    "claim_id": item["item_id"],
                    "text": item["text"],
                    "epistemic_class": EPISTEMIC_CLASS,
                }
            )
            statement_items.append(item)
        elif item["item_type"] == "HYPOTHESIS":
            hypotheses.append(
                {
                    "hypothesis_id": item["item_id"],
                    "statement": item["text"],
                    "label": "HYPOTHESIS",
                    "epistemic_class": EPISTEMIC_CLASS,
                }
            )
            uncertainty.append({"target_id": item["item_id"], "label": "UNCERTAIN"})
        elif item["item_type"] == "PREDICTION":
            hypothesis_ref = None
            if hypotheses:
                hypothesis_ref = hypotheses[0]["hypothesis_id"]
            predictions.append(
                {
                    "prediction_id": item["item_id"],
                    "statement": item["text"],
                    "label": "PREDICTION",
                    "hypothesis_ref": hypothesis_ref,
                    "epistemic_class": EPISTEMIC_CLASS,
                }
            )
            uncertainty.append({"target_id": item["item_id"], "label": "UNTESTED"})

    contradictions = _contradictions(statement_items, validated["constraints"]["max_contradictions"])
    experiments = _experiments(
        hypotheses,
        observations,
        validated["constraints"]["max_experiments"],
    )
    reviews = _reviews(claims, contradictions, validated["constraints"]["max_reviews"])
    return {
        "protocol_version": PROTOCOL_VERSION,
        "agent_id": AGENT_ID,
        "agent_context_id": validated["agent_context_id"],
        "mission_id": validated["mission_id"],
        "authority_class": AUTHORITY_CLASS,
        "epistemic_class": EPISTEMIC_CLASS,
        "production_class": PRODUCTION_CLASS,
        "observations": observations,
        "claims": claims,
        "hypotheses": hypotheses,
        "predictions": predictions,
        "contradictions": contradictions,
        "proposed_experiments": experiments,
        "requested_reviews": reviews,
        "uncertainty_labels": uncertainty,
        "provenance_refs": provenance_refs,
    }


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


def _contradictions(items: list[dict[str, Any]], maximum: int) -> list[dict[str, Any]]:
    ordered = sorted(items, key=lambda item: item["item_id"])
    found: list[dict[str, Any]] = []
    serial = 1
    for index, left in enumerate(ordered):
        for right in ordered[index + 1 :]:
            if not _negation_pair(left["text"], right["text"]):
                continue
            found.append(
                {
                    "contradiction_id": f"contradiction.{serial}",
                    "left_item_id": left["item_id"],
                    "right_item_id": right["item_id"],
                    "rationale": "supplied texts differ by an explicit NOT prefix",
                }
            )
            serial += 1
            if len(found) >= maximum:
                return found
    return found


def _negation_pair(left: str, right: str) -> bool:
    a = _norm(left)
    b = _norm(right)
    return a == "not " + b or b == "not " + a


def _experiments(
    hypotheses: list[dict[str, Any]],
    observations: list[dict[str, Any]],
    maximum: int,
) -> list[dict[str, Any]]:
    if maximum <= 0 or not hypotheses or observations:
        return []
    selected = hypotheses[0]
    return [
        {
            "experiment_id": "experiment.missing-observation",
            "hypothesis_id": selected["hypothesis_id"],
            "method": "descriptive inspection of supplied context; no external execution",
            "missing_observation": "required observation is absent from supplied context",
            "execution_requested": False,
        }
    ][:maximum]


def _reviews(
    claims: list[dict[str, Any]],
    contradictions: list[dict[str, Any]],
    maximum: int,
) -> list[dict[str, Any]]:
    reviews: list[dict[str, Any]] = []
    for claim in claims:
        reviews.append({"artifact_id": claim["claim_id"]})
        if len(reviews) >= maximum:
            return reviews
    for contradiction in contradictions:
        reviews.append({"artifact_id": contradiction["contradiction_id"]})
        if len(reviews) >= maximum:
            return reviews
    return reviews
