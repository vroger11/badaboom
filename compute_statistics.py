import argparse
import pandas as pd

from badaboom.asteroid_parser import AsteroidDatasetParser
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure, output_file, save
from bokeh.transform import dodge
from tqdm import tqdm


def main(api_key, fn_figure_events, fn_figure_asteroid_size, start_year=1980, end_year=2030):
    """Retreive information (from start_year to en_year), do all figures and compute some information.

    Parameters
    ----------

    api_key: (str)
        Your API key provided by NASA, see https://api.nasa.gov/ for more details.

    fn_figure_events: (str)
        Filename of the first figure.

    fn_figure_asteroid_size: (str)
        Filename of the second figure.

    start_year: (int)

    end_year: (int)
    """
    adp = AsteroidDatasetParser(api_key)

    # Gathering data
    years = list(range(start_year, end_year+1)) # first registered year 1899; no data are available before
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
        poten_hazardous_events_per_year.append(year_neo_feed_df["is_potentially_hazardous_asteroid"].sum())
        small_asteroids.append(year_asteroid_df[year_asteroid_df["estimated_diameter_max"] < 0.1].shape[0])
        medium_asteroids.append(year_asteroid_df[(year_asteroid_df["estimated_diameter_max"] >= 0.1) & (year_asteroid_df["estimated_diameter_max"] < .5)].shape[0])
        big_asteroids.append(year_asteroid_df[(year_asteroid_df["estimated_diameter_max"] >= 0.5) & (year_asteroid_df["estimated_diameter_max"] < 1.)].shape[0])
        enormous_asteroids.append(year_asteroid_df[(year_asteroid_df["estimated_diameter_max"] >= 1.) & (year_asteroid_df["estimated_diameter_max"] < 2.)].shape[0])
        gigantic_asteroids.append(year_asteroid_df[year_asteroid_df["estimated_diameter_max"] >= 2.].shape[0])

    # Figures generation
    # Figure 1
    today_timestamp = pd.Timestamp.today()

    mdata = {
        'years'                           : years,
        'nunique_events_per_year'         : nunique_events_per_year,
        'nunique_asteroid_per_year'       : nunique_asteroid_per_year
    }

    source = ColumnDataSource(data=mdata)

    # Creating a column data source
    tooltips = [
        ("Year", "@years"),
        ("Number of unique events", "@nunique_events_per_year"),
        ("Number of unique asteroid", "@nunique_asteroid_per_year"),
    ]

    #Initializing our plot
    p = figure(plot_width=1350, plot_height=600,
            title=f"Past and future asteroids events. Produced the {today_timestamp.date()}.",
            tooltips=tooltips)
    #Plotting our vertical bar chart
    p.vbar(x=dodge('years', -0.16, range=p.x_range), top='nunique_events_per_year', width=0.28, source=source,
        color="firebrick", legend_label="Number of unique events per year")

    p.vbar(x=dodge('years',  0.16,  range=p.x_range), top='nunique_asteroid_per_year', width=0.28, source=source,
        color="grey", legend_label="Number of unique asteroid per year")

    p.legend.location = "top_left"
    p.legend.orientation = "horizontal"

    #Enhancing our graph
    p.x_range.range_padding = 0.1

    output_file(fn_figure_events + ".html")
    save(p)

    # Figure 2
    source = ColumnDataSource(data=dict(
        years=years,
        y1=small_asteroids,
        y2=medium_asteroids,
        y3=big_asteroids,
        y4=enormous_asteroids,
        y5=gigantic_asteroids
    ))

    tooltips = [
        ("Year", "@years"),
        ("Asteroids with max diameter < 100m", "@y1"),
        ("Asteroids with max diameter \u2265 100m and < 500m", "@y2"),
        ("Asteroids with max diameter \u2265 500m and < 1km", "@y3"),
        ("Asteroids with max diameter \u2265 1km and < 2km", "@y4"),
        ("Asteroids with max diameter \u2265 2km", "@y5"),
    ]

    p = figure(plot_width=1350, plot_height=600,
            title=f"Past and future asteroids events sorted by size. Produced the {today_timestamp.date()}.",
            tooltips=tooltips)
    p.vbar_stack(["y1", "y2", "y3", "y4", "y5"], x='years', width=0.5,
                color=["grey", "firebrick", "blue", "black", "red"],
                legend_label=[
                    "Asteroids with max diameter < 100m",
                    "Asteroids withmax diameter \u2265 100m and < 500m",
                    "Asteroids with max diameter \u2265 500m and < 1km",
                    "Asteroids with max diameter \u2265 1km and < 2km",
                    "Asteroids with max diameter \u2265 2km"],
                source=source)

    p.legend.location = "top_left"

    output_file(fn_figure_asteroid_size + ".html")
    save(p)

    # Some information
    begin_date = pd.Timestamp(year=start_year, month=1, day=1)
    end_date = pd.Timestamp(year=end_year, month=12, day=31)

    if start_year <= today_timestamp.year:
        asteroid_encontered = adp.df_neo_feed[(adp.df_neo_feed["date"] >= begin_date) & (adp.df_neo_feed["date"] < today_timestamp)]["asteroid_id"].unique()
        print(f"Unique asteroid encountered and observed from {start_year} until today: {asteroid_encontered.shape[0]}")

    if end_year >= today_timestamp.year:
        begin = today_timestamp if today_timestamp.year >= start_year else begin_date
        asteroid_predicted = adp.df_neo_feed[(adp.df_neo_feed["date"] > begin) & (adp.df_neo_feed["date"] <= end_date)]["asteroid_id"].unique()
        print(f"Unique asteroid predicted to encounter from {begin} until {end_year}: {asteroid_predicted.shape[0]}")

    # Save the 10 biggest asteroids from events between start_year and end_year
    asteroid_ids_selected = adp.df_neo_feed[(adp.df_neo_feed["date"] >= begin_date) & (adp.df_neo_feed["date"] <= end_date)]["asteroid_id"]
    selected_asteroids = adp.df_asteroids[adp.df_asteroids["asteroid_id"].isin(asteroid_ids_selected)]
    md_text = selected_asteroids.sort_values("estimated_diameter_max", ascending=False).head(10)[
        ["asteroid_neo_reference_id", "asteroid_name", "estimated_diameter_min", "estimated_diameter_max", "absolute_magnitude_h", "links"]
    ].to_markdown(index=False)
    with open(f'biggest_asteroid_between_{start_year}_{end_year}.md', 'w') as f:
        f.write(md_text)
        f.close()

    print(f"Biggest asteroids between {start_year} and {end_year}:")
    print(md_text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Gather data from the "Asteroids - NeoWs" database then create some figure and compute some information.'
    )
    parser.add_argument("--api_key", type=str,
                         help="")
    parser.add_argument("--starting_year", type=int, default=1980,
                         help="Starting year from which the results are computed.")
    parser.add_argument("--last_year", type=int, default=2030,
                         help="Last year from which the results are computed.")
    parser.add_argument("--fn_figure_events", type=str, default="Figure 1 - unique events per year",
                         help="Filename of the outputed figure for the unique events per year.")
    parser.add_argument("--fn_figure_asteroid_size", type=str, default="Figure 2 - asteroid size per year",
                         help="Filename of the outputed figure for the number of asteroid size per year.")

    args = parser.parse_args()
    main(args.api_key, args.fn_figure_events, args.fn_figure_asteroid_size, args.starting_year, args.last_year)