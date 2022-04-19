from h2o_wave import main, app, Q, ui

from time import time
import os

import pandas as pd
import numpy as np
import plotly.express as px
from plotly import io as pio
from plotly import graph_objects as go

from loguru import logger

os.environ["H2O_WAVE_NO_LOG"] = "1"


@app("/insurance")
async def serve(q: Q):
    times_df_loaded = 0
    if not q.client.initialized:
        q.client.initialized = True
        # Load dataframe
        start = time()
        rates = pd.read_csv("data/rate_sample.csv", nrows=100000)
        # One dataframe per app as per this answer
        # https://github.com/h2oai/wave/discussions/1342#discussioncomment-2550120
        q.app.rates = preprocess_df(rates)
        end = time()
        print(f"It took {end - start:.2f}s to load df")
        times_df_loaded += 1
        print(f"Dataframe loaded {times_df_loaded} times in total")

        hist_initial_value = "rate"
        q.page["input_hist"] = ui.form_card(
            box="1 1 5 2",
            items=[
                ui.dropdown(
                    name="choice_hist",
                    label="Histogram: Choose variable to plot",
                    value=hist_initial_value,
                    trigger=True,
                    choices=[
                        ui.choice(name="rate", label="Rate"),
                        ui.choice(name="year", label="Year"),
                        ui.choice(name="age", label="Age"),
                        ui.choice(name="state", label="State"),
                    ],
                )
            ],
        )
        q.page["hist"] = ui.frame_card(
            box="1 2 5 4",
            title="",
            content=plot_histograms(q, hist_initial_value),
        )

        box_initial_value = "none"
        q.page["input_box"] = ui.form_card(
            box="6 1 4 2",
            items=[
                ui.dropdown(
                    name="choice_box",
                    label="Boxplot: Choose variable for x-axis (optional)",
                    value=box_initial_value,
                    trigger=True,
                    choices=[
                        ui.choice("none", "None"),
                        ui.choice("age", "Age"),
                        ui.choice("state", "State (ordered by median)"),
                        ui.choice("year", "Year"),
                    ],
                )
            ],
        )

        q.page["box"] = ui.frame_card(
            box="6 2 4 4",
            title="",
            content=plot_boxplot(q, x=box_initial_value),
        )

        map_initial_value = "median"
        q.page["input_map"] = ui.form_card(
            box="6 6 4 2",
            items=[
                ui.dropdown(
                    name="choice_map",
                    label="Map: Choose aggregate statistic",
                    value=map_initial_value,
                    trigger=True,
                    choices=[
                        ui.choice(name="median", label="Median"),
                        ui.choice(name="mean", label="Mean"),
                        ui.choice(name="min", label="Minimum"),
                        ui.choice(name="max", label="Maximum"),
                        ui.choice(name="std", label="Standard Deviation"),
                    ],
                ),
            ],
        )
        q.page["map"] = ui.frame_card(
            box="6 7 4 5",
            title="",
            content=plot_usa_map(q, map_initial_value),
        )

    # Map
    if q.args.choice_map:
        q.page["map"].content = plot_usa_map(q, q.args.choice_map)

    # Histogram
    if q.args.choice_hist:
        q.page["hist"].content = plot_histograms(q, q.args.choice_hist)

    # Boxplot
    if q.args.choice_box:
        q.page["box"].content = plot_boxplot(q, x=q.args.choice_box)

    await q.page.save()


def preprocess_df(df):
    age_cols = ["BusinessYear", "StateCode", "Age", "IndividualRate"]
    age_full = df.loc[:, age_cols]
    age_full.columns = ["year", "state", "age", "rate"]

    # Turn all values in age column to ints
    age_full = age_full[age_full.age != "Family Option"]
    age_full["age"] = age_full.age.str.replace("0-20", "20")
    age_full["age"] = age_full.age.str.replace("65 and over", "65")
    age_full["age"] = pd.to_numeric(age_full.age)

    # Drop all outlier plans
    age_full = age_full[age_full.rate < 9999]

    return age_full


def plot_boxplot(q, x="none"):
    if x == "none":
        x = None
    if x == "state":
        return plot_boxplot_state(q)
    fig = px.box(q.app.rates, y="rate", x=x)
    html = pio.to_html(fig, validate=False, include_plotlyjs="cdn")
    return html


def plot_boxplot_state(q):
    # Order by median
    sorted_state_count = q.app.rates.groupby("state").median().sort_values("rate")
    ordering = sorted_state_count.index

    fig = px.box(q.app.rates, y="rate", x="state", category_orders={"state": ordering})

    fig.update_layout(
        xaxis={
            "tickmode": "array",
            "tickvals": list(range(len(ordering))),
            "ticktext": ordering,
            "tickfont_size": 9,
        }
    )
    html = pio.to_html(fig, validate=False, include_plotlyjs="cdn")
    return html


def plot_usa_map(q, statistic):

    match statistic:
        case "median":
            rate_by_state = q.app.rates.groupby("state").median().rate
        case "max":
            rate_by_state = q.app.rates.groupby("state").max().rate
        case "min":
            rate_by_state = q.app.rates.groupby("state").min().rate
        case "mean":
            rate_by_state = q.app.rates.groupby("state").mean().rate
        case "std":
            rate_by_state = q.app.rates.groupby("state").std().rate

    # title = f"{statistic.title()} Rate" if statistic != "std" else "Standard Deviation"
    # title = title + " by State"
    fig = px.choropleth(
        # rate_by_state,
        locationmode="USA-states",
        locations=rate_by_state.index,
        scope="usa",
        color=rate_by_state,
        color_continuous_scale="reds",
        # title=title,
    )
    fig.layout.coloraxis.colorbar.title = "Rate ($)"
    html = pio.to_html(fig, validate=False, include_plotlyjs="cdn")

    return html


def plot_histograms(q, column):
    match column:
        case "rate":
            return plot_hist_rate(q)
        case "age":
            return plot_hist_age(q)
        case "state":
            return plot_hist_state(q)
        case "year":
            return plot_hist_year(q)


def plot_hist_rate(q):
    fig = px.histogram(q.app.rates, x="rate", log_y=True)
    html = pio.to_html(fig, validate=False, include_plotlyjs="cdn")
    return html


def plot_hist_age(q):
    fig = px.histogram(q.app.rates, x="age")
    html = pio.to_html(fig, validate=False, include_plotlyjs="cdn")
    return html


def plot_hist_year(q):
    year_count = q.app.rates.groupby("year").count()
    fig = px.histogram(
        year_count,
        x=["2014", "2015", "2016"],
        y="state",
        labels=dict(state="year", x="year"),
    )
    html = pio.to_html(fig, validate=False, include_plotlyjs="cdn")
    return html


def plot_hist_state(q):
    sorted_state_count = q.app.rates.groupby("state").count().sort_values("rate")
    ordering = sorted_state_count.index

    fig = px.histogram(q.app.rates, x="state", category_orders={"state": ordering})

    fig.update_layout(
        xaxis={
            "tickmode": "array",
            "tickvals": list(range(len(ordering))),
            "ticktext": ordering,
        }
    )
    html = pio.to_html(fig, validate=False, include_plotlyjs="cdn")
    return html
