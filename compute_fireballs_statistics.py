import argparse
import numpy as np
import os
import pandas as pd

from badaboom.fireballs_parser import gather_fireball_data
from bokeh.plotting import figure, output_file, save
from os.path import exists, join

# use bokeh instead of matplotlib for pandas
pd.set_option('plotting.backend', 'pandas_bokeh')


def main(folder_results):
    """Compute statistics for fireball with NASA data.

    Parameters:
    -----------

    folder_results: str
        Folder where the resulting figures will be generated.
    """
    df = gather_fireball_data()
    if not exists(folder_results):
        os.makedirs(folder_results)

    p_energy = np.log(df["energy"]).plot.hist(
        bins=40,
        show_figure=False,
        ylabel="Occurences",
        xlabel="log(J)",
        title="Energy distribution."
    )
    p_energy.plot_width=1350
    output_file(join(folder_results, "fireball_energy_hist.html"))
    save(p_energy)


    p_impact_energy = np.log(df["impact-e"]).plot.hist(
        bins=40,
        show_figure=False,
        ylabel="Occurences",
        xlabel="log(kt)",
        title="Impact energy distribution."
    )
    p_impact_energy.plot_width=1350
    output_file(join(folder_results, "fireball_impact_energy_hist.html"))
    save(p_impact_energy)

    print(f"Number of fireballs not located: {len(df[np.isnan(df['lon'])])}")

    df.groupby(df["date"].dt.year)["date"].count().plot(
        kind="bar",
        show_figure=False,
        figsize=(1350, 600),
        xlabel="year",
        ylabel="Occurences",
        title="Number of fireballs detected per year."
    )

    p = df[np.isnan(df['lon'])].groupby(df["date"].dt.year)["date"].count().plot(
        kind="bar",
        show_figure=False,
        figsize=(1350, 600),
        xlabel="year",
        ylabel="Occurences",
        title="Recorded fireballs without location."
    )
    output_file(join(folder_results, "fireball_missing_locations.html"))
    save(p)

    # convert lat and lon to follow standard latitude and longitude values
    df_map = df.assign(
        longitude=df["lon-dir"].apply(lambda x: 1 if x == "E" else -1) * df["lon"],
        latitude=df["lat-dir"].apply(lambda x: 1 if x == "N" else -1) * df["lat"],
        size=np.log(df["energy"]+1)*2,
        year=df["date"].apply(lambda x: x.year),
        month=df["date"].apply(lambda x: x.month),
        day=df["date"].apply(lambda x: x.day)
    )

    p_map = df_map.dropna(subset=['lat', 'lon']).plot_bokeh.map(
        x="longitude",
        y="latitude",
        hovertool_string="""<h2> @{year}-@{month}-@{day} </h2>
                            <h3> Energy value: @{energy}J </h3>
                            <h3> Impact energy value: @{impact-e}kt </h3>""",
        tile_provider="STAMEN_TERRAIN_RETINA",
        size="size",
        figsize=(1000, 1100),
        title="Fireball recorded impacts sorted by energy values.",
        show_figure=False
    )

    output_file(join(folder_results, "fireball_map.html"))
    save(p_map)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Gather data from Nasa open database about fireballs.'
    )
    parser.add_argument("--folder_results", type=str, default="fireball_results",
                         help="Folder where the resulting figures will be.")

    args = parser.parse_args()
    main(args.folder_results)

