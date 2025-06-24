# app.py
import streamlit as st
import pandas as pd
from pandasai import SmartDataframe
from pandasai.llm.local_llm import LocalLLM
from Basketball.StandAloneBasketball.API.StatsHighestScoreNBA import StatsHighestScoreNBA
from Basketball.BasketballStatsData.statsResults import ResultLogger

st.set_page_config(page_title="NBA Stats Chat", page_icon="🏀", layout="wide")
st.title("🏀 NBA Stats Chat — Conditional Charts & Smart Context")

PLAYER_CHOICES = {
    "All Players": None,
    "LeBron James": 214152,
    "Stephen Curry": 338365,
    "Kevin Durant": 329525,
    "Kyrie Irving": 551768,
    "James Harden": 201935,
    "Giannis Antetokounmpo": 739957,
    "Luka Dončić": 1121277,
    "Joel Embiid": 794508,
    "Nikola Jokić": 830650
}

player_name = st.sidebar.selectbox("Player", options=list(PLAYER_CHOICES.keys()))
player_id = PLAYER_CHOICES[player_name]

stat_key = st.sidebar.selectbox(
    "Stat to track",
    options=list(StatsHighestScoreNBA.STAT_LABELS.keys()),
    format_func=lambda k: StatsHighestScoreNBA.STAT_LABELS[k]
)
start_year = st.sidebar.number_input("Start Season", min_value=2000, max_value=2100, value=2020)
end_year = st.sidebar.number_input("End Season", min_value=2000, max_value=2100, value=2021)
show_table = st.sidebar.checkbox("Show stats table", value=False)

if st.sidebar.button("Fetch Data"):
    logger = ResultLogger(stat_key=stat_key, stat_labels=StatsHighestScoreNBA.STAT_LABELS)
    stats = StatsHighestScoreNBA()
    combined_df = []

    # If "All Players" is selected
    selections = PLAYER_CHOICES.items() if player_id is None else [(player_name, player_id)]
    for name, pid in selections:
        logger.log_section(f"Fetching for {name} ({pid})")
        df = stats.get_highest_stat_df(pid, name, stat_key, start_year, end_year, logger=logger)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
        combined_df.append(df)

    full_df = pd.concat(combined_df, ignore_index=True)
    st.session_state["df"] = full_df
    st.success("✅ Data loaded")

if "df" not in st.session_state or st.session_state["df"].empty:
    st.info("Click ‘Fetch Data’ to load data, then ask a question.")
    st.stop()

df = st.session_state["df"]

if show_table:
    st.write("### Stats Table")
    st.dataframe(df, use_container_width=True)

st.markdown("### Ask a question:")
st.caption("e.g. 'On what date did LeBron scored his fewest points?' or 'Plot points over time across all players'")
prompt = st.text_input("Your question:")

def run_chat(prompt: str):
    ask_plot = any(w in prompt.lower() for w in ["plot", "chart", "graph", "visualize", "show"])
    df2 = df.copy()

    # Filter dataframe based on prompt intent
    key = prompt.lower()
    # Select only scalar columns
    if "date" in key:
        cols = ['player', 'date', 'value']
    elif "season" in key:
        cols = ['player', 'season', 'value']
    else:
        cols = ['player', 'value']

    df2 = df.loc[:, [c for c in cols if c in df.columns]]

    llm = LocalLLM(api_base="http://localhost:11434/v1", model="llama3")
    sdf = SmartDataframe(
        df2,
        name=f"{'All Players' if player_id is None else player_name} {StatsHighestScoreNBA.STAT_LABELS[stat_key]} Stats",
        config={
            "llm": llm,
            "show_code": False,
            "save_charts": ask_plot,
            "max_retries": 1,
            "enable_cache": True,
            "security": "standard"
        },
    )
    return sdf.chat(prompt)


if prompt:
    with st.spinner("🤖 Thinking…"):
        try:
            response = run_chat(prompt)
            if isinstance(response, dict) and response.get("type") == "plot":
                st.image(response["value"], use_container_width=True)
            else:
                answer = response.get("value") if isinstance(response, dict) else response
                st.markdown("**Answer:**")
                st.write(answer)
        except Exception as e:
            st.error(f"⚠️ Error: {e}")
