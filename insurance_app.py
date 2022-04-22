from h2o_wave import main, app, Q, ui

import pandas as pd
import numpy as np
import plotly.express as px
from plotly import io as pio

MARGIN = dict(l=0, r=0, t=30, b=0)


@app("/insurance")
async def serve(q: Q):
    if not q.client.initialized:
        q.client.initialized = True
        # Load dataframe
        q.app.rates = pd.read_csv("data/rate_sample_preprocessed_200k.csv")

        hist_initial_value = "rate"
        q.page["dropdown_hist"] = ui.form_card(
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
            box="1 2 5 5",
            title="",
            content=plot_histograms(q, hist_initial_value),
        )

        box_initial_value = "none"
        q.page["dropdown_box"] = ui.form_card(
            box="6 1 4 2",
            items=[
                ui.dropdown(
                    name="choice_box",
                    label="Boxplot: Choose variable for x-axis",
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
            box="6 2 4 5",
            title="",
            content=plot_boxplot(q, x=box_initial_value),
        )

        map_initial_value = "median"
        q.page["dropdown_map"] = ui.form_card(
            box="6 7 4 2",
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
            box="6 8 4 5",
            title="",
            content=plot_usa_map(q, map_initial_value),
        )

        line_initial_value = "age"
        q.page["dropdown_line"] = ui.form_card(
            box="1 7 5 2",
            items=[
                ui.dropdown(
                    name="choice_line",
                    label="Line: Choose variable to plot",
                    value=line_initial_value,
                    trigger=True,
                    choices=[
                        ui.choice(name="age", label="Age"),
                        ui.choice(name="state", label="State"),
                        ui.choice(name="year", label="Year"),
                    ],
                )
            ],
        )
        q.page["line"] = ui.frame_card(
            box="1 8 5 5",
            title="",
            content=plot_mean_and_median_lines(q, line_initial_value),
        )

    # Update Map
    if q.args.choice_map:
        q.page["map"].content = plot_usa_map(q, q.args.choice_map)

    # Update Histogram
    if q.args.choice_hist:
        q.page["hist"].content = plot_histograms(q, q.args.choice_hist)

    # Update Boxplot
    if q.args.choice_box:
        q.page["box"].content = plot_boxplot(q, x=q.args.choice_box)

    # Update Line
    if q.args.choice_line:
        q.page["line"].content = plot_mean_and_median_lines(q, q.args.choice_line)

    await q.page.save()


def preprocess_df(df):
    cols_we_want = ["BusinessYear", "StateCode", "Age", "IndividualRate"]
    df = df.loc[:, cols_we_want]
    df.columns = ["year", "state", "age", "rate"]

    # Turn all values in age column to ints
    df = df[df.age != "Family Option"]
    df["age"] = df.age.str.replace("0-20", "20")
    df["age"] = df.age.str.replace("65 and over", "65")
    df["age"] = pd.to_numeric(df.age)

    # Drop all outlier plans
    df = df[df.rate < 9999]

    return df


def plot_boxplot(q, x="none"):
    if x == "none":
        x = None

    if x == "state":
        return plot_boxplot_state(q)

    title = f"Distribution of Rate"
    if x is not None:
        title += f" Grouped by {x.title()}"
    fig = px.box(
        q.app.rates,
        y="rate",
        x=x,
        title=title,
    )
    fig.update_layout(margin=MARGIN)
    html = pio.to_html(fig, validate=False, include_plotlyjs="cdn")
    return html


def plot_boxplot_state(q):
    # Order by median
    sorted_state_count = q.app.rates.groupby("state").median().sort_values("rate")
    ordering = sorted_state_count.index

    title = "Distribution of Rate Grouped by State"
    fig = px.box(
        q.app.rates,
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
    fig.update_layout(margin=MARGIN)
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
    title = "Count Histogram of Rate"
    fig = px.histogram(q.app.rates, x="rate", log_y=True, title=title)
    fig.update_layout(margin=MARGIN)
    html = pio.to_html(fig, validate=False, include_plotlyjs="cdn")
    return html


def plot_hist_age(q):
    title = "Count Histogram of Age"
    fig = px.histogram(q.app.rates, x="age", title=title)
    fig.update_layout(margin=MARGIN)
    html = pio.to_html(fig, validate=False, include_plotlyjs="cdn")
    return html


def plot_hist_year(q):
    title = "Count Histogram of Year"
    year_count = q.app.rates.groupby("year").count()
    fig = px.histogram(
        year_count,
        x=["2014", "2015", "2016"],
        y="state",
        labels=dict(state="year", x="year"),
        title=title,
    )
    fig.update_layout(margin=MARGIN)
    html = pio.to_html(fig, validate=False, include_plotlyjs="cdn")
    return html


def plot_hist_state(q):
    sorted_state_count = q.app.rates.groupby("state").count().sort_values("rate")
    ordering = sorted_state_count.index

    title = "Count Histogram of State"
    fig = px.histogram(
        q.app.rates, x="state", category_orders={"state": ordering}, title=title
    )

    fig.update_layout(
        margin=MARGIN,
        xaxis={
            "tickmode": "array",
            "tickvals": list(range(len(ordering))),
            "ticktext": ordering,
        },
    )
    html = pio.to_html(fig, validate=False, include_plotlyjs="cdn")
    return html


# Plot mean and median rate for a column
def plot_mean_and_median_lines(q, column):

    median = q.app.rates.groupby(column).median().rate
    mean = q.app.rates.groupby(column).mean().rate

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
                "tickvals": list(range(len(q.app.rates[column].unique()))),
                "ticktext": ordering,
            }
        )
    elif column == "year":
        fig.update_layout(xaxis={"tickvals": [2014, 2015, 2016]})
    else:
        pass
    html = pio.to_html(fig, validate=False, include_plotlyjs="cdn")
    return html
