"""
gui_app.py

A simple Streamlit GUI for your Agentic Recommendation Explainer.

What it does:
- Loads IBES, FUND, NEWS data.
- Lets you pick a ticker and a specific IBES recommendation.
- Builds the context for that recommendation.
- Runs the Explainer Crew (Gemini) and shows the markdown explanation.
"""

import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from data_loader import load_datasets, build_context_for_rec
from crew_config import create_explainer_crew


# Load environment variables from .env (for GEMINI_API_KEY / GOOGLE_API_KEY)
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
        page_title="Agentic Recommendation Explainer",
        layout="wide",
    )

    st.title("📈 Agentic Recommendation Explainer (Gemini + CrewAI)")
    st.write(
        "Interactively explore IBES analyst recommendations and generate "
        "LLM-based explanations using your Gemini-powered Explainer agent."
    )

    # Check API keys
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error(
            "No Gemini API key found.\n\n"
            "Please set `GEMINI_API_KEY` or `GOOGLE_API_KEY` in your `.env` file.\n\n"
            "Example:\n"
            "```text\n"
            "GEMINI_API_KEY=your_key_here\n"
            "```"
        )
        st.stop()

    # Load data
    ibes, fund, news = get_datasets()

    st.sidebar.header("Dataset Overview")
    st.sidebar.write(f"**IBES rows:** {len(ibes)}")
    st.sidebar.write(f"**FUND rows:** {len(fund)}")
    st.sidebar.write(f"**NEWS rows:** {len(news)}")

    # --- Sidebar controls: choose ticker and recommendation ---

    st.sidebar.header("Selection")

    # All available tickers
    all_tickers = sorted(ibes["ticker"].dropna().unique().tolist())

    # Default to AMZN if present, else first ticker
    default_ticker_index = 0
    if "AMZN" in all_tickers:
        default_ticker_index = all_tickers.index("AMZN")

    selected_ticker = st.sidebar.selectbox(
        "Choose ticker:",
        all_tickers,
        index=default_ticker_index,
    )

    # Filter IBES rows for that ticker
    ibes_ticker = ibes[ibes["ticker"] == selected_ticker].copy()

    if ibes_ticker.empty:
        st.error(f"No IBES recommendations found for ticker {selected_ticker}.")
        st.stop()

    # Build a nice label for each recommendation
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

    # Parse the global IBES index from the label (before the first " | ")
    selected_rec_index = int(selected_label.split(" | ")[0])

    # Window sizes
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

    # --- Main area: show selected IBES row and context ---

    st.subheader("1️⃣ Selected IBES Recommendation")

    rec_series = ibes.loc[selected_rec_index]

    cols = st.columns(4)

    # Force everything to plain strings before passing to st.metric
    ticker_str = str(rec_series.get("ticker", "N/A"))
    company_str = str(rec_series.get("cname", "N/A"))

    rec_date_val = rec_series.get("anndats", None)
    if pd.notna(rec_date_val):
        # convert to "YYYY-MM-DD" string
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

    st.subheader("2️⃣ Context (IBES + FUND + NEWS)")

    # Build context string for this rec
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

    # --- Run Explainer agent ---

    st.subheader("3️⃣ Run Explainer Agent")

    st.write(
        "Click the button to run the Gemini-powered Explainer on the context above. "
        "This may take a few seconds."
    )

    if st.button("🔍 Generate Explanation"):
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


if __name__ == "__main__":
    main()
