from __future__ import annotations

from dataclasses import dataclass, field

from src import config


@dataclass
class Subgraph:
    nodes: list[dict] = field(default_factory=list)
    links: list[dict] = field(default_factory=list)
    evidence: list[dict] = field(default_factory=list)

    def dict(self) -> dict:
        return {"nodes": self.nodes, "links": self.links, "evidence": self.evidence}


class _Builder:
    def __init__(self) -> None:
        self._nodes: dict[str, dict] = {}
        self._links: set[tuple[str, str, str]] = set()
        self.evidence: list[dict] = []

    def add_node(self, nid: str, label: str, kind: str, confidence: float | None = None) -> None:
        if nid not in self._nodes:
            node = {"id": nid, "label": label, "kind": kind}
            self._nodes[nid] = node

    def add_link(self, source: str, target: str, predicate: str) -> None:
        self._links.add((source, target, predicate))

    def add_evidence(
        self, subject: str, predicate: str, obj: str, source_ids: list[str], metaedge: str
    ) -> None:
        self.evidence.append(
            {
                "subject": subject,
                "predicate": predicate,
                "object": obj,
                "source_ids": source_ids,
                "hetionet_metaedge": metaedge,
            }
        )

    def build(self) -> Subgraph:
        nodes = list(self._nodes.values())
        if len(nodes) > config.MAX_NODES:
            order = {"Disease": 0, "Gene": 1, "BiologicalProcess": 2}
            nodes.sort(key=lambda n: order.get(n["kind"], 3))
            nodes = nodes[: config.MAX_NODES]
            valid = {n["id"] for n in nodes}
            links = [
                {"source": s, "target": t, "predicate": p}
                for (s, t, p) in self._links
                if s in valid and t in valid
            ]
        else:
            links = [
                {"source": s, "target": t, "predicate": p} for (s, t, p) in self._links
            ]
        return Subgraph(nodes=nodes, links=links, evidence=self.evidence)


def from_genes_of_disease(records: list[dict]) -> Subgraph:
    b = _Builder()
    for r in records:
        b.add_node(r["d_id"], r["d_name"], "Disease")
        b.add_node(r["g_id"], r["g_name"], "Gene")
        b.add_link(r["d_id"], r["g_id"], config.METAEDGE_DaG)
        b.add_evidence(
            r["d_name"], config.PREDICATES["DaG"], r["g_name"],
            [r["d_id"], r["g_id"]], "DaG",
        )
    return b.build()


def from_processes_of_disease(records: list[dict]) -> Subgraph:
    b = _Builder()
    seen_dag: set[tuple[str, str]] = set()
    for r in records:
        b.add_node(r["d_id"], r["d_name"], "Disease")
        b.add_node(r["g_id"], r["g_name"], "Gene")
        b.add_node(r["b_id"], r["b_name"], "BiologicalProcess")
        b.add_link(r["d_id"], r["g_id"], config.METAEDGE_DaG)
        b.add_link(r["g_id"], r["b_id"], config.METAEDGE_GpBP)

        if (r["d_id"], r["g_id"]) not in seen_dag:
            seen_dag.add((r["d_id"], r["g_id"]))
            b.add_evidence(
                r["d_name"], config.PREDICATES["DaG"], r["g_name"],
                [r["d_id"], r["g_id"]], "DaG",
            )
        b.add_evidence(
            r["g_name"], config.PREDICATES["GpBP"], r["b_name"],
            [r["g_id"], r["b_id"]], "GpBP",
        )
    return b.build()


def from_shared_genes(records: list[dict]) -> Subgraph:
    b = _Builder()
    for r in records:
        b.add_node(r["a_id"], r["a_name"], "Disease")
        b.add_node(r["b_id"], r["b_name"], "Disease")
        b.add_node(r["g_id"], r["g_name"], "Gene")
        b.add_link(r["a_id"], r["g_id"], config.METAEDGE_DaG)
        b.add_link(r["b_id"], r["g_id"], config.METAEDGE_DaG)
        b.add_evidence(
            r["g_name"],
            "associates with both diseases",
            f'{r["a_name"]} + {r["b_name"]}',
            [r["a_id"], r["b_id"], r["g_id"]],
            "DaG",
        )
    return b.build()


def from_diseases_by_symptom(records: list[dict]) -> Subgraph:
    b = _Builder()
    for r in records:
        b.add_node(r["s_id"], r["s_name"], "Symptom")
        b.add_node(r["d_id"], r["d_name"], "Disease")
        b.add_link(r["d_id"], r["s_id"], config.METAEDGE_DpS)
        b.add_evidence(
            r["d_name"], config.PREDICATES["DpS"], r["s_name"],
            [r["d_id"], r["s_id"]], "DpS",
        )
    return b.build()


def from_diseases_by_symptoms(records: list[dict]) -> Subgraph:
    b = _Builder()
    for r in records:
        if not r.get("informed"):
            continue  # no grafo, só os sintomas que o usuário informou
        b.add_node(r["s_id"], r["s_name"], "Symptom")
        b.add_node(r["d_id"], r["d_name"], "Disease")
        b.add_link(r["d_id"], r["s_id"], config.METAEDGE_DpS)
        b.add_evidence(
            r["d_name"], config.PREDICATES["DpS"], r["s_name"],
            [r["d_id"], r["s_id"]], "DpS",
        )
    return b.build()


def differential_table(records: list[dict], max_symptoms: int = 8) -> list[dict]:
    by_disease: dict[str, dict] = {}
    order: list[str] = []
    for r in records:
        d = r["d_name"]
        if d not in by_disease:
            by_disease[d] = {"disease": d, "matched": r["matched"], "symptoms": []}
            order.append(d)
        by_disease[d]["symptoms"].append(
            {"name": r["s_name"], "informed": bool(r.get("informed"))}
        )
    out = []
    for d in order:
        entry = by_disease[d]
        entry["symptoms"] = entry["symptoms"][:max_symptoms]
        out.append(entry)
    return out


def from_symptoms_of_disease(records: list[dict]) -> Subgraph:
    b = _Builder()
    for r in records:
        b.add_node(r["d_id"], r["d_name"], "Disease")
        b.add_node(r["s_id"], r["s_name"], "Symptom")
        b.add_link(r["d_id"], r["s_id"], config.METAEDGE_DpS)
        b.add_evidence(
            r["d_name"], config.PREDICATES["DpS"], r["s_name"],
            [r["d_id"], r["s_id"]], "DpS",
        )
    return b.build()


def to_cytoscape(response: dict) -> dict:
    nodes = []
    for n in response.get("nodes", []):
        name = n["label"]
        if n.get("confidence") is not None:
            name = f'{name} ({n["confidence"]:.0%})'
        nodes.append({"data": {"id": n["id"], "label": n["kind"], "name": name}})
    edges = []
    for i, l in enumerate(response.get("links", [])):
        edges.append(
            {
                "data": {
                    "id": f"e{i}",
                    "source": l["source"],
                    "target": l["target"],
                    "label": l["predicate"],
                }
            }
        )
    return {"nodes": nodes, "edges": edges}
