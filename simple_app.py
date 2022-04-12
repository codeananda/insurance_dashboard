from h2o_wave import main, app, Q, ui

from time import time

import pandas as pd
import numpy as np
import plotly.express as px
from plotly import io as pio
from plotly import graph_objects as go


@app("/insurance")
async def serve(q: Q):
    times_df_loaded = 0
    if not q.client.initialized:
        q.client.initialized = True
        # Load dataframe
        start = time()
        rates = pd.read_csv("data/rate_sample.csv", nrows=100000)
        q.client.rates = preprocess_df(rates)
        end = time()
        print(f"It took {end - start:.2f}s to load df")
        times_df_loaded += 1
        print(f"Dataframe loaded {times_df_loaded} times in total")

        q.page["map"] = ui.frame_card(box="1 1 4 5", title="", content="")
        q.page["box"] = ui.frame_card(box="5 1 4 5", title="", content="")

    # Map
    median_rate_by_state = q.client.rates.groupby("state").median().rate

    ### CHANGE WHAT HAPPENS WHEN YOU HOVER. ATM SAYS 'LOCATIONS' AND 'COLOR' ###
    fig_map = px.choropleth(
        # rate_by_state,
        locationmode="USA-states",
        locations=median_rate_by_state.index,
        scope="usa",
        color=median_rate_by_state,
        color_continuous_scale="reds",
        title="Median Rate by State",
    )
    html_map = pio.to_html(fig_map, validate=False, include_plotlyjs="cdn")
    q.page["map"].content = html_map

    # Boxplot
    fig_box = px.box(q.client.rates, y="rate")
    html_box = pio.to_html(fig_box, validate=False, include_plotlyjs="cdn")
    q.page["box"].content = html_box

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

    return age_full
