from datetime import datetime
from unittest.mock import patch

import pandas as pd
import pytest

from badaboom.parsers.fireballs import gather_fireball_data

# Sample response data for mocking
sample_api_response = {
    "data": [
        ["2021-01-01T00:00:00", "1.1", "2.2", "3.3", "Type1", "4.4", "Source1", "5.5", "6.6"],
        ["2021-02-01T00:00:00", None, "2.3", None, "Type2", "4.5", "Source2", "5.6", None],
    ],
    "fields": ["date", "energy", "impact-e", "alt", "lat", "lon", "source", "vx", "vy"],
}


@pytest.fixture
def mock_response():
    """Fixture to provide a mock response object."""

    class MockResponse:
        @staticmethod
        def json():
            return sample_api_response

    return MockResponse()


@patch("requests.get")
def test_gather_fireball_data(mock_get, mock_response):
    """Test the gather_fireball_data function with mocked API response."""
    mock_get.return_value = mock_response

    df = gather_fireball_data()

    # Verify the dataframe
    assert isinstance(df, pd.DataFrame), "The result should be a DataFrame."
    assert (
        list(df.columns) == sample_api_response["fields"]
    ), "The columns do not match the expected fields."
    assert len(df) == len(
        sample_api_response["data"]
    ), "The number of rows in the DataFrame is incorrect."

    # Check the data in the first row
    row = df.iloc[0]
    assert row["date"] == datetime.fromisoformat(
        sample_api_response["data"][0][0]
    ), "Date value is incorrect."
    assert (
        row["energy"] == float(sample_api_response["data"][0][1]) * 10
    ), "Energy value is incorrect."
    assert row["impact-e"] == float(
        sample_api_response["data"][0][2]
    ), "Impact-e value is incorrect."
    assert row["alt"] == float(sample_api_response["data"][0][3]), "Altitude value is incorrect."
    assert row["lat"] == sample_api_response["data"][0][4], "Latitude value is incorrect."
    assert row["lon"] == float(sample_api_response["data"][0][5]), "Longitude value is incorrect."
    assert row["source"] == sample_api_response["data"][0][6], "Source value is incorrect."
    assert row["vx"] == float(sample_api_response["data"][0][7]), "Vx value is incorrect."
    assert row["vy"] == float(sample_api_response["data"][0][8]), "Vy value is incorrect."

    # Check for NaN values in the second row
    row = df.iloc[1]
    assert pd.isna(row["energy"]), "Energy value should be NaN."
    assert row["impact-e"] == float(
        sample_api_response["data"][1][2]
    ), "Impact-e value is incorrect."
    assert pd.isna(row["alt"]), "Altitude value should be NaN."
    assert row["lat"] == sample_api_response["data"][1][4], "Latitude value is incorrect."
    assert row["lon"] == float(sample_api_response["data"][1][5]), "Longitude value is incorrect."
    assert row["source"] == sample_api_response["data"][1][6], "Source value is incorrect."
    assert row["vx"] == float(sample_api_response["data"][1][7]), "Vx value is incorrect."
    assert pd.isna(row["vy"]), "Vy value should be NaN."
