from __future__ import annotations

from src import config, neo4j_client

Q_GENES_OF_DISEASE = """
MATCH (d:Disease {id: $id})-[:DaG]->(g:Gene)
RETURN d.id AS d_id, d.name AS d_name,
       g.id AS g_id, g.name AS g_name
ORDER BY count {(g)--()} DESC, g.name
LIMIT $k
"""

Q_PROCESSES_OF_DISEASE = """
MATCH (d:Disease {id: $id})-[:DaG]->(g:Gene)
WITH d, g ORDER BY count {(g)--()} DESC, g.name LIMIT $k_genes
MATCH (g)-[:GpBP]->(b:BiologicalProcess)
WITH d, g, b ORDER BY b.name
WITH d, g, collect(b)[0..$k_bp] AS bps
UNWIND bps AS b
RETURN d.id AS d_id, d.name AS d_name,
       g.id AS g_id, g.name AS g_name,
       b.id AS b_id, b.name AS b_name
"""

Q_SHARED_GENES = """
MATCH (a:Disease {id: $id_a})-[:DaG]->(g:Gene)<-[:DaG]-(b:Disease {id: $id_b})
RETURN a.id AS a_id, a.name AS a_name,
       b.id AS b_id, b.name AS b_name,
       g.id AS g_id, g.name AS g_name
ORDER BY count {(g)--()} DESC, g.name
LIMIT $k
"""

Q_DISEASES_BY_SYMPTOM = """
MATCH (d:Disease)-[:DpS]->(s:Symptom {id: $id})
RETURN s.id AS s_id, s.name AS s_name,
       d.id AS d_id, d.name AS d_name
ORDER BY d.name
LIMIT $k
"""

Q_SYMPTOMS_OF_DISEASE = """
MATCH (d:Disease {id: $id})-[:DpS]->(s:Symptom)
RETURN d.id AS d_id, d.name AS d_name,
       s.id AS s_id, s.name AS s_name
ORDER BY count {(s)--()} DESC, s.name
LIMIT $k
"""

Q_DISEASES_BY_SYMPTOMS = """
MATCH (d:Disease)-[:DpS]->(m:Symptom)
WHERE m.id IN $ids
WITH d, count(DISTINCT m) AS matched
ORDER BY matched DESC, d.name
LIMIT $k
MATCH (d)-[:DpS]->(s:Symptom)
RETURN d.id AS d_id, d.name AS d_name, matched AS matched,
       s.id AS s_id, s.name AS s_name,
       (s.id IN $ids) AS informed
ORDER BY matched DESC, d.name, informed DESC, s.name
"""


def diseases_by_symptoms(symptom_ids: list[str], k: int | None = None) -> list[dict]:
    """Diseases presenting any of the symptoms, each with its full symptom list."""
    return neo4j_client.run_query(
        Q_DISEASES_BY_SYMPTOMS,
        ids=symptom_ids,
        k=k or config.MAX_NODES,
    )


def genes_of_disease(disease_id: str, k: int | None = None) -> list[dict]:
    return neo4j_client.run_query(
        Q_GENES_OF_DISEASE, id=disease_id, k=k or config.MAX_GENES
    )


def processes_of_disease(
    disease_id: str, k_genes: int | None = None, k_bp: int | None = None
) -> list[dict]:
    return neo4j_client.run_query(
        Q_PROCESSES_OF_DISEASE,
        id=disease_id,
        k_genes=k_genes or config.MAX_GENES,
        k_bp=k_bp or config.MAX_BP_PER_GENE,
    )


def shared_genes(id_a: str, id_b: str, k: int | None = None) -> list[dict]:
    return neo4j_client.run_query(
        Q_SHARED_GENES, id_a=id_a, id_b=id_b, k=k or config.MAX_GENES
    )


def diseases_by_symptom(symptom_id: str, k: int | None = None) -> list[dict]:
    return neo4j_client.run_query(
        Q_DISEASES_BY_SYMPTOM, id=symptom_id, k=k or config.MAX_NODES
    )


def symptoms_of_disease(disease_id: str, k: int | None = None) -> list[dict]:
    return neo4j_client.run_query(
        Q_SYMPTOMS_OF_DISEASE, id=disease_id, k=k or config.MAX_GENES
    )


