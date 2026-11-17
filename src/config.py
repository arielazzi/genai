from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


DIR_DATA = ROOT / "data"
DIR_SUBSET = DIR_DATA / "subset"
FILE_NODES = DIR_SUBSET / "nodes.tsv"
FILE_EDGES = DIR_SUBSET / "edges.tsv"
FILE_PROVENANCE = DIR_SUBSET / "provenance.json"


NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")


OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL = os.getenv("MODEL", "qwen3:8b")


MAX_NODES = int(os.getenv("MAX_NODES", "40"))
MAX_GENES = int(os.getenv("MAX_GENES", "15"))
MAX_BP_PER_GENE = int(os.getenv("MAX_BP_POR_GENE", "6"))


SOURCE = "Hetionet v1.0"
SOURCE_URL = "https://het.io/"

TYPE_COLORS = {
    "Disease": "#E4572E",            
    "Gene": "#4C9AFF",               
    "BiologicalProcess": "#2EC4B6",  
    "Symptom": "#F6C945",            
}

PREDICATES = {
    "DaG": "associates with (gene)",
    "GpBP": "participates in (biological process)",
    "DrD": "resembles (disease)",
    "DpS": "presents (symptom)",
}

METAEDGE_DaG = "DaG"   
METAEDGE_GpBP = "GpBP"  
METAEDGE_DrD = "DrD"   
METAEDGE_DpS = "DpS"   
