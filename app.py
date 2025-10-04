import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# ----------------------------
# CONFIG
# ----------------------------
METEOMATICS_USERNAME = "kapileshwarkar_vivan"
METEOMATICS_PASSWORD = "2wtUESzE3C4SW9012x4y"
BASE_URL = "https://api.meteomatics.com"

st.title("📍 Weather Probability Dashboard with Map Pin")

# Map input
st.markdown("**Drop a pin on the map to select a location:**")
location = st.map(pd.DataFrame({'lat':[0],'lon':[0]}), zoom=2)  # Initial empty map

# Streamlit doesn’t directly allow interactive pin, so use this workaround:
lat = st.number_input("Latitude", value=40.7128)
lon = st.number_input("Longitude", value=-74.0060)

date = st.date_input("Select Date", datetime.today())
parameter = st.selectbox("Select Variable", {
    "Temperature (°C)": "t_2m:C",
    "Precipitation (mm)": "precip_24h:mm",
    "Windspeed (km/h)": "wind_speed_10m:kmh"
})

# Helper function
def get_meteomatics_data(lat, lon, date, parameter):
    start = date.strftime("%Y-%m-%d")
    end = start
    url = f"{BASE_URL}/{start}T00:00:00Z--{end}T23:59:59Z/{parameter}/{lat},{lon}/json"
    response = requests.get(url, auth=(METEOMATICS_USERNAME, METEOMATICS_PASSWORD))
    if response.status_code == 200:
        data = response.json()["data"][0]["coordinates"][0]["dates"]
        df = pd.DataFrame(data)
        df["validdate"] = pd.to_datetime(df["date"])
        df["value"] = df["value"].astype(float)
        return df
    else:
        st.error(f"API Error {response.status_code}: {response.text}")
        return None

if st.button("Fetch Weather Data"):
    df = get_meteomatics_data(lat, lon, date, parameter)
    if df is not None and not df.empty:
        st.success("✅ Data fetched successfully")
        st.dataframe(df)
        # Plot
        plt.hist(df["value"], bins=10, color="skyblue", edgecolor="black")
        plt.xlabel(parameter)
        plt.ylabel("Frequency")
        plt.title("Historical Data Distribution")
        st.pyplot(plt)
    else:
        st.warning("No data available for this selection")
