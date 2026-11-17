
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

if __package__ in (None, ""):
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import neo4j_client

PROCESS_TERMS = [
    "biological process",
    "biological processes",
    "process",
    "processes",
    "participate",
    "participates",
    "pathway",
    "pathways",
]

SYMPTOMS_OF_DISEASE_TERMS = [
    "symptom",
    "symptoms",
    "which symptoms",
    "what symptoms",
    "signs",
    "manifestations",
    "present with",
    "presents with",
]

DISEASE_BY_SYMPTOM_TERMS = [
    "which diseases",
    "what diseases",
    "which disease",
    "present",
    "presents",
    "symptom",
    "who has",
    "associated with the symptom",
    "cause",
    "causes",
]

DIFFERENTIAL_TERMS = [
    "patient",
    "presents the symptoms",
    "symptoms of",
    "possible diseases",
    "possible disease",
    "could have",
    "might have",
    "suffers from",
    "suffering from",
]


@dataclass
class Intent:
    kind: str
    diseases: list[str] = field(default_factory=list)   # real node IDs
    labels: list[str] = field(default_factory=list)     # real graph names (English)
    symptoms: list[str] = field(default_factory=list)   # real Symptom IDs


def _normalize(text: str) -> str:
    t = unicodedata.normalize("NFKD", text.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t).strip()


_name_cache: dict[str, list[tuple[str, str, str]]] | None = None


def _load_names() -> dict[str, list[tuple[str, str, str]]]:
    global _name_cache
    if _name_cache is not None:
        return _name_cache
    cache: dict[str, list[tuple[str, str, str]]] = {"Disease": [], "Symptom": []}
    try:
        rows = neo4j_client.run_query(
            "MATCH (n) WHERE n:Disease OR n:Symptom "
            "RETURN n.id AS id, n.name AS name, head(labels(n)) AS kind"
        )
        for r in rows:
            kind = "Disease" if r["kind"] == "Disease" else "Symptom"
            cache[kind].append((r["id"], r["name"], _normalize(r["name"])))
    except Exception:
        cache = {"Disease": [], "Symptom": []}
    _name_cache = cache
    return cache



def _match_nodes(text_norm: str, kind: str) -> list[tuple[int, str, str]]:
    raw: list[tuple[int, str, str]] = []
    for nid, _name, norm in _load_names()[kind]:
        pos = text_norm.find(norm)
        if pos >= 0:
            raw.append((pos, nid, norm))
    names = [n for _, _, n in raw]
    kept = [
        (pos, nid, norm) for pos, nid, norm in raw
        if not any(norm != other and norm in other for other in names)
    ]
    kept.sort()
    return kept


def _detect_diseases(text_norm: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for _pos, nid, _norm in _match_nodes(text_norm, "Disease"):
        if nid not in seen:
            seen.add(nid)
            out.append((nid, _graph_name(nid, "Disease")))
    return out


def _detect_symptoms(text_norm: str) -> list[str]:
    seen: list[str] = []
    for _pos, sid, _norm in _match_nodes(text_norm, "Symptom"):
        if sid not in seen:
            seen.append(sid)
    return seen


def _graph_name(node_id: str, kind: str) -> str:
    for nid, name, _norm in _load_names()[kind]:
        if nid == node_id:
            return name
    return node_id


def symptom_name(symptom_id: str) -> str:
    return _graph_name(symptom_id, "Symptom")


def identify(question: str) -> Intent:
    norm = _normalize(question)
    diseases = _detect_diseases(norm)

    if diseases:
        ids = [d[0] for d in diseases]
        names = [d[1] for d in diseases]
        if len(ids) >= 2:
            return Intent(kind="shared_genes", diseases=ids[:2], labels=names[:2])
        
        wants_symptoms = any(t in norm for t in SYMPTOMS_OF_DISEASE_TERMS)
        wants_process = any(t in norm for t in PROCESS_TERMS)

        if wants_symptoms:
            kind = "symptoms_of_disease"
        elif wants_process:
            kind = "processes_of_disease"
        else:
            kind = "genes_of_disease"
        return Intent(kind=kind, diseases=ids, labels=names)

    symptoms = _detect_symptoms(norm)
    wants_disease_by_symptom = any(t in norm for t in DISEASE_BY_SYMPTOM_TERMS)
    if symptoms and wants_disease_by_symptom:
        is_differential = any(t in norm for t in DIFFERENTIAL_TERMS)
        if len(symptoms) >= 2 or is_differential:
            return Intent(
                kind="diseases_by_symptoms",
                symptoms=symptoms,
                labels=[symptom_name(s) for s in symptoms],
            )
        return Intent(
            kind="diseases_by_symptom",
            symptoms=symptoms[:1],
            labels=[symptom_name(symptoms[0])],
        )

    return Intent(kind="out_of_scope")
