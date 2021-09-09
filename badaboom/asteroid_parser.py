"""
This module provides a parser to gather data from the 'Asteroids - NeoWs' database.
Souces of the database: https://api.nasa.gov/
"""
import pandas as pd
import numpy as np
import requests

from os.path import exists
from time import sleep


class AsteroidDatasetParser:
    """Parser to retrieve asteroids dataset from the open data provided by NASA.

    Compatible with the data: Asteroids - NeoWs

    The data will be stored into two dataframes.
    The first dataframe will store the events registered (in the df_neo_feed variable).
    The second dataframe will store the asteroid information (in the df_asteroids variable).
    These two dataframes can be joined using the asteroid ID.
    """

    def __init__(self, api_key,
                 local_neo_feed_datapath="neo_feed_data.csv", local_asteroid_datapath="asteroid_data.csv",
                 api_location="https://api.nasa.gov/neo/rest/v1/") -> None:
        """
        Parameters
        ----------

        api_key: (str)
            Your API key provided by NASA, see https://api.nasa.gov/ for more details.

        local_neo_feed_datapath: (str)
            Path where the events dataframe will be saved/loaded.

        local_asteroid_datapath: (str)
            Path where the asteroids dataframe will be saved/loaded.

        api_location: (str)
            Url to the 'Asteroids - NeoWs' API.
        """
        self.api_location = api_location
        self.api_key = api_key
        self.local_neo_feed_datapath = local_neo_feed_datapath
        self.local_asteroid_datapath = local_asteroid_datapath

        # Do a dummy request to check the remaining requests available
        query = f"feed?start_date=2015-12-30&end_date=2015-12-30&api_key={api_key}"
        r = requests.get(api_location + query)
        self.remaining_requests = int(r.headers['X-RateLimit-Remaining'])

         # load existing dataframes and list known asteroids
        if not exists(self.local_neo_feed_datapath):
            self.df_neo_feed = pd.DataFrame([], columns=self.events_desc)
            self.df_asteroids = pd.DataFrame([], columns=self.asteroids_desc)
            self.known_asteroids = []
        else:
            self.df_neo_feed = pd.read_csv(self.local_neo_feed_datapath, parse_dates=["date"])
            self.df_asteroids = pd.read_csv(self.local_asteroid_datapath)
            self.known_asteroids = self.df_asteroids["asteroid_id"].to_list()


    def retrieve_year_dataframe(self, year):
        """Return dataframe_corresponding to year.

        Download the data if requiered and save it in the local database is required.
        """
        begin_year = pd.Timestamp(year=year, month=1, day=1)
        end_year = pd.Timestamp(year=year, month=12, day=31)

        selected_df_neo_feed = self.df_neo_feed[(self.df_neo_feed["date"] >= begin_year) & (self.df_neo_feed["date"] <= end_year)]
        selected_df_asteroids = self.df_asteroids[self.df_asteroids["asteroid_id"].isin(selected_df_neo_feed["asteroid_id"])]

        if len(selected_df_neo_feed) <= 0 or selected_df_neo_feed["is_estimation"].any():
            # remove year data if any to be safe about estimations
            index_to_remove = self.df_neo_feed[(self.df_neo_feed["date"] >= begin_year) & (self.df_neo_feed["date"] <= end_year)].index
            self.df_neo_feed.drop(index_to_remove, inplace=True)

            # fill year
            start_date = begin_year
            end_date = start_date + pd.Timedelta(days=6)
            while start_date <= end_year: # TODO maybe a tqdm progress bar?
                self._download_week_informations(start_date, end_date)

                # prepare next date
                start_date = end_date + pd.Timedelta(days=1)
                end_date = start_date + pd.Timedelta(days=6)
                if end_date > end_year:
                    end_date = end_year

            self.df_neo_feed.to_csv(self.local_neo_feed_datapath, sep=',', index=False)
            self.df_asteroids.to_csv(self.local_asteroid_datapath, sep=',', index=False)

            selected_df_neo_feed = self.df_neo_feed[(self.df_neo_feed["date"] >= begin_year) & (self.df_neo_feed["date"] <= end_year)]
            selected_df_asteroids = self.df_asteroids[self.df_asteroids["asteroid_id"].isin(selected_df_neo_feed["asteroid_id"])]

        return selected_df_neo_feed, selected_df_asteroids

    @property
    def local_df_neo_feed(self):
        return self.df_neo_feed

    @property
    def local_df_asteroids(self):
        return self.df_asteroids

    def _download_week_informations(self, start_date, end_date):
        """The download is week by week as it is a limitation of the 'Asteroids - NeoWs' API.

        It updates the dataframes.
        Warning: It supposes the week does not exists in the local dataframes.
        """
        if self.remaining_requests < 1:
            print("You have reached your hourly number of requests possible.")
            print("The program will pause for 1 hour to be able to retrieve the data.")
            sleep(3600)

        query = f"feed?start_date={start_date}&end_date={end_date}&api_key={self.api_key}"
        r = requests.get(self.api_location + query)
        self.remaining_requests = int(r.headers['X-RateLimit-Remaining'])

        week_dict = r.json()

        events_list = []
        asteroids_list_to_add = []
        today_timestamp = pd.Timestamp.today()
        for event_date in week_dict["near_earth_objects"]:
            for asteroid_event in week_dict["near_earth_objects"][event_date]:
                try:
                    event_timestamp = pd.Timestamp(event_date)
                    asteroid_id = int(asteroid_event["id"])
                    events_list.append([
                        event_timestamp, asteroid_id, int(asteroid_event['neo_reference_id']),
                        bool(asteroid_event['is_potentially_hazardous_asteroid']), event_timestamp >= today_timestamp,
                        float(asteroid_event["close_approach_data"][0]["relative_velocity"]["kilometers_per_second"]),
                        float(asteroid_event["close_approach_data"][0]["miss_distance"]["kilometers"])
                    ])

                    if asteroid_id not in self.known_asteroids:
                        if "absolute_magnitude_h" in asteroid_event.keys(): # this information is sometimes missing
                            magnitude_info = float(asteroid_event["absolute_magnitude_h"])
                        else:
                            magnitude_info = np.nan

                        if 'estimated_diameter' not in asteroid_event.keys(): # this information is sometimes missing
                            estimated_diameter_min = np.nan
                            estimated_diameter_max = np.nan
                        else:
                            estimated_diameter_min = float(asteroid_event['estimated_diameter']["kilometers"]["estimated_diameter_min"])
                            estimated_diameter_max = float(asteroid_event['estimated_diameter']["kilometers"]["estimated_diameter_max"])

                        self.known_asteroids.append(asteroid_id)
                        asteroids_list_to_add.append([
                            asteroid_id, int(asteroid_event['neo_reference_id']), asteroid_event["name"],
                            bool(asteroid_event['is_potentially_hazardous_asteroid']), bool(asteroid_event["is_sentry_object"]),
                            magnitude_info, asteroid_event["nasa_jpl_url"],
                            estimated_diameter_min, estimated_diameter_max
                        ])

                except KeyError as e:
                    print("Event received:")
                    print(asteroid_event)
                    print("Week revceived:")
                    print(week_dict)
                    raise Exception(f"Error unexpected, key {e} is missing.")

        # update local df, it supposes the new week does not exist in the local dataframes
        df_events = pd.DataFrame(events_list, columns=self.events_desc)
        self.df_neo_feed = self.df_neo_feed.append(df_events, ignore_index=True).sort_values(by='date')
        if len(asteroids_list_to_add) > 0:
            df_asteroids_to_add = pd.DataFrame(asteroids_list_to_add, columns=self.asteroids_desc)
            self.df_asteroids = self.df_asteroids.append(df_asteroids_to_add, ignore_index=True).sort_values(by='asteroid_id')

    @property
    def events_desc(self):
        return ["date", "asteroid_id",
                "asteroid_neo_reference_id", "is_potentially_hazardous_asteroid", "is_estimation",
                "relative_velocity_kms", "miss_distance"] # velociy in kilometers per secondes and distance in kilometers

    @property
    def asteroids_desc(self):
        return ["asteroid_id", "asteroid_neo_reference_id", "asteroid_name",
                "is_potentially_hazardous_asteroid", "is_sentry_object",
                "absolute_magnitude_h", "links",
                "estimated_diameter_min", "estimated_diameter_max"] # in kilometers
