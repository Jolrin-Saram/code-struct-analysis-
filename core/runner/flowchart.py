from __future__ import annotations

from collections import defaultdict
from typing import Any

CATEGORY_OUTCOME = {
    "Buffer Overflow": "Crash / Stack Corruption",
    "Memory Corruption": "Crash / Undefined Behavior",
    "Memory Safety": "Data Corruption Risk",
    "Command Injection": "Arbitrary Command Execution",
    "Deployment Fragility": "Runtime Failure in Different Environments",
    "Quality Debt": "Hidden Bug Accumulation",
}


def build_error_flowchart(findings: list[dict[str, Any]], top_n: int = 20) -> str:
    if not findings:
        return "flowchart TD\n  A[\"Code Scan\"] --> B[\"No risky patterns detected\"]\n"

    ranked = sorted(findings, key=lambda x: int(x.get("score", 0)), reverse=True)[:top_n]

    lines: list[str] = []
    lines.append("flowchart TD")
    lines.append('  A["Code Scan Start"] --> B["Match Risk Rules"]')

    category_nodes: dict[str, str] = {}
    file_nodes: dict[str, str] = {}

    for idx, finding in enumerate(ranked, start=1):
        category = str(finding.get("category", "General Risk"))
        file_ref = f"{finding.get('file', '?')}:{finding.get('line', '?')}"
        rule_id = str(finding.get("rule_id", "rule"))

        if category not in category_nodes:
            cnode = f"C{len(category_nodes) + 1}"
            category_nodes[category] = cnode
            lines.append(f'  B --> {cnode}["{_escape(category)}"]')

            outcome = CATEGORY_OUTCOME.get(category, "Potential Runtime Error")
            onode = f"O{len(category_nodes)}"
            lines.append(f'  {cnode} --> {onode}["{_escape(outcome)}"]')

        fnode = f"F{idx}"
        lines.append(
            f'  {category_nodes[category]} --> {fnode}["{_escape(rule_id)} @ { _escape(file_ref)}"]'
        )

        file_key = str(finding.get("file", "?"))
        if file_key not in file_nodes:
            pnode = f"P{len(file_nodes) + 1}"
            file_nodes[file_key] = pnode
            lines.append(f'  {pnode}["File: {_escape(file_key)}"]')

        lines.append(f"  {fnode} --> {file_nodes[file_key]}")

    return "\n".join(lines) + "\n"


def summarize_flow_edges(findings: list[dict[str, Any]]) -> dict[str, int]:
    edges: dict[str, int] = defaultdict(int)
    for f in findings:
        category = str(f.get("category", "General Risk"))
        outcome = CATEGORY_OUTCOME.get(category, "Potential Runtime Error")
        edges[f"{category} -> {outcome}"] += 1
    return dict(sorted(edges.items(), key=lambda x: x[1], reverse=True))


def _escape(text: str) -> str:
    return text.replace('"', "'")
