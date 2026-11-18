from __future__ import annotations

from src import config, graph_context, intent, llm, retrieval


def _base_response(intent_kind: str, data_mode: str) -> dict:
    return {
        "answer": "",
        "nodes": [],
        "links": [],
        "evidence": [],
        "intent": intent_kind,
        "source": config.SOURCE,
        "mode": {"data": data_mode, "llm": "n/a"},
        "limitations": [],
    }


def _abstain(response: dict, message: str) -> dict:
    response["answer"] = message
    response["mode"]["llm"] = "abstention"
    return response


def answer_question(question: str) -> dict:
    it = intent.identify(question)

    resp = _base_response(it.kind, "neo4j")

    if it.kind == "out_of_scope":
        return _abstain(resp, "It's not possible to identify the intent from the question.")

    if it.kind == "genes_of_disease":
        records = retrieval.genes_of_disease(it.diseases[0])
        sub = graph_context.from_genes_of_disease(records)
    elif it.kind == "processes_of_disease":
        records = retrieval.processes_of_disease(it.diseases[0])
        sub = graph_context.from_processes_of_disease(records)
    elif it.kind == "shared_genes":
        records = retrieval.shared_genes(it.diseases[0], it.diseases[1])
        sub = graph_context.from_shared_genes(records)
    elif it.kind == "diseases_by_symptom":
        records = retrieval.diseases_by_symptom(it.symptoms[0])
        sub = graph_context.from_diseases_by_symptom(records)
    elif it.kind == "diseases_by_symptoms":
        records = retrieval.diseases_by_symptoms(it.symptoms)
        sub = graph_context.from_diseases_by_symptoms(records)
        resp["differential"] = graph_context.differential_table(records)
        resp["informed_symptoms"] = [intent.symptom_name(s) for s in it.symptoms]
    elif it.kind == "symptoms_of_disease":
        records = retrieval.symptoms_of_disease(it.diseases[0])
        sub = graph_context.from_symptoms_of_disease(records)
    else:
        return _abstain(resp, "Intent not supported in this version.")

    resp["nodes"] = sub.nodes
    resp["links"] = sub.links
    resp["evidence"] = sub.evidence

    text, llm_mode = llm.generate_answer(question, sub.evidence)
    resp["answer"] = text
    resp["mode"]["llm"] = llm_mode
    return resp

