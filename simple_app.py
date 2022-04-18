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

        map_initial_value = "median"
        q.page["input_map"] = ui.form_card(
            box="1 1 4 2",
            items=[
                ui.dropdown(
                    name="aggregate_statistic",
                    label="Choose aggregate statistic",
                    value=map_initial_value,  # set default value
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
            box="1 2 4 5",
            title="",
            content=plot_usa_map(q, map_initial_value),
        )

        q.page["input_box"] = ui.form_card(
            box="5 1 4 2",
            items=[
                ui.choice_group(
                    name="box_category",
                    label="Group by Category (optional)",
                    inline=True,
                    value="none",
                    choices=[
                        ui.choice("none", "No Category"),
                        ui.choice("age", "Age"),
                        ui.choice("state", "State"),
                        ui.choice("year", "Year"),
                    ],
                ),
                ui.button(name="choose_box_category", label="Submit", primary=True),
            ],
        )

        q.page["box"] = ui.frame_card(
            box="5 3 4 5",
            title="",
            content=plot_boxplot(q),
        )

    # Map
    if q.args.aggregate_statistic:
        q.page["map"].content = plot_usa_map(q, q.args.aggregate_statistic)

    # Boxplot
    if q.args.choose_box_category:

        q.page["box"].content = plot_boxplot(
            q, x=q.args.box_category if q.args.box_category != "none" else None
        )

    await q.page.save()


def preprocess_df(df):
    age_cols = ["BusinessYear", "StateCode", "Age", "IndividualRate"]
    age_full = df.loc[:, age_cols]
    age_full.columns = ["year", "state", "age", "rate"]
    age_full = age_full[age_full.age != "Family Option"]

    # Turn all values in age column to ints
    age_full["age"] = age_full.age.str.replace("0-20", "20")
    age_full["age"] = age_full.age.str.replace("65 and over", "65")
    age_full["age"] = pd.to_numeric(age_full.age)

    # Drop all outlier plans
    age_full = age_full[age_full.rate < 9999]

    return age_full


def plot_boxplot(q, x=None):
    fig = px.box(q.app.rates, y="rate", x=x)
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
    fig.layout.coloraxis.colorbar.title = "Rate ($)"
    html = pio.to_html(fig, validate=False, include_plotlyjs="cdn")

    return html
