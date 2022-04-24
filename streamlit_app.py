import pandas as pd
import numpy as np
import plotly.express as px
from plotly import io as pio
import streamlit as st

from streamlit_funcs import (
    plot_histograms,
    plot_mean_and_median_lines,
    plot_boxplot,
    plot_usa_map,
)

title = "Health Insurance Interactive EDA Dashboard"
st.set_page_config(
    page_title=title,
    page_icon="🏥",
    layout="wide",
)

st.title(title)

left_col, right_col = st.columns(2)

with left_col:
    choice_hist = st.selectbox(
        "Histogram: Choose variable to plot", ("Rate", "Year", "Age", "State")
    )

    plot_histograms(choice_hist)

    choice_line = st.selectbox(
        "Line: Choose variable to plot",
        ("age", "state", "year"),
        format_func=lambda x: x.title(),
    )
    plot_mean_and_median_lines(choice_line)

with right_col:
    choice_boxplot = st.selectbox(
        "Boxplot: Choose variable for x-axis",
        ("none", "age", "state", "year"),
        format_func=lambda x: x.title(),
    )

    plot_boxplot(choice_boxplot)

    choice_map = st.selectbox(
        "Map: Choose aggregate statistic",
        ("median", "mean", "min", "max", "std"),
        format_func=lambda x: x.title() if x.startswith("m") else "Standard Deviation",
    )

    plot_usa_map(choice_map)
