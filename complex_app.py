from h2o_wave import main, app, Q, ui
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from plotly import graph_objects as go
from plotly import io as pio
from pprint import pprint

np.random.seed(19680801)


@app("/demo")
async def serve(q: Q):
    if not q.client.initialized:  # First visit
        q.client.initialized = True
        q.client.points = 25
        q.client.plotly_controls = False

        q.page["controls"] = ui.form_card(
            box="1 1 4 2",
            items=[
                ui.slider(
                    name="points",
                    label="Points",
                    min=5,
                    max=50,
                    step=1,
                    value=q.client.points,
                    trigger=True,
                ),
                ui.toggle(
                    name="plotly_controls", label="Plotly Controls", trigger=True
                ),
            ],
        )
        q.page["plot"] = ui.frame_card(box="1 3 4 5", title="", content="")

    if q.args.points is not None:
        q.client.points = q.args.points

    if q.args.plotly_controls is not None:
        q.client.plotly_controls = q.args.plotly_controls

    n = q.client.points

    # Create plot with plotly
    fig = go.Figure(
        data=go.Scatter(
            x=np.random.rand(n),
            y=np.random.rand(n),
            mode="markers",
            marker=dict(size=(8 * np.random.rand(n)) ** 2, color=np.random.rand(n)),
            opacity=0.8,
        )
    )
    _ = fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgb(255, 255, 255)",
        plot_bgcolor="rgb(255, 255, 255)",
    )
    config = {
        "scrollZoom": q.client.plotly_controls,
        "showLink": q.client.plotly_controls,
        "displayModeBar": q.client.plotly_controls,
    }
    html = pio.to_html(fig, validate=False, include_plotlyjs="cdn", config=config)

    q.page["plot"].content = html

    # Save page
    await q.page.save()


choices = [
    ui.choice("A", "Option A"),
    ui.choice("B", "Option B"),
    ui.choice("C", "Option C", disabled=True),
    ui.choice("D", "Option D"),
]

choices_dialog = [ui.choice(str(i), f"Option {i}") for i in range(1, 102)]


@app("/dropdown")
async def serve(q: Q):
    if q.args.show_inputs:
        q.page["example"].items = [
            ui.text(f"dropdown={q.args.dropdown}"),
            ui.text(f"dropdown_multi={q.args.dropdown_multi}"),
            ui.text(f"dropdown_disabled={q.args.dropdown_disabled}"),
            ui.text(f"dropdown_dialog={q.args.dropdown_dialog}"),
            ui.text(f"dropdown_popup_always={q.args.dropdown_popup_always}"),
            ui.text(f"dropdown_popup_never={q.args.dropdown_popup_never}"),
            ui.button(name="show_form", label="Back", primary=True),
        ]
    else:
        q.page["example"] = ui.form_card(
            box="1 1 4 10",
            items=[
                ui.dropdown(
                    name="dropdown",
                    label="Pick one",
                    value="B",
                    required=True,
                    choices=choices,
                ),
                ui.dropdown(
                    name="dropdown_multi",
                    label="Pick multiple",
                    values=["B", "D"],
                    required=True,
                    choices=choices,
                ),
                ui.dropdown(
                    name="dropdown_disabled",
                    label="Pick one (Disabled)",
                    value="B",
                    choices=choices,
                    disabled=True,
                ),
                ui.dropdown(
                    name="dropdown_dialog",
                    label="Pick multiple in dialog (>100 choices)",
                    values=["1"],
                    required=True,
                    choices=choices_dialog,
                ),
                ui.dropdown(
                    name="dropdown_popup_always",
                    label="Always show popup even when choices < 100",
                    value="A",
                    required=True,
                    choices=choices,
                    popup="always",
                ),
                ui.dropdown(
                    name="dropdown_popup_never",
                    label="Never show popup even when choices > 100",
                    value="1",
                    required=True,
                    choices=choices_dialog,
                    popup="never",
                ),
                ui.button(name="show_inputs", label="Submit", primary=True),
            ],
        )
    await q.page.save()


@app("/insurance_explorer")
async def serve(q: Q):

    # Display dropdown menu
    q.page["input"] = ui.form_card(
        box="1 1 2 2",
        items=[
            ui.dropdown(
                name="agg_stat",
                label="Input",
                value="median",
                trigger=True,
                choices=[
                    ui.choice(name="median", label="Median"),
                    ui.choice(name="mean", label="Mean"),
                    ui.choice(name="max", label="Max"),
                ],
            )
        ],
    )

    q.page["output"] = ui.frame_card(
        box="1 2 2 2", title="Output", content=q.args.agg_stat
    )

    await q.page.save()


# async def serve(q: Q):
#     # Load all the dataframes and transforms we need
#     if not q.client.initialized:
#         q.client.rates = pd.read_csv("data/Rate.csv", nrows=100000)
#         q.page["usa_map"] = ui.frame_card(box="1 3 4 5", title="", content="")
#         ui.form_card(box="1 1 4 1", items=[ui.text("hello")])
#         q.client.initialized = True

#     # display_usa_map(q, q.client.rates)

#     print("q.args")
#     print("q.args begins", q.args)

#     await q.page.save()


# def display_usa_map(q: Q, rates):

#     # if q.args.mean:
#     #     rate_by_state = rates.groupby("StateCode").mean().IndividualRate
#     #     name = q.args.mean.title()
#     # elif q.args.max:
#     #     rate_by_state = rates.groupby("StateCode").max().IndividualRate
#     #     name = q.args.max.title()
#     # elif q.args.min:
#     #     rate_by_state = rates.groupby("StateCode").min().IndividualRate
#     #     name = q.args.min.title()
#     # elif q.args.std:
#     #     rate_by_state = rates.groupby("StateCode").std().IndividualRate
#     #     name = q.args.std.title()
#     # else:
#     #     rate_by_state = rates.groupby("StateCode").median().IndividualRate
#     #     name = "Median"

#     # Display dropdown menu
#     q.page["controls"] = ui.form_card(
#         box="1 1 2 2",
#         items=[
#             ui.dropdown(
#                 name="state_agg_stat",
#                 label="Choose Aggregated Statistic",
#                 value="median",
#                 trigger=True,
#                 choices=[
#                     ui.choice(name="median", label="Median"),
#                     ui.choice(name="mean", label="Mean"),
#                     ui.choice(name="max", label="Max"),
#                     ui.choice(name="min", label="Min"),
#                     ui.choice(name="std", label="Standard Deviation"),
#                 ],
#             )
#         ],
#     )

#     # rate_by_state = rates.groupby("StateCode").median().IndividualRate
#     # name = q.args.median

#     fig = px.choropleth(
#         # rate_by_state,
#         locationmode="USA-states",
#         locations=rate_by_state.index,
#         scope="usa",
#         color=rate_by_state,
#         color_continuous_scale="reds",
#         title=f"{name} Rate by State (all data)",
#     )

#     html = pio.to_html(fig, validate=False, include_plotlyjs="cdn")

#     q.page["usa_map"].content = html


# def get_map_values(q: Q):
#     if q.args.median:
#         rate_by_state = rates.groupby("StateCode").median().IndividualRate
#         name = q.args.median
#     if q.args.mean:
#         rate_by_state = rates.groupby("StateCode").mean().IndividualRate
#         name = q.args.mean
#     if q.args.max:
#         rate_by_state = rates.groupby("StateCode").max().IndividualRate
#         name = q.args.max
#     if q.args.min:
#         rate_by_state = rates.groupby("StateCode").min().IndividualRate
#         name = q.args.min
#     if q.args.std:
#         rate_by_state = rates.groupby("StateCode").std().IndividualRate
#         name = q.args.std
