import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import matplotlib.pyplot as plt
from streamlit_folium import st_folium
import folium
# ----------------------------
# CONFIG
# ----------------------------
METEOMATICS_USERNAME = "kapileshwarkar_vivan"
METEOMATICS_PASSWORD = "2wtUESzE3C4SW9012x4y"
BASE_URL = "https://api.meteomatics.com"

st.set_page_config(page_title="NASA Weather Probability Dashboard", layout="wide")
st.title("📍 Weather Probability Dashboard with Map Pin")
st.markdown("Click on the map to select a location:")

# ----------------------------
# Map for user to click
# ----------------------------
m = folium.Map(location=[20,0], zoom_start=2)
map_data = st_folium(m, width=700, height=400)

if map_data and map_data["last_clicked"]:
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    st.success(f"Selected Location: Latitude {lat:.4f}, Longitude {lon:.4f}")
else:
    # Default fallback location
    lat = 40.7128
    lon = -74.0060
    st.info(f"Default Location: Latitude {lat}, Longitude {lon}")

# ----------------------------
# Date & Variable selection
# ----------------------------
date = st.date_input("Select Date", datetime.today())

variable_dict = {
    "Temperature (°C)": "t_2m:C",
    "Precipitation (mm)": "precip_24h:mm",
    "Windspeed (km/h)": "wind_speed_10m:kmh"
}

parameter = variable_dict[st.selectbox("Select Variable", list(variable_dict.keys()))]

# Remove any accidental whitespace
parameter = parameter.replace(" ", "")

# ----------------------------
# Function to fetch Meteomatics data
# ----------------------------
def get_meteomatics_data(lat, lon, date, parameter):
    start = date.strftime("%Y-%m-%d")
    end = start
    url = f"{BASE_URL}/{start}T00:00:00Z--{end}T23:59:59Z/{parameter}/{lat},{lon}/json"
    try:
        response = requests.get(url, auth=(METEOMATICS_USERNAME, METEOMATICS_PASSWORD))
        response.raise_for_status()
        data = response.json()["data"][0]["coordinates"][0]["dates"]
        df = pd.DataFrame(data)
        df["validdate"] = pd.to_datetime(df["date"])
        df["value"] = df["value"].astype(float)
        return df
    except requests.exceptions.HTTPError as e:
        st.error(f"API Error {response.status_code}: {response.text}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return None

# ----------------------------
# Fetch & display data
# ----------------------------
if st.button("Fetch Weather Data"):
    df = get_meteomatics_data(lat, lon, date, parameter)
    if df is not None and not df.empty:
        st.success("✅ Data fetched successfully")
        st.dataframe(df)

        # Histogram
        fig, ax = plt.subplots()
        ax.hist(df["value"], bins=10, color="skyblue", edgecolor="black")
        ax.set_xlabel(parameter)
        ax.set_ylabel("Frequency")
        ax.set_title("Historical Data Distribution")
        st.pyplot(fig)

        # Probability above threshold
        threshold = st.number_input("Set threshold for 'extreme' condition", value=30.0)
        prob = (df["value"] > threshold).mean() * 100
        st.metric("Probability > Threshold", f"{prob:.1f}%")

        # CSV download
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Data as CSV", csv, "weather_data.csv", "text/csv")
    else:
        st.warning("No data available for this selection")
