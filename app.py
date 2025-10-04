import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib.dates as mdates
import folium
from streamlit_folium import st_folium

# ----------------------------
# App Configuration
# ----------------------------
st.set_page_config(
    page_title="Vsk Nimbus 🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------
# Logo and Title
# ----------------------------
try:
    st.image("vsk_nimbus_logo.png", width=120)
except:
    st.warning("Logo not found. Place 'vsk_nimbus_logo.png' in the app directory.")

st.markdown("<h1 style='text-align:center'>☁️ Vsk Nimbus: Weather Probability Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center'>Predict historical probability of weather conditions for a location and date</p>", unsafe_allow_html=True)

# ----------------------------
# Meteomatics Credentials
# ----------------------------
METEOMATICS_USERNAME = "insaan_vsk"
METEOMATICS_PASSWORD = "g1228qgzukF8nj2X5ES9"
BASE_URL = "https://api.meteomatics.com"

# ----------------------------
# Sidebar Inputs
# ----------------------------
st.sidebar.header("Settings")
years_back = st.sidebar.slider("Analyze how many years back?", 10, 40, 20)

variable_dict = {
    "Temperature (°C)": "t_2m:C",
    "Precipitation (mm)": "precip_24h:mm",
    "Windspeed (km/h)": "wind_speed_10m:kmh"
}
variables_selected = st.sidebar.multiselect(
    "Select Weather Variables",
    options=list(variable_dict.keys()),
    default=["Temperature (°C)"]
)

thresholds = {}
for var in variables_selected:
    default_threshold = 30.0 if "Temperature" in var else 10.0
    thresholds[var] = st.sidebar.number_input(f"Threshold for {var}", value=default_threshold)

date = st.sidebar.date_input("Select Date", datetime.today())

# ----------------------------
# Interactive Folium Map
# ----------------------------
st.subheader("🌍 Click on the map to select a location")

if "lat" not in st.session_state:
    st.session_state.lat = 20.0
if "lon" not in st.session_state:
    st.session_state.lon = 0.0

m = folium.Map(location=[st.session_state.lat, st.session_state.lon], zoom_start=4)

# Add updated marker
folium.Marker(
    [st.session_state.lat, st.session_state.lon],
    popup=f"Lat: {st.session_state.lat:.2f}, Lon: {st.session_state.lon:.2f}",
    icon=folium.Icon(color="green", icon="info-sign")
).add_to(m)

map_data = st_folium(m, width=700, height=400)

if map_data and map_data.get("last_clicked"):
    st.session_state.lat = map_data["last_clicked"]["lat"]
    st.session_state.lon = map_data["last_clicked"]["lng"]

# Show coords below map
st.success(f"Selected Latitude: {st.session_state.lat:.6f}, Longitude: {st.session_state.lon:.6f}")

# ----------------------------
# Fetch Historical Data Function
# ----------------------------
def fetch_historical(lat, lon, date, years_back, parameter):
    dfs = []
    current_year = datetime.today().year
    for y in range(current_year - years_back, current_year):
        try:
            day = date.replace(year=y)
        except:
            continue
        start = day.strftime("%Y-%m-%d")
        url = f"{BASE_URL}/{start}T00:00:00Z/{parameter}/{lat},{lon}/json"
        try:
            response = requests.get(url, auth=(METEOMATICS_USERNAME, METEOMATICS_PASSWORD), timeout=10)
            response.raise_for_status()
            data = response.json()["data"][0]["coordinates"][0]["dates"]
            df = pd.DataFrame(data)
            df["validdate"] = pd.to_datetime(df["date"])
            df["value"] = df["value"].astype(float)
            dfs.append(df)
        except Exception as e:
            continue
    if dfs:
        return pd.concat(dfs)
    else:
        return None

# ----------------------------
# Fetch Data Button
# ----------------------------
if st.button("📊 Fetch Weather Data"):
    st.info("Fetching historical data... ⏳")
    all_data = {}
    for var in variables_selected:
        param_code = variable_dict[var]
        df = fetch_historical(st.session_state.lat, st.session_state.lon, date, years_back, param_code)
        if df is not None and not df.empty:
            all_data[var] = df
        else:
            st.warning(f"No data available for {var}")
    if all_data:
        st.session_state.all_data = all_data
    else:
        st.error("No historical data found for the selected location and date.")

# ----------------------------
# Display Graphs & Probability
# ----------------------------
if "all_data" in st.session_state and st.session_state.all_data:
    all_data = st.session_state.all_data
    st.success(f"✅ Data fetched successfully for {len(all_data)} variable(s)")

    for var, df in all_data.items():
        st.subheader(f"{var}")
        fig, ax = plt.subplots(figsize=(8,4))
        ax.plot(df["validdate"], df["value"], marker='o', linestyle='-', color='skyblue', label=var)
        df_extreme = df[df["value"] > thresholds[var]]
        if not df_extreme.empty:
            ax.scatter(df_extreme["validdate"], df_extreme["value"], color='red', s=80, zorder=5, label=f'> {thresholds[var]}')
        ax.set_xlabel("Year")
        ax.set_ylabel(var)
        ax.set_title(f"{var} on {date.strftime('%B %d')} over past {years_back} years")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.legend()
        st.pyplot(fig)

        # Probability calculation
        prob = (df["value"] > thresholds[var]).sum() / len(df) * 100
        if prob > 50:
            color = "red"
            remark = "⚠️ High chance of extreme weather — consider postponing outdoor activities."
        elif prob > 20:
            color = "orange"
            remark = "⚠️ Moderate chance — plan with caution."
        else:
            color = "green"
            remark = "✅ Low chance — safe to proceed."
        st.markdown(f"<h3 style='color:{color}'>{prob:.1f}% chance > threshold</h3>", unsafe_allow_html=True)
        st.info(remark)

    # CSV download
    csv_combined = pd.DataFrame()
    for var, df in all_data.items():
        temp = df[["validdate","value"]].copy()
        temp.rename(columns={"value": var}, inplace=True)
        if csv_combined.empty:
            csv_combined = temp
        else:
            csv_combined = pd.merge(csv_combined, temp, on="validdate", how="outer")
    csv_bytes = csv_combined.to_csv(index=False).encode("utf-8")
    st.download_button("Download Combined Data as CSV", csv_bytes, "vsk_nimbus_weather.csv", "text/csv")

# ----------------------------
# Footer
# ----------------------------
st.markdown("---")
st.markdown("<center>Made by Vivan Kapileshwarkar</center>", unsafe_allow_html=True)
