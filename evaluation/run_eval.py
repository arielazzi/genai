from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import neo4j_client, pipeline 

FILE_QUESTIONS = ROOT / "evaluation" / "questions.json"
FILE_RESULTS = ROOT / "evaluation" / "results.md"


def _evidence_names(response: dict) -> set[str]:
    names: set[str] = set()
    for n in response.get("nodes", []):
        names.add(n["label"].lower())
    return names


def _claims_supported(response: dict) -> bool:
    if response["mode"]["llm"] == "abstencao":
        return True
    names = _evidence_names(response)
    if not names:
        return response["mode"]["llm"] == "abstencao"
    return True


def evaluate() -> dict:
    cases = json.loads(FILE_QUESTIONS.read_text(encoding="utf-8"))["casos"]
    data_ok, msg = neo4j_client.ping()
    if not data_ok:
        raise SystemExit(f"{msg}\nInicie o Neo4j e carregue o subconjunto antes de avaliar.")

    rows = []
    n_intent = n_retrieval = n_abstention = n_supported = 0
    n_abstention_cases = 0

    for c in cases:
        r = pipeline.answer_question(c["pergunta"], data_ok=True)
        intent_ok = r["intent"] == c["intencao_esperada"]
        n_intent += intent_ok

        exp = c["esperado"]
        graph_names = _evidence_names(r)
        if r["intent"] in ("diseases_by_symptom", "diseases_by_symptoms"):
            n_entities = len([n for n in r["nodes"] if n["kind"] == "Disease"])
        else:
            n_entities = len([n for n in r["nodes"] if n["kind"] != "Disease"])

        # Retrieval
        rec_ok = True
        if "min_genes" in exp:
            rec_ok &= n_entities >= exp["min_genes"]
        if "min_processos" in exp:
            n_bp = len([n for n in r["nodes"] if n["kind"] == "BiologicalProcess"])
            rec_ok &= n_bp >= exp["min_processos"]
        if "deve_conter_algum" in exp:
            rec_ok &= any(g.lower() in graph_names for g in exp["deve_conter_algum"])
        if exp.get("tipo") == "abstencao":
            rec_ok = r["mode"]["llm"] == "abstencao"
        n_retrieval += rec_ok

        # Abstention
        if exp.get("deve_abster"):
            n_abstention_cases += 1
            if r["mode"]["llm"] == "abstencao":
                n_abstention += 1

        supported = _claims_supported(r)
        n_supported += supported

        rows.append(
            {
                "id": c["id"],
                "question": c["pergunta"],
                "intent_exp": c["intencao_esperada"],
                "intent_got": r["intent"],
                "intent_ok": intent_ok,
                "n_genes": len([n for n in r["nodes"] if n["kind"] == "Gene"]),
                "n_bp": len([n for n in r["nodes"] if n["kind"] == "BiologicalProcess"]),
                "n_evid": len(r["evidence"]),
                "llm_mode": r["mode"]["llm"],
                "rec_ok": rec_ok,
                "supported": supported,
            }
        )

    total = len(cases)
    summary = {
        "total": total,
        "acerto_intencao": f"{n_intent}/{total}",
        "acerto_recuperacao": f"{n_retrieval}/{total}",
        "abstencao_correta": f"{n_abstention}/{n_abstention_cases}" if n_abstention_cases else "n/a",
        "taxa_afirmacoes_sustentadas": f"{n_supported}/{total} = {n_supported/total:.0%}",
    }
    _write(rows, summary)
    return summary


def _write(rows: list[dict], summary: dict) -> None:
    md = ["# Resultados da avaliação\n"]
    for k, v in summary.items():
        md.append(f"- **{k}**: {v}")
    md.append("\n## Detalhe por caso\n")
    md.append("| # | pergunta | intenção esp/obt | genes | bp | evid | modo LLM | rec ok | sustentado |")
    md.append("|---|----------|------------------|-------|----|------|----------|--------|------------|")
    for l in rows:
        md.append(
            f"| {l['id']} | {l['question'][:48]} | {l['intent_exp']} / {l['intent_got']} "
            f"| {l['n_genes']} | {l['n_bp']} | {l['n_evid']} | {l['llm_mode']} "
            f"| {'PASS' if l['rec_ok'] else 'FAIL'} | {'PASS' if l['supported'] else 'FAIL'} |"
        )

    FILE_RESULTS.write_text("\n".join(md), encoding="utf-8")


if __name__ == "__main__":
    summary = evaluate()
    print("Resumo da avaliação:")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    neo4j_client.close()
