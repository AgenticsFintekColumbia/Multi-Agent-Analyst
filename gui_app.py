"""
gui_app.py - UPDATED VERSION WITH MULTI-AGENT EXPLAINER

Replace your existing gui_app.py with this version.
The key changes are:
1. Import multi_explainer instead of crew_config for explainer
2. Update the explainer button logic to use run_multi_analyst_explainer
"""

import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from data_loader import load_datasets, build_context_for_rec
from multi_explainer import run_multi_analyst_explainer  # NEW IMPORT
from multi_recommender import run_multi_analyst_recommendation



@st.cache_data(show_spinner="Loading datasets...")
def get_datasets():
    """
    Cached wrapper around load_datasets() so we don't reload
    the feather files on every interaction.
    """
    ibes, fund, news = load_datasets(data_dir="data/")
    return ibes, fund, news


def main():


    st.title("Agentic Recommendation Explainer")
    st.write(
        "Interactively explore IBES analyst recommendations and generate "
        "LLM-based explanations and model recommendations using "
        "Gemini-powered agents. Agentic AI, The Data Economy & Fintech"
    )

    #api key check

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

    #load data

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

    #Sidebar: ticker & recommendation selection
    st.sidebar.header("Selection")

    #Prefer official ticker (oftic) when available, otherwise fall back to IBES ticker
    #Create a single "display_ticker" column for the dropdown
    ibes_ticker_map = ibes.copy()
    ibes_ticker_map["display_ticker"] = ibes_ticker_map["oftic"].fillna(ibes_ticker_map["ticker"])

    #Build the unique list of display tickers
    all_tickers = sorted(ibes_ticker_map["display_ticker"].dropna().unique().tolist())

    #Default to AMZN if present, else first ticker
    default_ticker_index = 0
    if "AMZN" in all_tickers:
        default_ticker_index = all_tickers.index("AMZN")

    selected_ticker = st.sidebar.selectbox(
        "Choose ticker (official when available):",
        all_tickers,
        index=default_ticker_index,
    )

    #Filter IBES rows where either oftic OR ticker matches the selected display ticker
    ibes_ticker = ibes[
        (ibes["oftic"] == selected_ticker) | (ibes["ticker"] == selected_ticker)
    ].copy()

    if ibes_ticker.empty:
        st.error(f"No IBES recommendations found for ticker {selected_ticker}.")
        st.stop()


    if ibes_ticker.empty:
        st.error(f"No IBES recommendations found for ticker {selected_ticker}.")
        st.stop()

    #Build labels for each rec of this ticker
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

    #Window sliders
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

    #main:selected ibes rec

    st.subheader("1️⃣ Selected IBES Recommendation")

    rec_series = ibes.loc[selected_rec_index]

    cols = st.columns(4)

    #Convert everything to string for st.metric
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

    #recheck this was from mismatch tickers due to ibes data, note if IBES ticker differs from official exchange ticker (oftic)
    official_ticker = rec_series.get("oftic", None)

    if pd.notna(official_ticker) and str(official_ticker) != ticker_str:
        st.caption(
            f"Note: IBES ticker code **{ticker_str}** differs from the official "
            f"exchange ticker **{official_ticker}** (`oftic`). "
            "This app uses the IBES ticker as the primary identifier."
        )


    with st.expander("Show full IBES row"):
        st.write(rec_series.to_dict())

    #main context

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

    #main: run agents

    st.subheader("3️⃣ Run Agent(s)")

    st.write(
        "Choose which agent to run based on the sidebar selection. "
        "The Explainer justifies the analyst's rating; the Recommender issues "
        "its own rating."
    )

    #=============================================================================
    # UPDATED: Multi-Agent Explainer option
    #=============================================================================
    if agent_mode in [
        "Explainer: Explain analyst rating",
        "Both: Run Explainer and Recommender",
    ]:
        if st.button("🔍 Generate Explanation (Multi-Agent)", key="explainer_btn"):
            with st.spinner("Running Multi-Agent Explainer Team with Gemini..."):
                try:
                    explanation_md = run_multi_analyst_explainer(
                        ibes_df=ibes,
                        fund_df=fund,
                        news_df=news,
                        rec_index=selected_rec_index,
                        fund_window_days=fund_window_days,
                        news_window_days=news_window_days,
                    )
                except Exception as e:
                    st.error(f"Error running Multi-Agent Explainer: {type(e).__name__}: {e}")
                    import traceback
                    st.text(traceback.format_exc())
                else:
                    st.success("Explanation generated successfully!")
                    st.markdown("---")
                    st.markdown("### 📄 Multi-Agent Explainer Output")
                    st.markdown(explanation_md)

    #Recommender option (multi-analyst)
    if agent_mode in [
        "Recommender: Model's own rating",
        "Both: Run Explainer and Recommender",
    ]:
        if st.button("📊 Generate Model Recommendation", key="recommender_btn"):
            cusip_val = rec_series.get("cusip", None)
            rec_date_val = rec_series.get("anndats", None)

            if pd.isna(cusip_val) or pd.isna(rec_date_val):
                st.error("CUSIP or recommendation date is missing for this IBES row; "
                         "cannot run the multi-analyst recommender.")
            else:
                with st.spinner("Running multi-analyst Recommender Team with Gemini..."):
                    try:
                        reco_md = run_multi_analyst_recommendation(
                            cusip=str(cusip_val),
                            rec_date=rec_date_val,
                            fund_df=fund,
                            news_df=news,
                            news_window_days=news_window_days,
                            ticker=ticker_str,
                            company=company_str,
                        )
                    except Exception as e:
                        st.error(
                            f"Error running multi-analyst Recommender agent: "
                            f"{type(e).__name__}: {e}"
                        )
                    else:
                        st.success("Model recommendation generated successfully!")
                        st.markdown("---")
                        st.markdown("### 🧮 Model Recommendation (Multi-Analyst)")
                        st.markdown(reco_md)

                        # Optional: quick IBES vs model note
                        st.markdown("#### IBES vs Model (quick view)")
                        st.write(f"- **IBES rating (etext):** {rating_str}")
                        st.write(
                            "- **Model rating:** see the final rating in the markdown above."
                        )


if __name__ == "__main__":
    main()