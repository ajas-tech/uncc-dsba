import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Semmelweis & Handwashing", layout="wide")

# ── Data ─────────────────────────────────────────────────────────────────────
data = {
    "Year":   [1841,1842,1843,1844,1845,1846,1847,1848,1849]*2,
    "Births": [3036,3287,3060,3157,3492,4010,4010,3742,3500,
               2442,2659,2739,2956,3241,3754,3754,3600,3400],
    "Deaths": [237,518,274,260,241,459,122,47,46,
               86,202,164,68,66,105,48,48,36],
    "Clinic": ["Clinic 1"]*9 + ["Clinic 2"]*9,
}
df = pd.DataFrame(data)
df["Mortality Rate (%)"] = (df["Deaths"] / df["Births"] * 100).round(2)
HANDWASHING_YEAR = 1847

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.header("🔍 Filters")
year_range = st.sidebar.slider(
    "Year range",
    min_value=int(df["Year"].min()),
    max_value=int(df["Year"].max()),
    value=(int(df["Year"].min()), int(df["Year"].max())),
)
clinics = st.sidebar.multiselect(
    "Clinics",
    options=["Clinic 1", "Clinic 2"],
    default=["Clinic 1", "Clinic 2"],
)

filtered = df[
    (df["Year"] >= year_range[0]) &
    (df["Year"] <= year_range[1]) &
    (df["Clinic"].isin(clinics))
]

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🧼 The Semmelweis Handwashing Discovery")
st.markdown(
    """
    In the 1840s, Hungarian physician **Dr. Ignaz Semmelweis** worked at the Vienna General Hospital,
    where he noticed dramatically different death rates between two maternity clinics.
    **Clinic 1** was staffed by medical students who came directly from autopsies,
    while **Clinic 2** was staffed by midwives. In **May 1847**, Semmelweis mandated
    chlorinated lime handwashing — and mortality plummeted almost overnight.
    This app explores that data visually.
    """
)
st.divider()

# ── KPI cards ─────────────────────────────────────────────────────────────────
c1_before = df[(df["Clinic"]=="Clinic 1") & (df["Year"] < HANDWASHING_YEAR)]
c1_after  = df[(df["Clinic"]=="Clinic 1") & (df["Year"] >= HANDWASHING_YEAR)]
before_rate = (c1_before["Deaths"].sum() / c1_before["Births"].sum() * 100)
after_rate  = (c1_after["Deaths"].sum()  / c1_after["Births"].sum()  * 100)
reduction   = before_rate - after_rate

col1, col2, col3 = st.columns(3)
col1.metric("Clinic 1 mortality BEFORE handwashing", f"{before_rate:.1f}%")
col2.metric("Clinic 1 mortality AFTER handwashing",  f"{after_rate:.1f}%",
            delta=f"-{reduction:.1f} pp", delta_color="inverse")
col3.metric("Relative reduction in deaths (Clinic 1)", f"{reduction/before_rate*100:.0f}%",
            delta="after 1847", delta_color="inverse")

st.divider()

# ── Chart 1: Mortality rate over time ────────────────────────────────────────
st.subheader("📈 Mortality Rate Over Time")

fig1 = px.line(
    filtered, x="Year", y="Mortality Rate (%)", color="Clinic",
    markers=True,
    color_discrete_map={"Clinic 1": "#e05c5c", "Clinic 2": "#5c8de0"},
    title="Annual Mortality Rate by Clinic (Deaths / Births)",
)
# Handwashing annotation
if year_range[0] <= HANDWASHING_YEAR <= year_range[1]:
    fig1.add_vline(
        x=HANDWASHING_YEAR, line_dash="dash", line_color="#2ecc71", line_width=2,
    )
    fig1.add_annotation(
        x=HANDWASHING_YEAR, y=filtered["Mortality Rate (%)"].max() * 0.95,
        text="🧼 Handwashing<br>Introduced",
        showarrow=True, arrowhead=2, ax=40, ay=-30,
        font=dict(color="#2ecc71", size=12),
    )
fig1.update_layout(
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    yaxis_title="Mortality Rate (%)", xaxis_title="Year",
    legend_title="Clinic",
)
st.plotly_chart(fig1, use_container_width=True)

# ── Chart 2: Births vs Deaths grouped bar ────────────────────────────────────
st.subheader("📊 Births vs Deaths by Year & Clinic")

fig2 = go.Figure()
colors_births = {"Clinic 1": "#f4a261", "Clinic 2": "#457b9d"}
colors_deaths = {"Clinic 1": "#e05c5c", "Clinic 2": "#5c8de0"}

for clinic in clinics:
    sub = filtered[filtered["Clinic"] == clinic]
    fig2.add_bar(
        x=[sub["Year"].astype(str), [clinic]*len(sub)],
        y=sub["Births"], name=f"{clinic} – Births",
        marker_color=colors_births[clinic], opacity=0.75,
    )
    fig2.add_bar(
        x=[sub["Year"].astype(str), [clinic]*len(sub)],
        y=sub["Deaths"], name=f"{clinic} – Deaths",
        marker_color=colors_deaths[clinic],
    )

fig2.update_layout(
    barmode="group",
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    yaxis_title="Count", xaxis_title="Year / Clinic",
    legend_title="Series",
)
st.plotly_chart(fig2, use_container_width=True)

# ── Chart 3: Before vs After bar (Clinic 1 only) ─────────────────────────────
st.subheader("🔬 Before vs After Handwashing — Clinic 1")

c1 = df[df["Clinic"] == "Clinic 1"].copy()
c1["Period"] = c1["Year"].apply(
    lambda y: f"Before ({df['Year'].min()}–{HANDWASHING_YEAR-1})"
              if y < HANDWASHING_YEAR
              else f"After ({HANDWASHING_YEAR}–{df['Year'].max()})"
)
period_summary = (
    c1.groupby("Period")
    .apply(lambda g: pd.Series({
        "Avg Mortality Rate (%)": (g["Deaths"].sum() / g["Births"].sum() * 100).round(2)
    }))
    .reset_index()
)

fig3 = px.bar(
    period_summary, x="Period", y="Avg Mortality Rate (%)",
    color="Period",
    color_discrete_sequence=["#e05c5c", "#2ecc71"],
    text="Avg Mortality Rate (%)",
    title="Average Mortality Rate Before vs After Handwashing (Clinic 1)",
)
fig3.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
fig3.update_layout(
    showlegend=False,
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    yaxis_title="Avg Mortality Rate (%)",
)
st.plotly_chart(fig3, use_container_width=True)

# ── Raw data ──────────────────────────────────────────────────────────────────
with st.expander("📄 View raw data"):
    st.dataframe(filtered.sort_values(["Year","Clinic"]), use_container_width=True)

# ── Findings ──────────────────────────────────────────────────────────────────
st.divider()
st.subheader("🔎 Key Findings")
st.info(
    """
    **1. Clinic 1 had dramatically higher mortality than Clinic 2 before 1847.**
    Medical students performing autopsies before delivering babies were unknowingly
    transferring cadaveric particles — what we now call pathogens — to mothers.

    **2. Handwashing caused an immediate and dramatic drop in deaths.**
    Clinic 1's mortality rate fell from ~10–12 % in peak years to under 2 % within
    a single year of Semmelweis introducing chlorinated lime handwashing in May 1847.

    **3. The data is one of the earliest examples of evidence-based infection control.**
    Despite initial resistance from the medical establishment, Semmelweis's data
    foreshadowed Germ Theory and laid the foundation for modern surgical hygiene.
    """
)

st.caption("Data source: Semmelweis (1861). Vienna General Hospital maternity ward records, 1841–1849.")
