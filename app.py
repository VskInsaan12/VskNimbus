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

# ----------------------------
# Helper Function: Get Meteomatics Data
# ----------------------------
def get_meteomatics_data(lat, lon, start_date, end_date, parameter="t_2m:C"):
    url = f"{BASE_URL}/{start_date}T00:00:00Z--{end_date}T23:59:59Z/P1D/{parameter}/{lat},{lon}/json"
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

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="NASA Weather Probability Dashboard", layout="wide")

st.title("🌍 NASA + Meteomatics Weather Probability Dashboard")
st.markdown("""
Get the **probability of specific weather conditions** for any location and date using historical data.
Perfect for outdoor planning, events, and climate insights.
""")

# User input
location = st.text_input("Enter Location (City or Lat,Lon)", "New York")
lat = st.number_input("Latitude", value=40.7128)
lon = st.number_input("Longitude", value=-74.0060)
date = st.date_input("Select Date", datetime.today())
parameter = st.selectbox("Select Variable", {
    "Temperature (2m, °C)": "t_2m:C",
    "Precipitation (mm)": "precip_24h:mm",
    "Windspeed (10m, km/h)": "wind_speed_10m:kmh",
    "Snow Depth (cm)": "snow_depth:cm",
    "Relative Humidity (%)": "relative_humidity_2m:p"
})

years_back = st.slider("How many years of history?", 10, 40, 20)

# ----------------------------
# Fetch Data
# ----------------------------
if st.button("Analyze Weather Probability"):
    start_year = datetime.today().year - years_back
    results = []

    for year in range(start_year, datetime.today().year):
        target_date = date.replace(year=year)
        start = target_date.strftime("%Y-%m-%d")
        end = target_date.strftime("%Y-%m-%d")

        df = get_meteomatics_data(lat, lon, start, end, parameter)
        if df is not None and not df.empty:
            results.append(df)

    if results:
        all_data = pd.concat(results)
        st.success(f"✅ Loaded {len(all_data)} years of data")

        # Stats
        mean_val = all_data["value"].mean()
        threshold = st.number_input("Set threshold for 'extreme' condition", value=30.0)
        prob = (all_data["value"] > threshold).mean() * 100

        st.metric("Mean Value", f"{mean_val:.2f}")
        st.metric("Probability > Threshold", f"{prob:.1f}%")

        # Plot
        fig, ax = plt.subplots()
        ax.hist(all_data["value"], bins=15, color="skyblue", edgecolor="black")
        ax.axvline(threshold, color="red", linestyle="--", label=f"Threshold = {threshold}")
        ax.set_title("Historical Distribution")
        ax.set_xlabel("Value")
        ax.set_ylabel("Frequency")
        ax.legend()
        st.pyplot(fig)

        # Download
        csv = all_data.to_csv(index=False).encode("utf-8")
        st.download_button("Download Data as CSV", csv, "weather_data.csv", "text/csv")

    else:
        st.warning("No data available for this selection.")
