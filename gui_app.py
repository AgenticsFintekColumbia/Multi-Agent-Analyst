"""
gui_app.py

A Streamlit GUI for the Agentic Recommendation Explainer system.

Features:
- Load IBES, FUND, NEWS data.
- Pick a ticker and specific IBES recommendation.
- Build the context around that recommendation.
- Run either:
  - Explainer agent (why did analyst give this rating?), or
  - Recommender agent (what rating would the model give?), or both.
"""

import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from data_loader import load_datasets, build_context_for_rec
from crew_config import create_explainer_crew, create_recommender_crew


# Load environment variables from .env (for local dev)
load_dotenv()


@st.cache_data(show_spinner="Loading datasets...")
def get_datasets():
    """
    Cached wrapper around load_datasets() so we don't reload
    the feather files on every interaction.
    """
    ibes, fund, news = load_datasets(data_dir="data/")
    return ibes, fund, news


def main():
    # Basic page config
    st.set_page_config(
        page_title="Agentic Recommendation Explainer (Gemini + CrewAI)",
        layout="wide",
    )

    st.title("📈 Agentic Recommendation Explainer (Gemini + CrewAI)")
    st.write(
        "Interactively explore IBES analyst recommendations and generate "
        "LLM-based explanations and model recommendations using your "
        "Gemini-powered agents."
    )

    # --- API key check ---

    api_key = (
        os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or st.secrets.get("GEMINI_API_KEY", None)
    )
    if not api_key:
        st.error(
            "No Gemini API key found.\n\n"
            "Please set `GEMINI_API_KEY` or `GOOGLE_API_KEY` in your `.env` file, "
            "or define `GEMINI_API_KEY` in Streamlit secrets.\n\n"
            "Example `.env` entry:\n"
            "```text\n"
            "GEMINI_API_KEY=your_key_here\n"
            "```"
        )
        st.stop()

    # --- Load data ---

    ibes, fund, news = get_datasets()

    # Sidebar: dataset overview
    st.sidebar.header("Dataset Overview")
    st.sidebar.write(f"**IBES rows:** {len(ibes)}")
    st.sidebar.write(f"**FUND rows:** {len(fund)}")
    st.sidebar.write(f"**NEWS rows:** {len(news)}")

    # Sidebar: agent mode selection
    st.sidebar.header("Agent Selection")
    agent_mode = st.sidebar.radio(
        "Choose agent mode:",
        [
            "Explainer: Explain analyst rating",
            "Recommender: Model's own rating",
            "Both: Run Explainer and Recommender",
        ],
        index=0,
    )

    # Sidebar: ticker & recommendation selection
    st.sidebar.header("Selection")

    all_tickers = sorted(ibes["ticker"].dropna().unique().tolist())

    default_ticker_index = 0
    if "AMZN" in all_tickers:
        default_ticker_index = all_tickers.index("AMZN")

    selected_ticker = st.sidebar.selectbox(
        "Choose ticker:",
        all_tickers,
        index=default_ticker_index,
    )

    ibes_ticker = ibes[ibes["ticker"] == selected_ticker].copy()

    if ibes_ticker.empty:
        st.error(f"No IBES recommendations found for ticker {selected_ticker}.")
        st.stop()

    # Build labels for each rec of this ticker
    option_labels = []
    option_indices = []
    for idx, row in ibes_ticker.iterrows():
        date = row["anndats"].date() if pd.notna(row["anndats"]) else "N/A"
        rating = row.get("etext", "N/A")
        analyst = str(row.get("analyst", "N/A")).strip()
        label = f"{idx} | {date} | {rating} | {analyst}"
        option_labels.append(label)
        option_indices.append(idx)

    selected_label = st.sidebar.selectbox(
        "Choose a specific recommendation:",
        option_labels,
    )

    selected_rec_index = int(selected_label.split(" | ")[0])

    # Window sliders
    fund_window_days = st.sidebar.slider(
        "FUND window (days before rec date):",
        min_value=7,
        max_value=90,
        value=30,
        step=1,
    )
    news_window_days = st.sidebar.slider(
        "NEWS window (± days around rec date):",
        min_value=1,
        max_value=30,
        value=7,
        step=1,
    )

    # --- Main: selected IBES rec ---

    st.subheader("1️⃣ Selected IBES Recommendation")

    rec_series = ibes.loc[selected_rec_index]

    cols = st.columns(4)

    # Convert everything to string for st.metric
    ticker_str = str(rec_series.get("ticker", "N/A"))
    company_str = str(rec_series.get("cname", "N/A"))

    rec_date_val = rec_series.get("anndats", None)
    if pd.notna(rec_date_val):
        rec_date_str = rec_date_val.strftime("%Y-%m-%d")
    else:
        rec_date_str = "N/A"

    rating_str = str(rec_series.get("etext", "N/A"))

    cols[0].metric("Ticker", ticker_str)
    cols[1].metric("Company", company_str)
    cols[2].metric("Recommendation Date", rec_date_str)
    cols[3].metric("IBES Rating (etext)", rating_str)

    with st.expander("Show full IBES row"):
        st.write(rec_series.to_dict())

    # --- Main: context ---

    st.subheader("2️⃣ Context (IBES + FUND + NEWS)")

    context_str, _ = build_context_for_rec(
        ibes=ibes,
        fund=fund,
        news=news,
        rec_index=selected_rec_index,
        fund_window_days=fund_window_days,
        news_window_days=news_window_days,
    )

    with st.expander("Show raw context string", expanded=False):
        st.text(context_str)

    # --- Main: run agent(s) ---

    st.subheader("3️⃣ Run Agent(s)")

    st.write(
        "Choose which agent to run based on the sidebar selection. "
        "The Explainer justifies the analyst's rating; the Recommender issues "
        "its own rating."
    )

    # Explainer option
    if agent_mode in [
        "Explainer: Explain analyst rating",
        "Both: Run Explainer and Recommender",
    ]:
        if st.button("🔍 Generate Explanation", key="explainer_btn"):
            with st.spinner("Running Explainer Agent with Gemini..."):
                try:
                    crew = create_explainer_crew(context_str)
                    explanation_md = crew.kickoff()
                except Exception as e:
                    st.error(f"Error running Explainer agent: {type(e).__name__}: {e}")
                else:
                    st.success("Explanation generated successfully!")
                    st.markdown("---")
                    st.markdown("### 📄 Explainer Output (Markdown)")
                    st.markdown(explanation_md)

    # Recommender option
    if agent_mode in [
        "Recommender: Model's own rating",
        "Both: Run Explainer and Recommender",
    ]:
        if st.button("📊 Generate Model Recommendation", key="recommender_btn"):
            with st.spinner("Running Recommender Agent with Gemini..."):
                try:
                    crew = create_recommender_crew(context_str)
                    reco_md = crew.kickoff()
                except Exception as e:
                    st.error(f"Error running Recommender agent: {type(e).__name__}: {e}")
                else:
                    st.success("Model recommendation generated successfully!")
                    st.markdown("---")
                    st.markdown("### 🧮 Model Recommendation (Markdown)")
                    st.markdown(reco_md)

                    # Optional: show IBES vs model rating side-by-side as text
                    st.markdown("#### IBES vs Model (quick view)")
                    st.write(f"- **IBES rating (etext):** {rating_str}")
                    st.write(
                        "- **Model rating:** (see `Model rating:` line in the markdown above)"
                    )


if __name__ == "__main__":
    main()
