from __future__ import annotations

import ollama
from src import config

SYSTEM = (
    "You are a biomedical relation-exploration assistant. Answer in English and ONLY based on the relations provided below, "
    "retrieved from a knowledge graph. Rules: \n"
    "1. do not invent genes, diseases or processes that are not in the relations; "
    "2. describe association, never causation; "
    "3. do not provide diagnosis, prognosis or clinical advice; "
    "4. if the relations are insufficient, say so clearly. Be concise and cite entities by name."
)

def _evidence_to_text(evidence: list[dict]) -> str:
    lines = [
        f'- {e["subject"]} {e["predicate"]} {e["object"]}'
        for e in evidence
    ]
    return "\n".join(lines)


def _user_prompt(question: str, evidence: list[dict]) -> str:
    return (
        "<graph_relations>\n"
        f"{_evidence_to_text(evidence)}\n"
        "</graph_relations>\n\n"
        f"Question: {question}"
    )


def generate_answer(question: str, evidence: list[dict]) -> tuple[str, str]:
    client = ollama.Client(host=config.OLLAMA_HOST)
    extra = {}
    if config.MODEL.startswith(("qwen3", "deepseek-r1")):
        extra["think"] = False 
    response = client.chat(
        model=config.MODEL,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": _user_prompt(question, evidence)},
        ],
        **extra,
    )
    return response["message"]["content"].strip(), "ollama"
