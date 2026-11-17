from __future__ import annotations

import sys
from pathlib import Path
import base64
import streamlit as st
from st_link_analysis import EdgeStyle, NodeStyle, st_link_analysis

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src import config, graph_context, pipeline

st.set_page_config(page_title="BioGraph AI", layout="wide")

NODE_STYLES = [
    NodeStyle("Disease", config.TYPE_COLORS["Disease"], "name"),
    NodeStyle("Gene", config.TYPE_COLORS["Gene"], "name"),
    NodeStyle("BiologicalProcess", config.TYPE_COLORS["BiologicalProcess"], "name"),
    NodeStyle("Symptom", config.TYPE_COLORS["Symptom"], "name"),
]
EDGE_STYLES = [
    EdgeStyle("DaG", color="#9AA5B1", directed=True),
    EdgeStyle("GpBP", color="#9AA5B1", directed=True),
    EdgeStyle("DrD", color="#9AA5B1", directed=True),
    EdgeStyle("DpS", color="#9AA5B1", directed=True),
]

GRAPH_LAYOUT = {
    "name": "cose",
    "animate": "end",
    "animationDuration": 500,
    "fit": True,
    "padding": 30,
    "nodeDimensionsIncludeLabels": True,
    "nodeRepulsion": 120000,
    "idealEdgeLength": 140,
    "edgeElasticity": 120,
    "gravity": 0.2,
    "numIter": 1500,
    "componentSpacing": 160,
}

def legend() -> None:
    items = " &nbsp; ".join(
        f'<span style="color:{color};font-size:20px">●</span> {name}'
        for name, color in [
            ("Disease", config.TYPE_COLORS["Disease"]),
            ("Gene", config.TYPE_COLORS["Gene"]),
            ("Biological Process", config.TYPE_COLORS["BiologicalProcess"]),
            ("Symptom", config.TYPE_COLORS["Symptom"]),
        ]
    )
    st.markdown(f"**Legend:** {items}", unsafe_allow_html=True)


def graph_panel(response: dict) -> None:
    nodes = response.get("nodes", [])
    if not nodes:
        st.info("No subgraph to display (question without evidence or out of scope).")
        return
    legend()
    elements = graph_context.to_cytoscape(response)
    graph_key = "graph_" + str(abs(hash(tuple(sorted(n["id"] for n in nodes)))))
    st_link_analysis(
        elements,
        layout=GRAPH_LAYOUT,
        node_styles=NODE_STYLES,
        edge_styles=EDGE_STYLES,
        height=275,
        key=graph_key,
    )
    _differential_panel(response)


def _differential_panel(response: dict) -> None:
    differential = response.get("differential")
    if not differential:
        return
    import pandas as pd

    st.markdown("#### Diseases matching the symptoms")
    rows = []
    for entry in differential:
        sintomas = ", ".join(
            f'{s["name"]}*' if s["informed"] else s["name"]
            for s in entry["symptoms"]
        )
        rows.append({"Disease": entry["disease"], "Symptoms in graph": sintomas})
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption("Symptoms you reported are marked with * — not a diagnosis.")


def evidence_panel(response: dict) -> None:
    ev = response.get("evidence", [])
    st.markdown("#### Evidence")
    if not ev:
        st.caption("No evidence retrieved for this question.")
    else:
        import pandas as pd

        df = pd.DataFrame(
            [
                {
                    "Subject": e["subject"],
                    "Predicate": e["predicate"],
                    "Object": e["object"],
                    "MetaEdge": e["hetionet_metaedge"],
                    "IDs (Hetionet)": ", ".join(e["source_ids"]),
                }
                for e in ev
            ]
        )
        st.dataframe(df, use_container_width=True, hide_index=True, height=240)
        st.caption(f"source: {config.SOURCE}: {config.SOURCE_URL}")

def process(question: str) -> None:
    with st.spinner("Querying the graph and drafting the answer..."):
        try:
            response = pipeline.answer_question(question)
        except Exception as error:
            response = {
                "answer": f"An error occurred while processing the question: {error}",
                "nodes": [], "links": [], "evidence": [],
                "intent": "error", "source": config.SOURCE,
                "mode": {"dados": "error", "llm": "error"},
                "limitations": [],
            }
    st.session_state.history.append({"question": question, "response": response})
    st.session_state.last = response


def brand_header() -> None:
    logo_b64 = base64.b64encode(
        (Path(__file__).resolve().parent / "image.png").read_bytes()
    ).decode("ascii")
    st.markdown(
        f"""
        <style>
          /* hide Streamlit's native header so our bar sits at the very top */
          header[data-testid="stHeader"] {{ display: none; }}
          /* fixed full-width top bar */
          .bg-topbar {{
              position: fixed; top: 0; left: 0; right: 0; z-index: 1000000;
              height: 56px; display: flex; align-items: center; gap: 0.6rem;
              padding: 0 1.3rem;
              background: #14171C; border-bottom: 1px solid #2A2F37;
          }}
          .bg-logo {{
              width: 34px; height: 34px; border-radius: 9px;
              object-fit: contain; background: #FFFFFF; padding: 3px;
              flex: 0 0 auto;
          }}
          .bg-name {{ font-size: 1.15rem; font-weight: 700; color: #E6E8EB;
                     letter-spacing: -0.01em; }}
          /* push content below the bar and drop the huge default bottom padding (10rem) */
          .stMainBlockContainer, .block-container {{
              padding-top: 4.4rem !important;
              padding-bottom: 1.5rem !important;
          }}
          /* remove padding from the chat history scroll container */
          div[data-test-scroll-behavior="scroll-to-bottom"] {{
              padding-bottom: 0 !important; padding-top: 0 !important; gap: 0 !important;
          }}
        </style>
        <div class="bg-topbar">
          <img class="bg-logo" src="data:image/png;base64,{logo_b64}" alt="BioGraph AI"/>
          <span class="bg-name">BioGraph AI</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    brand_header()

    st.session_state.setdefault("history", [])
    st.session_state.setdefault("last", None)

    left, right = st.columns([1, 2], gap="large")

    with left:
        st.markdown("### Assistant")

        if prompt := st.chat_input("Ask about a disease, genes or processes..."):
            process(prompt)

        if st.session_state.history:
            history_box = st.container(height=990, border=False)
            with history_box:
                for turn in reversed(st.session_state.history):
                    with st.chat_message("user"):
                        st.write(turn["question"])
                    with st.chat_message("assistant"):
                        r = turn["response"]
                        st.caption(f"intent: `{r['intent']}`")
                        st.markdown(r["answer"])

    with right:

        last = st.session_state.last
        if last is not None:
            st.markdown("### Subgraph")
            graph_panel(last)
            evidence_panel(last)

