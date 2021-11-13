import pandas as pd
import requests

from datetime import datetime


def gather_fireball_data(api_location="https://ssd-api.jpl.nasa.gov/fireball.api"):
    """Parser that retrieve fireball data from NASA open database.

    Details of the API is there: https://ssd-api.jpl.nasa.gov/doc/fireball.html

    Returns
    -------

    Dataframe containing all data from the NASA fireball API.
    Energy of the dataframe is in giga joules.
    """
    database_json = requests.get(api_location).json()

    # cast data
    casted_data = []
    for line in database_json["data"]:
        casted_data.append([
            datetime.fromisoformat(line[0]),
            float(line[1]) if line[1] is not None else float("NaN"),
            float(line[2]) if line[2] is not None else float("NaN"),
            float(line[3]) if line[3] is not None else float("NaN"),
            line[4],
            float(line[5]) if line[5] is not None else float("NaN"),
            line[6],
            float(line[7]) if line[7] is not None else float("NaN"),
            float(line[8]) if line[8] is not None else float("NaN")
        ])


    df =  pd.DataFrame(casted_data, columns=database_json['fields'])
    df["energy"] = df["energy"]*10
    return df