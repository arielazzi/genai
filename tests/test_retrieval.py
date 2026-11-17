from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import intent, neo4j_client, pipeline, retrieval  

MS = "Disease::DOID:2377"       
PARKINSON = "Disease::DOID:14330"
BREAST = "Disease::DOID:1612"
HYPERTENSION = "Disease::DOID:10763"

_neo_ok = neo4j_client.ping()[0]
requires_neo4j = pytest.mark.skipif(not _neo_ok, reason="Neo4j indisponível (DBMS não iniciado)")

@requires_neo4j
def test_intent_genes_of_disease():
    it = intent.identify("Which genes are associated with multiple sclerosis?")
    assert it.kind == "genes_of_disease"
    assert it.diseases == [MS]

@requires_neo4j
def test_intent_processes_multihop():
    it = intent.identify("Which biological processes do the genes of Parkinson's disease participate in?")
    assert it.kind == "processes_of_disease"
    assert it.diseases == [PARKINSON]

@requires_neo4j
def test_intent_shared_genes():
    it = intent.identify("Which genes are associated with both breast cancer and hypertension?")
    assert it.kind == "shared_genes"
    assert set(it.diseases) == {BREAST, HYPERTENSION}

@requires_neo4j
def test_intent_out_of_scope():
    it = intent.identify("What is the capital of France?")
    assert it.kind == "out_of_scope"

@requires_neo4j
def test_intent_diseases_by_symptom():
    it = intent.identify("Which diseases present tremor as a symptom?")
    assert it.kind == "diseases_by_symptom"
    assert it.symptoms == ["Symptom::D014202"]  

@requires_neo4j
def test_intent_symptoms_of_disease():
    it = intent.identify("What symptoms does multiple sclerosis present?")
    assert it.kind == "symptoms_of_disease"
    assert it.diseases == [MS]


@requires_neo4j
def test_intent_diseases_by_multiple_symptoms():
    it = intent.identify("The patient presents tremor, sleep disorders and hallucinations. Which diseases?")
    assert it.kind == "diseases_by_symptoms"
    assert len(it.symptoms) == 3
    assert "Symptom::D014202" in it.symptoms  

@requires_neo4j
def test_genes_of_disease_ms():
    recs = retrieval.genes_of_disease(MS, k=200)
    genes = {r["g_name"] for r in recs}
    assert len(genes) == 150  
    assert {"STAT4", "TNF", "IL1B"} <= genes

@requires_neo4j
def test_processes_multihop_ms():
    recs = retrieval.processes_of_disease(MS, k_genes=5, k_bp=5)
    assert recs, "should retrieve biological processes"
    assert all("b_name" in r for r in recs)

@requires_neo4j
def test_shared_genes_ms_parkinson():
    recs = retrieval.shared_genes(MS, PARKINSON, k=50)
    genes = {r["g_name"] for r in recs}
    assert "APOE" in genes  
    assert len(genes) == 8  

@requires_neo4j
def test_diseases_by_symptom_sleep():
    recs = retrieval.diseases_by_symptom("Symptom::D012893", k=40)
    diseases = {r["d_name"] for r in recs}
    assert len(diseases) >= 5
    assert {"Parkinson's disease", "Alzheimer's disease"} <= diseases

@requires_neo4j
def test_diseases_by_symptom_tremor():
    recs = retrieval.diseases_by_symptom("Symptom::D014202", k=40)
    diseases = {r["d_name"] for r in recs}
    assert diseases == {"Parkinson's disease", "multiple sclerosis"}

@requires_neo4j
def test_diseases_by_symptoms_ranking():
    recs = retrieval.diseases_by_symptoms(
        ["Symptom::D014202", "Symptom::D012893", "Symptom::D006212"]
    )
    cov = {r["d_name"]: r["matched"] for r in recs}
    assert cov["Parkinson's disease"] == 3  
    assert any(v < 3 for v in cov.values())  
    
    informed_flags = {r["informed"] for r in recs}
    assert informed_flags == {True, False}


@requires_neo4j
def test_diseases_by_symptoms_full_coverage_leads():
    recs = retrieval.diseases_by_symptoms(["Symptom::D004487", "Symptom::D050177"])  
    top = {r["d_name"]: r["matched"] for r in recs}
    assert top.get("hypertension") == 2


@requires_neo4j
def test_symptoms_of_disease_ms():
    recs = retrieval.symptoms_of_disease(MS, k=20)
    symptoms = {r["s_name"] for r in recs}
    assert len(symptoms) == 20  
    recs_all = retrieval.symptoms_of_disease(MS, k=200)
    assert len({r["s_name"] for r in recs_all}) == 78

@requires_neo4j
def test_pipeline_abstains_out_of_scope():
    r = pipeline.answer_question("What is the population of São Leopoldo?")
    assert r["mode"]["llm"] == "abstencao"
    assert r["evidence"] == []

@requires_neo4j
def test_pipeline_answers_with_evidence():
    r = pipeline.answer_question("Which genes are associated with multiple sclerosis?")
    assert r["evidence"], "should have evidence"
    assert r["nodes"], "should have nodes in the subgraph"
    assert r["mode"]["llm"] in {"ollama", "demo"}

@requires_neo4j
def test_pipeline_diseases_by_symptom():
    r = pipeline.answer_question("Which diseases present tremor as a symptom?")
    assert r["intent"] == "diseases_by_symptom"
    assert r["evidence"], "should have DpS evidence"
    kinds = {n["kind"] for n in r["nodes"]}
    assert "Symptom" in kinds and "Disease" in kinds

def test_pipeline_abstains_without_data():
    r = pipeline.answer_question("Which genes are associated with multiple sclerosis?")
    assert r["mode"]["dados"] == "neo4j"
    assert r["mode"]["llm"] == "abstencao"
