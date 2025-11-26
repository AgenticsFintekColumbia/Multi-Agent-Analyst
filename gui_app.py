"""
gui_app.py

Streamlit GUI for the Agentic Recommendation System. Run this to get complete system w ui

"""

import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Updated imports from new structure
from data_loader import load_datasets, build_context_for_rec
from src.explainer import run_multi_analyst_explainer
from src.recommender import run_multi_analyst_recommendation


@st.cache_data(show_spinner="Loading datasets...")
def get_datasets():
    """
    Cached wrapper around load_datasets() so we don't reload
    the feather files on every interaction.
    """
    ibes, fund, news = load_datasets(data_dir="data/")
    return ibes, fund, news


def inject_custom_css():
    """
    Light theming to make the app feel more polished.
    """
    st.markdown(
        """
        <style>
        /* Overall background */
        .stApp {
            background: linear-gradient(180deg, #f5f7ff 0%, #ffffff 40%);
        }

        /* Tweak headings */
        .main-title {
            font-weight: 700;
            font-size: 2.2rem;
        }

        .subheader-text {
            color: #6c757d;
        }

        /* Cards for the mode selection */
        .mode-card {
            padding: 1.5rem 1.2rem;
            border-radius: 1rem;
            border: 1px solid rgba(200, 200, 200, 0.6);
            background-color: rgba(255, 255, 255, 0.85);
            box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08);
            margin-bottom: 0.75rem;
        }
        .mode-card h3 {
            margin-bottom: 0.3rem;
        }
        .mode-card p {
            margin-bottom: 0.4rem;
        }

        /* Small mode badge */
        .mode-badge {
            display: inline-block;
            padding: 0.2rem 0.6rem;
            border-radius: 999px;
            border: 1px solid #cbd5e1;
            background-color: #e2e8f0;
            font-size: 0.8rem;
            font-weight: 500;
            color: #334155;
        }
        
        /* Warning badge for hidden info */
        .info-badge {
            display: inline-block;
            padding: 0.3rem 0.8rem;
            border-radius: 0.5rem;
            border: 1px solid #fbbf24;
            background-color: #fef3c7;
            font-size: 0.85rem;
            font-weight: 500;
            color: #92400e;
            margin-top: 0.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main():
    st.set_page_config(
        page_title="Agentic Stock Explainer & Recommender",
        page_icon="📈",
        layout="wide",
    )

    inject_custom_css()

    # Initialise mode in session state
    if "agent_mode" not in st.session_state:
        st.session_state.agent_mode = None  # "explainer" or "recommender"

    # --- Title & intro -----------------------------------------------------
    st.markdown('<h1 class="main-title">Agentic Recommendation Explainer</h1>', unsafe_allow_html=True)
    st.write(
        "Interactively explore IBES analyst recommendations and generate "
        "**LLM-based explanations** or **model-driven recommendations** using "
        "Gemini-powered agents. Built for *Agentic AI, The Data Economy & Fintech*."
    )

    # --- API key check -----------------------------------------------------
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

    # --- Step 1: Mode selection screen -------------------------------------
    if st.session_state.agent_mode is None:
        st.markdown("### 1️⃣ Choose what you want the system to do")

        left_col, right_col = st.columns(2)

        with left_col:
            st.markdown(
                """
                <div class="mode-card">
                    <h3>🔍 Explainer</h3>
                    <p class="subheader-text">
                        Justify the <strong>human analyst's rating</strong> based on IBES, FUND, and NEWS context.
                    </p>
                    <ul>
                        <li>Decomposes signals from fundamentals, price moves, and headlines</li>
                        <li>Focuses on <strong>Q1: Explain Analyst Rating</strong></li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Use Explainer", use_container_width=True, key="explainer_select"):
                st.session_state.agent_mode = "explainer"
                st.rerun()

        with right_col:
            st.markdown(
                """
                <div class="mode-card">
                    <h3>📊 Recommender</h3>
                    <p class="subheader-text">
                        Issue the <strong>model's own recommendation</strong> using multi-analyst signals.
                    </p>
                    <ul>
                        <li>Uses price action & news around the rec date</li>
                        <li>Focuses on <strong>Q2: Model Rating</strong></li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Use Recommender", use_container_width=True, key="recommender_select"):
                st.session_state.agent_mode = "recommender"
                st.rerun()

        st.markdown(
            "Once you choose a mode, you'll be able to pick a ticker, "
            "a specific IBES recommendation, and generate the output."
        )
        # Stop here on the landing screen
        st.stop()

    # --- If we get here, a mode has been selected --------------------------
    agent_mode = st.session_state.agent_mode

    # Load data only after mode is chosen
    ibes, fund, news = get_datasets()

    # Sidebar: dataset overview & mode badge
    st.sidebar.header("Dataset Overview")
    st.sidebar.write(f"**IBES rows:** {len(ibes)}")
    st.sidebar.write(f"**FUND rows:** {len(fund)}")
    st.sidebar.write(f"**NEWS rows:** {len(news)}")

    st.sidebar.markdown("---")
    sidebar_mode_label = "🔍 Explainer" if agent_mode == "explainer" else "📊 Recommender"
    st.sidebar.markdown(f"**Current Mode:** {sidebar_mode_label}")
    if st.sidebar.button("⬅️ Back to mode selection"):
        st.session_state.agent_mode = None
        st.rerun()

    # Mode badge under the title
    mode_label = "Explainer: Explain analyst rating" if agent_mode == "explainer" else "Recommender: Model's own rating"
    st.markdown(f'<div class="mode-badge">{mode_label}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # --- Step 2: Ticker & recommendation selection -------------------------
    st.subheader("1️⃣ Choose ticker & recommendation date")

    # Prefer official ticker (oftic) when available, otherwise fall back to IBES ticker
    ibes_ticker_map = ibes.copy()
    ibes_ticker_map["display_ticker"] = ibes_ticker_map["oftic"].fillna(
        ibes_ticker_map["ticker"]
    )

    # Build the unique list of display tickers
    all_tickers = sorted(ibes_ticker_map["display_ticker"].dropna().unique().tolist())

    # Default to AMZN if present, else first ticker
    default_ticker_index = 0
    if "AMZN" in all_tickers:
        default_ticker_index = all_tickers.index("AMZN")

    col_ticker, col_rec = st.columns([1, 2])

    with col_ticker:
        selected_ticker = st.selectbox(
            "Ticker (official when available):",
            all_tickers,
            index=default_ticker_index,
        )

    # Filter IBES rows where either oftic OR ticker matches the selected display ticker
    ibes_ticker = ibes[
        (ibes["oftic"] == selected_ticker) | (ibes["ticker"] == selected_ticker)
    ].copy()

    if ibes_ticker.empty:
        st.error(f"No IBES recommendations found for ticker {selected_ticker}.")
        st.stop()

    # Build labels for each rec - DIFFERENT for Explainer vs Recommender
    option_labels = []
    option_indices = []
    
    for idx, row in ibes_ticker.iterrows():
        date = row["anndats"].date() if pd.notna(row["anndats"]) else "N/A"
        analyst = str(row.get("analyst", "N/A")).strip()
        
        if agent_mode == "explainer":
            # Show rating for Explainer (we're explaining it)
            rating = row.get("etext", "N/A")
            label = f"{idx} | {date} | {rating} | {analyst}"
        else:
            # Hide rating for Recommender (avoid bias)
            label = f"{idx} | {date} | {analyst}"
        
        option_labels.append(label)
        option_indices.append(idx)

    with col_rec:
        if agent_mode == "explainer":
            select_label = "Specific IBES recommendation:"
        else:
            select_label = "Recommendation date & analyst:"
        
        selected_label = st.selectbox(select_label, option_labels)

    selected_rec_index = int(selected_label.split(" | ")[0])
    rec_series = ibes.loc[selected_rec_index]

    # Show info badge for Recommender mode
    if agent_mode == "recommender":
        st.markdown(
            '<div class="info-badge">ℹ️ Human analyst rating is hidden to avoid bias in model recommendations</div>',
            unsafe_allow_html=True
        )

    st.markdown("---")

    # --- Step 3: Window settings -------------------------------------------
    st.subheader("2️⃣ Set context windows")

    col_fund, col_news = st.columns(2)
    with col_fund:
        fund_window_days = st.slider(
            "FUND window (days before rec date):",
            min_value=7,
            max_value=90,
            value=30,
            step=1,
        )
    with col_news:
        news_window_days = st.slider(
            "NEWS window (± days around rec date):",
            min_value=1,
            max_value=30,
            value=7,
            step=1,
        )

    st.markdown("---")

    # --- Step 4: Show selected info (DIFFERENT for each mode) -------------
    st.subheader("3️⃣ Selected recommendation details")

    # Convert to strings
    ticker_str = str(rec_series.get("ticker", "N/A"))
    company_str = str(rec_series.get("cname", "N/A"))
    rec_date_val = rec_series.get("anndats", None)
    if pd.notna(rec_date_val):
        rec_date_str = rec_date_val.strftime("%Y-%m-%d")
    else:
        rec_date_str = "N/A"
    rating_str = str(rec_series.get("etext", "N/A"))

    if agent_mode == "explainer":
        # Show full info including rating for Explainer
        cols = st.columns(4)
        cols[0].metric("Ticker", ticker_str)
        cols[1].metric("Company", company_str)
        cols[2].metric("Recommendation Date", rec_date_str)
        cols[3].metric("IBES Rating (etext)", rating_str)
    else:
        # Hide rating for Recommender
        cols = st.columns(3)
        cols[0].metric("Ticker", ticker_str)
        cols[1].metric("Company", company_str)
        cols[2].metric("Recommendation Date", rec_date_str)

    # Note if IBES ticker differs from official exchange ticker (oftic)
    official_ticker = rec_series.get("oftic", None)
    if pd.notna(official_ticker) and str(official_ticker) != ticker_str:
        st.caption(
            f"Note: IBES ticker code **{ticker_str}** differs from the official "
            f"exchange ticker **{official_ticker}** (`oftic`). "
            "This app uses the IBES ticker as the primary identifier."
        )

    with st.expander("Show full IBES row (technical details)"):
        st.write(rec_series.to_dict())

    # --- Step 5: Context (optional expandable) -----------------------------
    st.subheader("4️⃣ Data context")

    context_str, _ = build_context_for_rec(
        ibes=ibes,
        fund=fund,
        news=news,
        rec_index=selected_rec_index,
        fund_window_days=fund_window_days,
        news_window_days=news_window_days,
    )

    with st.expander("📊 Show data context (IBES + FUND + NEWS)", expanded=False):
        st.text(context_str)

    st.markdown("---")

    # --- Step 6: Run the chosen agent -------------------------------------
    st.subheader("5️⃣ Generate output")

    st.write(
        "Click the button below to run the selected agent. "
        "The output will show the final result first, with detailed analyst reports available below."
    )

    if agent_mode == "explainer":
        # ===================================================================
        # EXPLAINER MODE
        # ===================================================================
        if st.button("🔍 Generate Explanation", key="explainer_btn", type="primary"):
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
                    st.error(
                        f"Error running Multi-Agent Explainer: {type(e).__name__}: {e}"
                    )
                    import traceback
                    st.text(traceback.format_exc())
                else:
                    st.success("✅ Explanation generated successfully!")
                    st.markdown("---")
                    
                    # Show the full explanation in main area
                    st.markdown("### 📄 Explanation Output")
                    st.markdown(explanation_md)
                    
                    # Optional: Add expandable for specialist reports if needed
                    # (Currently the explanation already includes all details)

    elif agent_mode == "recommender":
        # ===================================================================
        # RECOMMENDER MODE
        # ===================================================================
        if st.button("📊 Generate Model Recommendation", key="recommender_btn", type="primary"):
            cusip_val = rec_series.get("cusip", None)
            rec_date_val = rec_series.get("anndats", None)

            if pd.isna(cusip_val) or pd.isna(rec_date_val):
                st.error(
                    "CUSIP or recommendation date is missing for this IBES row; "
                    "cannot run the multi-analyst recommender."
                )
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
                            f"Error running multi-analyst Recommender: "
                            f"{type(e).__name__}: {e}"
                        )
                    else:
                        st.success("✅ Model recommendation generated successfully!")
                        st.markdown("---")
                        
                        # Parse the markdown to extract sections
                        # The format from multi_recommender.py is:
                        # 1. Header info
                        # 2. Final recommendation (## Model Recommendation (Final))
                        # 3. Individual analyst reports (# 📊 Individual Analyst Reports)
                        
                        sections = reco_md.split("# 📊 Individual Analyst Reports")
                        
                        if len(sections) == 2:
                            main_output = sections[0]
                            analyst_reports = sections[1]
                            
                            # Show main output (final recommendation)
                            st.markdown("### 🎯 Final Model Recommendation")
                            st.markdown(main_output)
                            
                            st.markdown("---")
                            
                            # Show comparison with human analyst (now that model is done)
                            st.markdown("### 📊 Comparison: Model vs Human Analyst")
                            
                            col_model, col_human = st.columns(2)
                            
                            with col_model:
                                st.markdown("**Model Rating:**")
                                st.info("See final rating in the recommendation above ☝️")
                            
                            with col_human:
                                st.markdown("**Human Analyst Rating (IBES):**")
                                st.info(f"**{rating_str}**")
                            
                            # Expandable detailed analyst reports
                            with st.expander("🔬 Show detailed analyst reports", expanded=False):
                                st.markdown("# 📊 Individual Analyst Reports")
                                st.markdown(analyst_reports)
                        
                        else:
                            # Fallback if format is different
                            st.markdown("### 🧮 Model Recommendation")
                            st.markdown(reco_md)
                            
                            # Show human rating comparison
                            st.markdown("---")
                            st.markdown("#### 📊 Human Analyst Rating (IBES)")
                            st.info(f"**{rating_str}**")


if __name__ == "__main__":
    main()