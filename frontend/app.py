"""
Module 9: Frontend
Streamlit app for demoing the system, including an agent trace viewer
that makes the context-engineering behavior visible for grading/demo.
"""
import streamlit as st
import requests

API_URL = "http://localhost:8000"

st.set_page_config(page_title="RegTech Multi-Agent System", layout="wide")
st.title("RBI/SEBI Regulatory Change-Impact Analyzer")

with st.sidebar:
    st.header("Query")
    doc_topic = st.text_input("Document topic (e.g. 'kyc')", value="kyc")
    query = st.text_area(
        "Your question",
        value="What changed in this circular and does it affect our current policy?",
    )
    submit = st.button("Analyze", type="primary")

if submit:
    with st.spinner("Running multi-agent analysis..."):
        try:
            response = requests.post(
                f"{API_URL}/analyze",
                json={"doc_topic": doc_topic, "query": query},
                timeout=120,
            )
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {e}")
            st.stop()

    tab1, tab2, tab3 = st.tabs(["Final Memo", "Structured Results", "Agent Trace"])

    with tab1:
        st.markdown(result.get("final_memo", "No memo generated."))

    with tab2:
        st.subheader("Delta (Diff Agent output)")
        st.json(result.get("delta"))
        st.subheader("Evidence (Retrieval Agent output)")
        st.json(result.get("evidence"))
        st.subheader("Impact Assessment")
        st.json(result.get("impact_assessment"))

    with tab3:
        st.subheader("Orchestrator Execution Trace")
        st.caption("Shows exactly what each agent did and in what order — demonstrates the context-scoping and re-routing behavior.")
        for i, step in enumerate(result.get("trace", [])):
            st.markdown(f"**Step {i+1}: `{step['node']}`** — {step['note']}")
else:
    st.info("Enter a document topic and query in the sidebar, then click Analyze.")
