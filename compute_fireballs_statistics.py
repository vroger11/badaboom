"""Utility to compute fireball statistics."""

import argparse
import os
from os.path import exists, join

import numpy as np
import plotly.express as px

from badaboom.parsers.fireballs import gather_fireball_data


def main(mapbox_token: str, folder_results: str) -> None:
    """Compute statistics for fireball with NASA data.

    Parameters:
    -----------

    folder_results: str
        Folder where the resulting figures will be generated.
    """
    df = gather_fireball_data()
    if not exists(folder_results):
        os.makedirs(folder_results)

    # Energy distribution plot
    fig_energy = px.histogram(
        np.log(df["energy"]), nbins=30, labels={"value": "log(GJ)"}, title="Energy distribution."
    )
    fig_energy.update_layout(xaxis_title="log(GJ)", yaxis_title="Occurrences", width=1350)
    fig_energy.write_html(join(folder_results, "fireball_energy_hist.html"))

    # Impact energy distribution plot
    fig_impact_energy = px.histogram(
        np.log(df["impact-e"]),
        nbins=40,
        labels={"value": "log(kt)"},
        title="Impact energy distribution.",
    )
    fig_impact_energy.update_layout(xaxis_title="log(kt)", yaxis_title="Occurrences", width=1350)
    fig_impact_energy.write_html(join(folder_results, "fireball_impact_energy_hist.html"))

    print(f"Number of fireballs not located: {len(df[np.isnan(df['lon'])])}")

    # Number of fireballs detected per year
    fireballs_per_year = df.groupby(df["date"].dt.year)["date"].count()
    fig_year = px.bar(
        fireballs_per_year,
        labels={"index": "year", "value": "Occurrences"},
        title="Number of fireballs detected per year.",
    )
    fig_year.update_layout(width=1350, height=600)
    fig_year.write_html(join(folder_results, "fireballs_per_year.html"))

    # Recorded fireballs without location
    fireballs_no_loc = df[np.isnan(df["lon"])].groupby(df["date"].dt.year)["date"].count()
    fig_no_loc = px.bar(
        fireballs_no_loc,
        labels={"index": "year", "value": "Occurrences"},
        title="Recorded fireballs without location.",
    )
    fig_no_loc.update_layout(width=1350, height=600)
    fig_no_loc.write_html(join(folder_results, "fireball_missing_locations.html"))

    # Convert lat and lon to follow standard latitude and longitude values
    df_map = df.assign(
        longitude=df["lon-dir"].apply(lambda x: 1 if x == "E" else -1) * df["lon"],
        latitude=df["lat-dir"].apply(lambda x: 1 if x == "N" else -1) * df["lat"],
        size=np.log(df["energy"] + 1) * 1.25,
        year=df["date"].apply(lambda x: x.year),
        month=df["date"].apply(lambda x: x.month),
        day=df["date"].apply(lambda x: x.day),
    )

    df_map = df_map.dropna(subset=["latitude", "longitude"])

    print(f'latitude: {df_map["latitude"].min()} - {df_map["latitude"].max()}')

    px.set_mapbox_access_token(mapbox_token)
    fig_map = px.scatter_mapbox(
        df_map,
        lat="latitude",
        lon="longitude",
        size="size",
        hover_name="date",
        hover_data={"energy": True, "impact-e": True, "year": True, "month": True, "day": True},
        title="Fireball recorded impacts sorted by energy values.",
        zoom=1,
        height=1100,
        width=1000,
    )
    fig_map.update_layout(mapbox_style="open-street-map")
    fig_map.write_html(join(folder_results, "fireball_map.html"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Gather data from Nasa open database about fireballs."
    )
    parser.add_argument(
        "--folder_results",
        type=str,
        default="fireball_results",
        help="Folder where the resulting figures will be.",
    )

    parser.add_argument("--mapbox_token", type=str, help="Your MapBox token.")

    args = parser.parse_args()
    main(args.mapbox_token, args.folder_results)
