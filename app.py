"""Crop-performance dashboard: streamlit run app.py"""
import plotly.express as px
import plotly.io as pio
import streamlit as st

from agri import report
from agri.pipeline import build

st.set_page_config(page_title="Crop performance", layout="wide")

INK, MUTED, GRID = "#1F2A24", "#6B7069", "#E6E1D6"
FARM_COLORS = ["#2F5D3A", "#B5763A", "#5B7FA3", "#A34F4F", "#8A8F5C"]
WATER = {"irrigated": "#5B7FA3", "rainfed": "#B5763A"}
pio.templates["coop"] = pio.templates["simple_white"].update(layout=dict(
    font=dict(family="IBM Plex Sans, sans-serif", color=INK, size=13),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    colorway=FARM_COLORS, margin=dict(l=10, r=10, t=10, b=10),
    legend=dict(orientation="h", y=1.08, x=0, title_text=""),
    yaxis=dict(gridcolor=GRID, showgrid=True, linecolor=GRID, tickcolor=GRID),
    xaxis=dict(linecolor=GRID, tickcolor=GRID)))
pio.templates.default = "coop"


@st.cache_data
def data():
    return build()


def chart(fig, height=320):
    st.plotly_chart(fig.update_layout(height=height, legend_title_text=""), width="stretch", config={"displayModeBar": False})


cycles, issues = data()
seasons = sorted(cycles.season.dropna().unique())
st.title("Crop performance")
st.caption(f"{cycles.farm_id.nunique()} member farms · {len(cycles)} crop cycles · "
           f"{seasons[0].split()[-1][:4]}–{seasons[-1].split()[-1][-2:]} seasons")

c1, c2, c3 = st.columns([1, 2, 1], vertical_alignment="bottom")
crop = c1.selectbox("Crop", sorted(cycles.crop.dropna().unique()), format_func=str.capitalize)
farms = c2.multiselect("Farms", sorted(cycles.farm_id.unique()), default=sorted(cycles.farm_id.unique()))
only_complete = c3.toggle("Complete cycles only", value=True)
view = cycles[(cycles.crop == crop) & cycles.farm_id.isin(farms)]
if only_complete:
    view = view[view.cycle_complete]
u = view[view.yield_kg_ha.notna()]


def med(col, fmt):
    return fmt.format(u[col].median()) if u[col].notna().any() else "–"


with st.container(border=True):
    k = st.columns(4)
    k[0].metric("Cycles", len(view), help=f"{int((~cycles.cycle_complete).sum())} cycles are incomplete overall; see Data quality")
    k[1].metric("Median yield", med("yield_kg_ha", "{:,.0f} kg/ha"))
    k[2].metric("Median gross return", med("gross_return_ha", "₹{:,.0f}/ha"))
    k[3].metric("Median input cost", med("input_cost_ha", "₹{:,.0f}/ha"))

tab1, tab2, tab3, tab4 = st.tabs(["Seasons and farms", "Weather and yield", "Data quality", "Report"])
farm_order = {"farm_id": sorted(cycles.farm_id.unique()), "season": seasons}

with tab1:
    l, r = st.columns(2, gap="large")
    with l:
        st.subheader("Yield by season")
        st.caption("kg per hectare; blank = no usable yield that season")
        hm = u.pivot_table(index="farm_id", columns="season", values="yield_kg_ha")
        chart(px.imshow(hm, text_auto=".0f", aspect="auto", color_continuous_scale=["#F3EFE4", "#2F5D3A"],
                        labels={"x": "", "y": "", "color": "kg/ha"})
              .update_traces(textfont_size=11).update_coloraxes(showscale=False)
              .update_xaxes(side="top", showline=False).update_yaxes(showline=False, ticksuffix="  ")
              .update_layout(margin=dict(l=50)), 30 * len(hm) + 60)
    with r:
        st.subheader("Return and cost per hectare")
        st.caption("Mean across seasons, ₹ per hectare")
        f = u.groupby("farm_id")[["gross_return_ha", "input_cost_ha"]].mean().reset_index().melt("farm_id")
        f["variable"] = f.variable.map({"gross_return_ha": "Gross return", "input_cost_ha": "Input cost"})
        chart(px.bar(f, y="farm_id", x="value", color="variable", barmode="group", orientation="h",
                     color_discrete_sequence=["#2F5D3A", "#C9C2B0"], category_orders=farm_order,
                     labels={"value": "", "farm_id": "", "variable": ""}))

    s = report.season_table(cycles).query("crop == @crop")
    l, r = st.columns(2, gap="large")
    with l:
        st.subheader("Median yield")
        st.caption("All farms, kg per hectare")
        chart(px.line(s, x="season", y="median_yield_kg_ha", markers=True,
                      labels={"median_yield_kg_ha": "", "season": ""}), 240)
    with r:
        st.subheader("Median selling price")
        st.caption("District mandi price within 30 days of harvest, ₹ per kg")
        chart(px.line(s, x="season", y="median_price_inr_kg", markers=True,
                      color_discrete_sequence=["#B5763A"], labels={"median_price_inr_kg": "", "season": ""}), 240)

    st.subheader("Farm summary")
    ft = report.farm_table(cycles).query("crop == @crop").drop(columns="crop")
    ft["irrigated"] = ft.irrigated.map({True: "Irrigated", False: "Rainfed"})
    st.dataframe(ft, hide_index=True, width="stretch", column_config={
        "farm_id": "Farm", "farm_name": "Name", "irrigated": "Water", "cycles": "Cycles",
        "mean_yield_kg_ha": st.column_config.NumberColumn("Yield (kg/ha)", format="localized"),
        "mean_input_cost_ha": st.column_config.NumberColumn("Input cost (₹/ha)", format="localized"),
        "mean_gross_return_ha": st.column_config.NumberColumn("Gross return (₹/ha)", format="localized"),
        "mean_net_return_ha": st.column_config.NumberColumn("Net return (₹/ha)", format="localized")})

with tab2:
    driver = st.selectbox("Compare yield with", list(report.DRIVERS), format_func=lambda d: report.DRIVERS[d].capitalize())
    l, r = st.columns([2, 1], gap="large")
    with l:
        chart(px.scatter(u.assign(water=u.irrigated.map({True: "irrigated", False: "rainfed"})),
                         x=driver, y="yield_kg_ha", color="water", hover_name="cycle_id",
                         color_discrete_map=WATER, labels={"yield_kg_ha": "Yield (kg/ha)", driver: report.DRIVERS[driver]})
              .update_traces(marker=dict(size=10, line=dict(width=1, color="white"))), 380)
    with r:
        a = report.associations(cycles).query("crop == @crop and driver == @driver")[["group", "rho", "n"]]
        a["group"] = a.group.map({"all": "All farms", "irrigated": "Irrigated", "rainfed": "Rainfed"})
        st.dataframe(a, hide_index=True, width="stretch", column_config={
            "group": "Group", "rho": st.column_config.NumberColumn("Spearman ρ", format="%+.2f"), "n": "Cycles"})
        st.caption(f"ρ is shown only with at least {report.MIN_N} cycles. If a link is strong for all farms but "
                   "weak inside each water group, irrigation explains it, not this factor. "
                   "These are associations, not causes.")

with tab3:
    st.subheader("Incomplete cycles")
    st.dataframe(cycles.loc[~cycles.cycle_complete, ["cycle_id", "incomplete_reason"]], hide_index=True,
                 width="stretch", column_config={"cycle_id": "Cycle", "incomplete_reason": "Reason"})
    st.subheader("Issue log")
    st.dataframe(issues, hide_index=True, width="stretch", column_config={
        "source": "Source file", "record": "Row", "field": "Field", "value": "Value", "issue": "Issue", "action": "Action"})
    st.download_button("Download clean crop-cycle dataset (CSV)", cycles.to_csv(index=False), "clean_crop_cycles.csv")

with tab4:
    st.markdown(report.markdown(cycles, issues).split("\n", 1)[1])

st.divider()
st.caption("Weather: Open-Meteo historical archive (saved responses in data/weather/). "
           "Farm, soil, input, harvest and price records are sample data.")
