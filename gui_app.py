"""
gui_app.py

Streamlit GUI for the Agentic Recommendation System. Run this to get complete system w ui
"""

import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv


# Load environment variables from .env
# Handle missing files and encoding issues gracefully
def safe_load_dotenv():
    """Safely load .env file, handling missing files and encoding issues."""
    from pathlib import Path

    env_file = Path(".env")

    # If .env doesn't exist, that's okay - user might set env vars directly
    if not env_file.exists():
        return False

    try:
        load_dotenv()
        return True
    except UnicodeDecodeError:
        # Try different encodings if UTF-8 fails
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        for encoding in encodings:
            try:
                load_dotenv(encoding=encoding)
                return True
            except (UnicodeDecodeError, Exception):
                continue
        # If all encodings fail, return False (user can set env vars directly)
        return False
    except Exception:
        # Any other error loading .env - continue without it
        return False


safe_load_dotenv()

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
            background: linear-gradient(180deg, #f5f7ff 0%, #ffffff 50%);
        }
        
        /* Main container spacing */
        .main-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 1rem;
        }

        /* Tweak headings */
        .main-title {
            font-weight: 700;
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            color: #0f172a;
        }
        
        /* Intro text spacing */
        .intro-text {
            margin-bottom: 2.5rem;
            color: #475569;
            font-size: 1.05rem;
            line-height: 1.7;
        }

        .subheader-text {
            color: #6c757d;
        }

        /* Cards for the mode selection */
        .mode-card {
            padding: 2rem 1.75rem;
            border-radius: 1.25rem;
            border: 1px solid rgba(200, 200, 200, 0.4);
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            box-shadow: 0 4px 20px rgba(15, 23, 42, 0.1), 0 1px 3px rgba(0, 0, 0, 0.05);
            margin-bottom: 1.5rem;
            transition: all 0.3s ease;
            height: 100%;
            display: flex;
            flex-direction: column;
        }
        .mode-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(15, 23, 42, 0.15), 0 2px 6px rgba(0, 0, 0, 0.08);
        }
        .mode-card h3 {
            margin-bottom: 0.75rem;
            margin-top: 0;
            font-size: 1.5rem;
            font-weight: 700;
            color: #1e293b;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .mode-card p {
            margin-bottom: 1rem;
            line-height: 1.6;
            color: #475569;
        }
        .mode-card ul {
            margin: 1rem 0 1.5rem 0;
            padding-left: 1.5rem;
            line-height: 1.8;
        }
        .mode-card li {
            margin-bottom: 0.5rem;
            color: #64748b;
        }
        .mode-card strong {
            color: #1e293b;
            font-weight: 600;
        }
        
        /* Button container spacing */
        .mode-card + button {
            margin-top: auto;
        }
        
        /* Section header spacing */
        .section-header {
            margin-bottom: 2rem;
            margin-top: 1.5rem;
        }
        
        /* Custom button styling for mode selection */
        .stButton > button {
            width: 100%;
            padding: 0.875rem 1.5rem;
            font-weight: 600;
            font-size: 1rem;
            border-radius: 0.75rem;
            transition: all 0.2s ease;
            border: none;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.1);
        }
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15);
        }
        
        /* Column gap for better spacing */
        .stColumn {
            padding: 0 0.75rem;
        }
        
        /* Remove default Streamlit spacing issues */
        .element-container {
            margin-bottom: 0;
        }
        
        /* Better spacing for mode selection area */
        .mode-selection-container {
            margin-top: 1rem;
            margin-bottom: 2rem;
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

        /* Team overview card (mirrors infographic vibe) */
        .team-card {
            margin-top: 0.8rem;
            padding: 1rem 1.2rem;
            border-radius: 1.1rem;
            border: 1px solid rgba(148, 163, 184, 0.45);
            background-color: rgba(255, 255, 255, 0.9);
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
        }
        .team-card-explainer {
            background: linear-gradient(135deg, #e0f2fe 0%, #eff6ff 100%);
            border-color: #bfdbfe;
        }
        .team-card-recommender {
            background: linear-gradient(135deg, #dcfce7 0%, #ecfdf5 100%);
            border-color: #bbf7d0;
        }
        .team-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 0.5rem;
            flex-wrap: wrap;
        }
        .team-title {
            font-weight: 600;
            font-size: 0.95rem;
        }
        .team-subtitle {
            font-size: 0.85rem;
            color: #6b7280;
        }
        .team-agents {
            margin-top: 0.55rem;
            display: flex;
            flex-wrap: wrap;
            gap: 0.35rem;
        }
        .agent-pill {
            display: inline-flex;
            align-items: center;
            padding: 0.2rem 0.6rem;
            border-radius: 999px;
            font-size: 0.78rem;
            background-color: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(148, 163, 184, 0.7);
            white-space: nowrap;
        }
        .agent-pill-manager {
            font-weight: 600;
            box-shadow: 0 0 0 1px rgba(37, 99, 235, 0.5);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_team_header(agent_mode):
    """
    Visual card showing the active team: Manager + 3 analysts.
    This is meant to mimic the infographic.
    """
    if agent_mode == "explainer":
        title = "Explainer Team"
        subtitle = "Q1 · Explain human analyst rating"
        extra_class = "team-card-explainer"
    else:
        title = "Recommender Team"
        subtitle = "Q2 · Model buy / hold / sell rating"
        extra_class = "team-card-recommender"

    st.markdown(
        f"""
        <div class="team-card {extra_class}">
            <div class="team-header">
                <div class="team-title">🏢 {title}</div>
                <div class="team-subtitle">{subtitle}</div>
            </div>
            <div class="team-agents">
                <span class="agent-pill agent-pill-manager">Manager</span>
                <span class="agent-pill">Fundamental Analyst</span>
                <span class="agent-pill">Technical Analyst</span>
                <span class="agent-pill">News &amp; Sentiment Analyst</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def split_manager_and_analysts(markdown_text):
    """
    Split a team markdown into manager summary vs analyst reports.

    Heuristics:
    - Prefer an explicit "# 📊 Individual Analyst Reports" marker.
    - Otherwise, split on the first analyst heading if we see one.
    - If nothing matches, treat everything as the manager report.
    """
    if not markdown_text:
        return "", None

    text = markdown_text.strip()
    marker = "# 📊 Individual Analyst Reports"

    if marker in text:
        head, tail = text.split(marker, 1)
        analyst_block = f"{marker}{tail}".strip()
        return head.strip(), analyst_block

    # Fallback: look for first analyst-style heading
    analyst_markers = [
        "## Fundamental Analyst",
        "## Fundamental Analyst Report",
        "## Technical Analyst",
        "## Technical Analyst Report",
        "## News & Sentiment Analyst",
        "## News & Sentiment Analyst Report",
    ]
    first_idx = len(text)
    found = False
    for m in analyst_markers:
        pos = text.find(m)
        if pos != -1:
            first_idx = min(first_idx, pos)
            found = True

    if found:
        manager_md = text[:first_idx].strip()
        analysts_md = text[first_idx:].strip()
        return manager_md, analysts_md

    # No clear split, everything is "manager"
    return text, None


def render_team_output(agent_mode, full_markdown, rating_str=None):
    """
    Show a short manager report first, with an expander
    to reveal the three analysts' detailed work.
    """
    manager_md, analysts_md = split_manager_and_analysts(full_markdown)

    if agent_mode == "explainer":
        title = "🔍 Explainer Manager Report"
    else:
        title = "🎯 Recommender Manager Report"

    st.markdown(f"### {title}")
    st.markdown(manager_md)

    # For the recommender, also show model vs human comparison inline
    if agent_mode == "recommender" and rating_str is not None:
        st.markdown("---")
        st.markdown("### 📊 Comparison: Model vs Human Analyst")
        col_model, col_human = st.columns(2)
        with col_model:
            st.markdown("**Model Rating:**")
            st.info("See the final rating in the manager report above ☝️")
        with col_human:
            st.markdown("**Human Analyst Rating (IBES):**")
            st.info(f"**{rating_str}**")

    if analysts_md:
        with st.expander("👥 View detailed work from the 3 analysts", expanded=False):
            st.markdown("#### 📊 Individual Analyst Reports")
            st.markdown(analysts_md)


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
    st.markdown(
        '<h1 class="main-title">Agentic Recommendation Explainer</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="intro-text">Interactively explore IBES analyst recommendations and generate '
        '<strong>LLM-based explanations</strong> or <strong>model-driven recommendations</strong> using '
        'Gemini-powered agents. Built for <em>Agentic AI, The Data Economy & Fintech</em>.</p>',
        unsafe_allow_html=True,
    )

    # --- API key check -----------------------------------------------------
    api_key = (
        os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or st.secrets.get("GEMINI_API_KEY", None)
    )
    if not api_key:
        from pathlib import Path

        env_example_exists = Path(".env.example").exists()

        error_msg = (
            "**No Gemini API key found.**\n\n"
            "To fix this:\n\n"
            "1. **Create a `.env` file** in the project root\n"
        )

        if env_example_exists:
            error_msg += (
                "   - Copy `.env.example` to `.env`\n"
                "   - Replace `your_api_key_here` with your actual API key\n\n"
            )
        else:
            error_msg += "   - Add this line: `GEMINI_API_KEY=your_key_here`\n\n"

        error_msg += (
            "2. **Get your free API key** from: "
            "[https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)\n\n"
            "**Alternative:** Set the environment variable directly:\n"
            "- Windows PowerShell: `$env:GEMINI_API_KEY='your_key'`\n"
            "- Mac/Linux: `export GEMINI_API_KEY='your_key'`\n"
        )

        st.error(error_msg)
        st.stop()

    # --- Step 1: Mode selection screen -------------------------------------
    if st.session_state.agent_mode is None:
        st.markdown(
            '<div class="section-header">'
            '<h2 style="font-size: 1.5rem; font-weight: 600; color: #1e293b; margin-bottom: 0.5rem;">'
            '1️⃣ Choose what you want the system to do'
            '</h2>'
            '</div>',
            unsafe_allow_html=True,
        )

        left_col, right_col = st.columns(2, gap="large")

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
            st.markdown('<div style="margin-top: 1.5rem;"></div>', unsafe_allow_html=True)
            if st.button(
                "Use Explainer", use_container_width=True, key="explainer_select", type="primary"
            ):
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
            st.markdown('<div style="margin-top: 1.5rem;"></div>', unsafe_allow_html=True)
            if st.button(
                "Use Recommender", use_container_width=True, key="recommender_select", type="primary"
            ):
                st.session_state.agent_mode = "recommender"
                st.rerun()

        st.markdown(
            '<p style="margin-top: 2rem; color: #64748b; font-size: 0.95rem; text-align: center; '
            'padding: 1rem; background: rgba(241, 245, 249, 0.5); border-radius: 0.75rem;">'
            'Once you choose a mode, you\'ll be able to pick a ticker, '
            'a specific IBES recommendation, and generate the output.'
            '</p>',
            unsafe_allow_html=True,
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
    mode_label = (
        "Explainer: Explain analyst rating"
        if agent_mode == "explainer"
        else "Recommender: Model's own rating"
    )
    st.markdown(
        f'<div class="mode-badge">{mode_label}</div>', unsafe_allow_html=True
    )

    # visual team card (manager + 3 analysts)
    render_team_header(agent_mode)

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
            unsafe_allow_html=True,
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

    # --- Step 5: Data context ----------------------------------------------
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
        "Click the button below to run the selected team. "
        "The manager's short report will appear first, with detailed analyst "
        "reports available behind a toggle."
    )

    if agent_mode == "explainer":
        # ===================================================================
        # EXPLAINER MODE
        # ===================================================================
        if st.button("🔍 Run Explainer Team", key="explainer_btn", type="primary"):
            with st.spinner(
                "Explainer Manager is collecting reports from the 3 analysts..."
            ):
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
                    st.success("✅ Explainer team finished. Manager report ready.")
                    st.markdown("---")
                    render_team_output(
                        agent_mode="explainer",
                        full_markdown=explanation_md,
                        rating_str=rating_str,  # not used in explainer but ok
                    )

    elif agent_mode == "recommender":
        # ===================================================================
        # RECOMMENDER MODE
        # ===================================================================
        if st.button("📊 Run Recommender Team", key="recommender_btn", type="primary"):
            cusip_val = rec_series.get("cusip", None)
            rec_date_val = rec_series.get("anndats", None)

            if pd.isna(cusip_val) or pd.isna(rec_date_val):
                st.error(
                    "CUSIP or recommendation date is missing for this IBES row; "
                    "cannot run the multi-analyst recommender."
                )
            else:
                with st.spinner(
                    "Recommender Manager is aggregating analyst views..."
                ):
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
                        st.success(
                            "✅ Recommender team finished. Manager report ready."
                        )
                        st.markdown("---")
                        render_team_output(
                            agent_mode="recommender",
                            full_markdown=reco_md,
                            rating_str=rating_str,
                        )


if __name__ == "__main__":
    main()
