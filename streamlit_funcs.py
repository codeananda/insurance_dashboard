import pandas as pd
import numpy as np
import plotly.express as px
from plotly import io as pio
import streamlit as st

MARGIN = dict(l=0, r=0, t=30, b=0)

rates = pd.read_csv("data/rate_sample_preprocessed_200k.csv")


def plot_histograms(column):
    match column:
        case "Rate":
            return plot_hist_rate()
        case "Age":
            return plot_hist_age()
        case "State":
            return plot_hist_state()
        case "Year":
            return plot_hist_year()


def plot_hist_rate():
    title = "Count Histogram of Rate"
    fig = px.histogram(rates, x="rate", log_y=True, title=title)
    fig.update_layout(margin=MARGIN)
    st.plotly_chart(fig, use_container_width=True)


def plot_hist_age():
    title = "Count Histogram of Age"
    fig = px.histogram(rates, x="age", title=title)
    fig.update_layout(margin=MARGIN)
    st.plotly_chart(fig, use_container_width=True)


def plot_hist_year():
    title = "Count Histogram of Year"
    year_count = rates.groupby("year").count()
    fig = px.histogram(
        year_count,
        x=["2014", "2015", "2016"],
        y="state",
        labels=dict(state="year", x="year"),
        title=title,
    )
    fig.update_layout(margin=MARGIN)
    st.plotly_chart(fig, use_container_width=True)


def plot_hist_state():
    sorted_state_count = rates.groupby("state").count().sort_values("rate")
    ordering = sorted_state_count.index

    title = "Count Histogram of State"
    fig = px.histogram(
        rates, x="state", category_orders={"state": ordering}, title=title
    )

    fig.update_layout(
        margin=MARGIN,
        xaxis={
            "tickmode": "array",
            "tickvals": list(range(len(ordering))),
            "ticktext": ordering,
        },
    )
    st.plotly_chart(fig, use_container_width=True)


# Plot mean and median rate for a column
def plot_mean_and_median_lines(column):

    median = rates.groupby(column).median().rate
    mean = rates.groupby(column).mean().rate

    # Sort by median for state
    if column == "state":
        median = median.sort_values()
        ordering = median.index
        mean = mean.loc[ordering]

    input_data = {
        "median": median,
        "mean": mean,
    }

    df_plot = pd.DataFrame(data=input_data)

    fig = px.line(
        df_plot,
        labels={"value": "rate"},
        title=f"Mean and Median Rate by {column.title()}",
    )
    fig.update_layout(margin=MARGIN)
    if column == "state":
        fig.update_layout(
            xaxis={
                "tickvals": list(range(len(rates[column].unique()))),
                "ticktext": ordering,
            }
        )
    elif column == "year":
        fig.update_layout(xaxis={"tickvals": [2014, 2015, 2016]})
    else:
        pass
    st.plotly_chart(fig, use_container_width=True)


def plot_boxplot(x="none"):
    if x == "none":
        x = None

    if x == "state":
        return plot_boxplot_state()

    title = f"Distribution of Rate"
    if x is not None:
        title += f" Grouped by {x.title()}"
    fig = px.box(
        rates,
        y="rate",
        x=x,
        title=title,
    )
    fig.update_layout(margin=MARGIN)
    st.plotly_chart(fig, use_container_width=True)


def plot_boxplot_state():
    # Order by median
    sorted_state_count = rates.groupby("state").median().sort_values("rate")
    ordering = sorted_state_count.index

    title = "Distribution of Rate Grouped by State"
    fig = px.box(
        rates,
        y="rate",
        x="state",
        category_orders={"state": ordering},
        title=title,
    )

    fig.update_layout(
        margin=MARGIN,
        xaxis={
            "tickmode": "array",
            "tickvals": list(range(len(ordering))),
            "ticktext": ordering,
            "tickfont_size": 9,
        },
    )
    st.plotly_chart(fig, use_container_width=True)


def plot_usa_map(statistic):

    match statistic:
        case "median":
            rate_by_state = rates.groupby("state").median().rate
        case "max":
            rate_by_state = rates.groupby("state").max().rate
        case "min":
            rate_by_state = rates.groupby("state").min().rate
        case "mean":
            rate_by_state = rates.groupby("state").mean().rate
        case "std":
            rate_by_state = rates.groupby("state").std().rate

    title = f"{statistic.title()} Rate" if statistic != "std" else "Standard Deviation"
    title = title + " by State"
    fig = px.choropleth(
        # rate_by_state,
        locationmode="USA-states",
        locations=rate_by_state.index,
        scope="usa",
        color=rate_by_state,
        color_continuous_scale="reds",
        title=title,
    )
    fig.update_layout(margin=MARGIN)
    fig.layout.coloraxis.colorbar.title = "Rate ($)"
    st.plotly_chart(fig, use_container_width=True)
