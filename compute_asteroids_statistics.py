"""Simple program to compute statistics and figures from
the ‘Asteroids - NeoWs’ database provided by NASA.
"""

import argparse
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
from tqdm import tqdm

from badaboom.parsers.asteroids import AsteroidDatasetParser


def main(
    api_key: str,
    fn_figure_events: str,
    fn_figure_asteroid_size: str,
    start_year: int = 1980,
    end_year: int = 2030,
) -> None:
    """Retrieve information (from start_year to en_year), do all figures and compute some
    information.

    Parameters
    ----------
    api_key : str
        Your API key provided by NASA, see https://api.nasa.gov/ for more details.
    fn_figure_events : str
        Filename of the first figure.
    fn_figure_asteroid_size : str
        Filename of the second figure.
    start_year : int, optional
        Year to start from, by default 1980
    end_year : int, optional
        Year to end the computation, by default 2030
    """
    adp = AsteroidDatasetParser(api_key)

    # Gathering data
    years = list(
        range(start_year, end_year + 1)
    )  # first registered year 1899; no data are available before
    nunique_asteroid_per_year = []
    nunique_events_per_year = []
    min_dist_per_year = []
    poten_hazardous_events_per_year = []
    small_asteroids = []
    medium_asteroids = []
    big_asteroids = []
    enormous_asteroids = []
    gigantic_asteroids = []

    pbar = tqdm(years)
    for year in pbar:
        pbar.set_description(f"Processing year {year}", refresh=True)
        res = adp.retrieve_year_dataframe(year)

        year_neo_feed_df, year_asteroid_df = res
        nunique_asteroid_per_year.append(year_neo_feed_df["asteroid_id"].nunique())
        nunique_events_per_year.append(year_neo_feed_df.shape[0])
        min_dist_per_year.append(year_neo_feed_df["miss_distance"].min())
        poten_hazardous_events_per_year.append(
            year_neo_feed_df["is_potentially_hazardous_asteroid"].sum()
        )
        small_asteroids.append(
            year_asteroid_df[year_asteroid_df["estimated_diameter_max"] < 0.1].shape[0]
        )
        medium_asteroids.append(
            year_asteroid_df[
                (year_asteroid_df["estimated_diameter_max"] >= 0.1)
                & (year_asteroid_df["estimated_diameter_max"] < 0.5)
            ].shape[0]
        )
        big_asteroids.append(
            year_asteroid_df[
                (year_asteroid_df["estimated_diameter_max"] >= 0.5)
                & (year_asteroid_df["estimated_diameter_max"] < 1.0)
            ].shape[0]
        )
        enormous_asteroids.append(
            year_asteroid_df[
                (year_asteroid_df["estimated_diameter_max"] >= 1.0)
                & (year_asteroid_df["estimated_diameter_max"] < 2.0)
            ].shape[0]
        )
        gigantic_asteroids.append(
            year_asteroid_df[year_asteroid_df["estimated_diameter_max"] >= 2.0].shape[0]
        )

    # Figures generation
    # Figure 1
    today_timestamp = pd.Timestamp.today()

    # Creating the figure
    fig = go.Figure()

    # Adding bars for the number of unique events per year
    fig.add_trace(
        go.Bar(
            x=years,
            y=nunique_events_per_year,
            name="Number of unique events per year",
            marker_color="firebrick",
        )
    )

    # Adding bars for the number of unique asteroids per year
    fig.add_trace(
        go.Bar(
            x=years,
            y=nunique_asteroid_per_year,
            name="Number of unique asteroids per year",
            marker_color="grey",
        )
    )

    # Updating the layout
    fig.update_layout(
        title=f"Past and future asteroids events. Produced on {today_timestamp.date()}",
        xaxis=dict(title="Years"),
        yaxis=dict(title="Count"),
        barmode="group",
        bargap=0.15,  # Gap between bars of adjacent location coordinates.
        bargroupgap=0.1,  # Gap between bars of the same location coordinates.
        legend=dict(x=0.1, y=1.1, orientation="h"),
    )

    # Saving the figure to an HTML file
    fig.write_html(f"{fn_figure_events}.html")

    # Figure 2
    # Creating the figure
    fig = go.Figure()

    # Adding stacked bars
    fig.add_trace(
        go.Bar(
            x=years,
            y=small_asteroids,
            name="Asteroids with max diameter < 100m",
            marker_color="grey",
        )
    )

    fig.add_trace(
        go.Bar(
            x=years,
            y=medium_asteroids,
            name="Asteroids with max diameter ≥ 100m and < 500m",
            marker_color="firebrick",
        )
    )

    fig.add_trace(
        go.Bar(
            x=years,
            y=big_asteroids,
            name="Asteroids with max diameter ≥ 500m and < 1km",
            marker_color="blue",
        )
    )

    fig.add_trace(
        go.Bar(
            x=years,
            y=enormous_asteroids,
            name="Asteroids with max diameter ≥ 1km and < 2km",
            marker_color="black",
        )
    )

    fig.add_trace(
        go.Bar(
            x=years,
            y=gigantic_asteroids,
            name="Asteroids with max diameter ≥ 2km",
            marker_color="red",
        )
    )

    # Updating the layout
    fig.update_layout(
        title="Past and future asteroids events sorted by size."
        f" Produced on {today_timestamp.date()}",
        xaxis=dict(title="Years"),
        yaxis=dict(title="Count"),
        barmode="stack",
        legend=dict(x=0.1, y=1.1, orientation="h"),
        hovermode="x unified",
    )

    # Saving the figure to an HTML file
    fig.write_html(f"{fn_figure_asteroid_size}.html")

    # Some information
    begin_date = pd.Timestamp(year=start_year, month=1, day=1)
    end_date = pd.Timestamp(year=end_year, month=12, day=31)

    if start_year <= today_timestamp.year:
        end = today_timestamp if today_timestamp.year <= end_year else end_date
        asteroid_encountered = adp.df_neo_feed[
            (adp.df_neo_feed["date"] >= begin_date) & (adp.df_neo_feed["date"] < today_timestamp)
        ]["asteroid_id"].unique()
        print(
            "Unique asteroid encountered and observed from "
            f"{start_year} until {end.date()}: {asteroid_encountered.shape[0]}"
        )

    if end_year >= today_timestamp.year:
        begin = today_timestamp if today_timestamp.year >= start_year else begin_date
        asteroid_predicted = adp.df_neo_feed[
            (adp.df_neo_feed["date"] > begin) & (adp.df_neo_feed["date"] <= end_date)
        ]["asteroid_id"].unique()
        print(
            "Unique asteroid predicted to encounter from "
            f"{begin.date()} until {end_year}: {asteroid_predicted.shape[0]}"
        )

    # Save the 10 biggest asteroids from events between start_year and end_year
    asteroid_ids_selected = adp.df_neo_feed[
        (adp.df_neo_feed["date"] >= begin_date) & (adp.df_neo_feed["date"] <= end_date)
    ]["asteroid_id"]
    selected_asteroids = adp.df_asteroids[
        adp.df_asteroids["asteroid_id"].isin(asteroid_ids_selected)
    ]
    md_text = (
        selected_asteroids.sort_values("estimated_diameter_max", ascending=False)
        .head(10)[
            [
                "asteroid_neo_reference_id",
                "asteroid_name",
                "estimated_diameter_min",
                "estimated_diameter_max",
                "absolute_magnitude_h",
                "links",
            ]
        ]
        .to_markdown(index=False)
    )
    with open(f"biggest_asteroid_between_{start_year}_{end_year}.md", "w") as f:
        f.write(md_text)
        f.close()

    print(f"Biggest asteroids between {start_year} and {end_year}:")
    print(md_text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Gather data from the "Asteroids - NeoWs" database'
        "then create some figure and compute some information."
    )
    parser.add_argument(
        "--api_key",
        type=str,
        help="Your API key provided by NASA, see https://api.nasa.gov/ for more details.",
    )
    parser.add_argument(
        "--starting_year",
        type=int,
        default=1980,
        help="Starting year from which the results are computed.",
    )
    parser.add_argument(
        "--last_year",
        type=int,
        default=datetime.now().year,
        help="Last year from which the results are computed.",
    )
    parser.add_argument(
        "--fn_figure_events",
        type=str,
        default="Figure 1 - unique events per year",
        help="Filename of the outputted figure for the unique events per year.",
    )
    parser.add_argument(
        "--fn_figure_asteroid_size",
        type=str,
        default="Figure 2 - asteroid size per year",
        help="Filename of the outputted figure for the number of asteroid size per year.",
    )

    args = parser.parse_args()
    main(
        args.api_key,
        args.fn_figure_events,
        args.fn_figure_asteroid_size,
        args.starting_year,
        args.last_year,
    )
