# app.py
import streamlit as st
import pandas as pd
from pandasai import SmartDataframe
from pandasai.llm.local_llm import LocalLLM

from Basketball.StandAloneBasketball.API.StatsHighestScoreNBA import StatsHighestScoreNBA
from Basketball.BasketballStatsData.statsResults import ResultLogger

st.set_page_config(page_title="NBA Stat Highlights Chat (Local LLM)", layout="wide")
st.title("🏀 NBA Stat Highlights — Chat with Your Stats")

# — Sidebar: Configuration
player = st.sidebar.number_input("Player ID", value=551768)
stat_key = st.sidebar.selectbox(
    "Stat to track",
    options=list(StatsHighestScoreNBA.STAT_LABELS.keys()),
    format_func=lambda k: StatsHighestScoreNBA.STAT_LABELS[k]
)
start_year = st.sidebar.number_input("Start Season", value=2020)
end_year = st.sidebar.number_input("End Season", value=2021)

if st.sidebar.button("📥 Fetch Data"):
    logger = ResultLogger(stat_key=stat_key, stat_labels=StatsHighestScoreNBA.STAT_LABELS)
    stats = StatsHighestScoreNBA()
    df = stats.get_highest_stat_df(player, stat_key, start_year, end_year, logger=logger)
    st.session_state["df"] = df
    st.success("✅ Data loaded!")

# — Require data to proceed
if "df" not in st.session_state or st.session_state["df"].empty:
    st.info("Load data with 'Fetch Data' to begin chatting.")
    st.stop()

df: pd.DataFrame = st.session_state["df"]
st.dataframe(df, use_container_width=True)

# — Prompt input and example guidance
st.markdown("### Ask anything about this dataset:")
st.caption(
    "e.g., **Which season had the lowest value?**  •  "
    "**Give me average value per season**  •  "
    "**Plot value over time**"
)
prompt = st.text_input("Your question:")

# — Chat logic powered by local LLM
if prompt:
    with st.spinner("🤖 Thinking…"):
        llm = LocalLLM(api_base="http://localhost:11434/v1", model="llama3")
        sdf = SmartDataframe(
            df,
            name="Stats",
            config={
                "llm": llm,
                "show_code": True,      # display the code generated
                "save_charts": True,    # enable chart plotting/saving
                "save_charts_path": ".", # save to working directory
            },
        )
        try:
            response = sdf.chat(prompt)
            st.markdown("**Generated Code:**")
            st.code(sdf.last_code_generated, language="python")
            st.markdown("**Result:**")
            st.write(response)

            # Display any saved charts
            import os
            charts_dir = os.path.join(".", "pandasai_exports", "charts")
            if os.path.isdir(charts_dir):
                for fname in os.listdir(charts_dir):
                    st.image(os.path.join(charts_dir, fname))
        except Exception as e:
            st.error(f"⚠️ Error during chat: {e}")
