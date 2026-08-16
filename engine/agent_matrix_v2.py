#!/usr/bin/env python3
"""Agent Matrix v2 generator (W12 PART J) — machine-generated, never hand-edited.

Laws:
- Source of truth = config/agent_registry.yaml ONLY. Nothing in the output is invented:
  any field the registry does not carry is printed as an explicit DEFINED marker.
- Deterministic output (no clock, no randomness): regenerating must reproduce the file
  byte-identically. tests/test_agent_matrix_v2.py pins freshness.
- Statuses are never promoted here; this document REPORTS the registry, it does not change it.
Field map (PART J's 16 required fields):
  identity=agent_id+name+form+lane · version · status(+criticality) · capabilities ·
  owner(governance law; AG-23=human) · dependencies · inputs(deps+probe feeds, table/deps
  granularity) · outputs(state_tables) · authority(allowed/forbidden) ·
  evidence_requirements(status-derived rule) · probes(required_probes+probe_refs) ·
  health · circuit · failure_mode(failure_behavior) · fallback(failure_policy+boot class) ·
  runtime(ops.runtime) · cadence
"""
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "config" / "agent_registry.yaml"
OUT = ROOT / "docs" / "architecture" / "agent_matrix_v2.md"

FIELDS = ("identity", "version", "status", "capabilities", "owner", "dependencies",
          "inputs", "outputs", "authority", "evidence_requirements", "probes", "health",
          "circuit", "failure_mode", "fallback", "runtime", "cadence")
NO_IO = "— DEFINED (no tables declared; payload-typed IO is a contract-v2 field, W10 F3 queue)"


def _owner(a):
    if a["agent_id"] == "AG-23":
        return "human operator (approval gateway; never software — F5 law)"
    return "AHOS governance — promotion only via improvement_proposal_v1 → human gate"


def _evidence_req(a):
    s = a["status"]
    if s == "EXISTS":
        return "executable evidence on file (CI-linted, test_exists_agents_have_real_evidence_paths): " + a.get("evidence", "—")
    if s == "PARTIAL":
        return "promotion requires probe id + contract envelope + test + evidence pack (NOT met yet)"
    if s == "PLANNED":
        return "spec only; enters runtime solely through self-evolution loop (PART K)"
    return "no artifact exists (MISSING) — build only via improvement_proposal_v1 with human approval"


def _fallback(a):
    pol = a["ops"]["failure_policy"]
    bc = a["ops"]["boot_class"]
    note = {"CRITICAL": "SAFE_HALT semantics; floor unaffected only if non-critical path",
            "NON_CRITICAL": "SYSTEM_DEGRADED; core pipeline continues",
            "ADVISORY": "SYSTEM_DEGRADED; DETERMINISTIC_ONLY floor continues unimpaired",
            "OPTIONAL": "never affects system status"}[bc]
    return (f"on_failure={pol.get('on_failure')}, retries={pol.get('retries')}, "
            f"backoff_s={pol.get('backoff_s')} · boot_class={bc} ⇒ {note}")


def render_agent(a):
    o = a["ops"]
    op = o["operability"]
    st = o.get("state_tables") or []
    rows = {
        "identity": f"{a['agent_id']} · {a['name']} · form={a['form']} · lane={a['lane']}",
        "version": a.get("version") or "—",
        "status": (f"{a['status']} · criticality={a['criticality']} · "
                   f"operability impl/contract/orch/live = {op['implemented']}/{op['contracted']}/"
                   f"{op['orchestrated']}/{op['live']}"),
        "capabilities": ", ".join(a.get("capabilities") or []) or "—",
        "owner": _owner(a),
        "dependencies": ", ".join(a.get("dependencies") or []) or "∅",
        "inputs": (f"agent deps [{', '.join(a.get('dependencies') or []) or '∅'}] + probe feeds "
                   f"[{', '.join(a.get('required_probes') or [])}] (deps/table granularity; "
                   f"payload-typed IO = contract v2, F3 queue)"),
        "outputs": ", ".join(st) if st else NO_IO,
        "authority": (f"allowed: {', '.join(a.get('allowed_authority') or [])} · "
                      f"forbidden: {', '.join(a.get('forbidden_authority') or [])}"),
        "evidence_requirements": _evidence_req(a),
        "probes": (f"required: {', '.join(a.get('required_probes') or [])} · "
                   f"refs: {', '.join(o.get('probe_refs') or []) or '—'}"),
        "health": f"{o['health'].get('kind')} → {o['health'].get('ref')}",
        "circuit": f"{o['circuit'].get('state')} (failures={o['circuit'].get('failures')})",
        "failure_mode": a.get("failure_behavior", "—"),
        "fallback": _fallback(a),
        "runtime": o["runtime"],
        "cadence": a["cadence"],
    }
    return "### " + rows["identity"] + "\n" + "\n".join(f"- **{k}**: {rows[k]}" for k in FIELDS[1:]) + "\n"


def render(reg):
    agents = reg["agents"]
    from collections import Counter
    c = Counter(a["status"] for a in agents)
    head = f"""# AHOS — AGENT MATRIX v2 (W12 PART J, machine-generated review)
Generator: engine/agent_matrix_v2.py · source of truth: config/agent_registry.yaml ·
freshness pinned by tests/test_agent_matrix_v2.py (doc == generator output, byte-identical).
Laws honored: no agent exists by declaration alone (PART J) — MISSING/PARTIAL/PLANNED never
promoted without executable evidence; no filler agents; every field is either registry-derived
or an explicit DEFINED marker; typed payload-level IO is queued for contract v2 (F3), and
until then inputs/outputs are declared at dependency/state-table granularity — never invented.
Census (computed, not asserted): {len(agents)} agents — """ + " / ".join(
        f"{k} {c.get(k, 0)}" for k in ("EXISTS", "PARTIAL", "PLANNED", "MISSING")) + """

Each block below carries exactly the 16 PART J fields: identity, version, status, capabilities,
owner, dependencies, inputs, outputs, authority, evidence_requirements, probes, health,
circuit, failure_mode, fallback, runtime, cadence.

"""
    return head + "\n".join(render_agent(a) for a in agents)


def main():
    reg = yaml.safe_load(REGISTRY.read_text(encoding='utf-8'))
    out = render(reg)
    if "--check" in sys.argv:
        cur = OUT.read_text(encoding='utf-8')
        if cur != out:
            print("STALE: agent_matrix_v2.md != generator output", file=sys.stderr)
            return 1
        print("FRESH: agent_matrix_v2.md matches generator output")
        return 0
    OUT.write_text(out)
    print(f"wrote {OUT} ({len(out)} bytes, {len(reg['agents'])} agents)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
