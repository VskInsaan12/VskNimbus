import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import matplotlib.pyplot as plt
from streamlit_folium import st_folium
import folium

st.set_page_config(
    page_title="Vsk Nimbus 🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Display logo
st.image("vsk_nimbus_logo.png", width=120)  # Replace with your logo file path
st.title("☁️ Vsk Nimbus: Weather Probability Dashboard")
st.markdown("Select a location, date, and weather variables to get historical probabilities and recommendations.")
# ----------------------------
# CONFIG
# ----------------------------
METEOMATICS_USERNAME = "kapileshwarkar_vivan"
METEOMATICS_PASSWORD = "2wtUESzE3C4SW9012x4y"
BASE_URL = "https://api.meteomatics.com"

st.sidebar.header("Settings")

# Historical years
years_back = st.sidebar.slider("Analyze how many years back?", 10, 40, 20)

# Weather variables
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

# Thresholds for each variable
thresholds = {}
for var in variables_selected:
    thresholds[var] = st.sidebar.number_input(f"Threshold for {var}", value=30.0 if "Temperature" in var else 10.0)

# Date input
date = st.sidebar.date_input("Select Date", datetime.today())

# ----------------------------
# Map for selecting location
# ----------------------------
st.subheader("📍 Select Location on Map")
default_lat, default_lon = 20, 0
m = folium.Map(location=[default_lat, default_lon], zoom_start=2)
map_data = st_folium(m, width=700, height=400)

if map_data and map_data["last_clicked"]:
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    folium.Marker([lat, lon], popup="Selected Location", tooltip="Selected Location").add_to(m)
    st.success(f"Selected Location: Latitude {lat:.4f}, Longitude {lon:.4f}")
else:
    lat = 40.7128
    lon = -74.0060
    folium.Marker([lat, lon], popup="Default Location", tooltip="Default Location").add_to(m)
    st.info(f"Default Location: Latitude {lat}, Longitude {lon}")

st_folium(m, width=700, height=400)

# ----------------------------
# Function to fetch historical data
# ----------------------------
def fetch_historical(lat, lon, date, years_back, parameter):
    dfs = []
    current_year = datetime.today().year
    for y in range(current_year - years_back, current_year):
        day = date.replace(year=y)
        start = day.strftime("%Y-%m-%d")
        end = start
        url = f"{BASE_URL}/{start}T00:00:00Z--{end}T23:59:59Z/{parameter}/{lat},{lon}/json"
        try:
            response = requests.get(url, auth=(METEOMATICS_USERNAME, METEOMATICS_PASSWORD))
            response.raise_for_status()
            data = response.json()["data"][0]["coordinates"][0]["dates"]
            df = pd.DataFrame(data)
            df["validdate"] = pd.to_datetime(df["date"])
            df["value"] = df["value"].astype(float)
            dfs.append(df)
        except:
            continue
    if dfs:
        return pd.concat(dfs)
    else:
        return None

# ----------------------------
# Fetch & Display Data
# ----------------------------
if st.button("Fetch Weather Data"):
    st.info("Fetching historical data... please wait ⏳")
    all_data = {}
    for var in variables_selected:
        param_code = variable_dict[var].replace(" ", "")
        df = fetch_historical(lat, lon, date, years_back, param_code)
        if df is not None and not df.empty:
            all_data[var] = df
        else:
            st.warning(f"No data available for {var}")

    if all_data:
        st.success(f"✅ Data fetched successfully for {len(all_data)} variable(s)")
        
        # Display metrics and plots in columns
        for var, df in all_data.items():
            st.subheader(f"{var}")
            
            # Time-Trend Plot
            fig, ax = plt.subplots(figsize=(10,4))
            ax.plot(df["validdate"], df["value"], marker='o', linestyle='-', color='skyblue', label=var)
            # Highlight extreme points above threshold
            extreme = df[df["value"] > thresholds[var]]
            ax.scatter(extreme["validdate"], extreme["value"], color='red', label=f'> {thresholds[var]}')
            ax.set_xlabel("Year")
            ax.set_ylabel(var)
            ax.set_title(f"{var} on {date.strftime('%B %d')} over past {years_back} years")
            ax.xaxis.set_major_formatter(DateFormatter("%Y"))
            ax.legend()
            st.pyplot(fig)
            
            # Probability & Remark
            prob = (df["value"] > thresholds[var]).sum() / len(df) * 100
            st.metric(f"Probability > Threshold ({var})", f"{prob:.1f}%")
            
            if prob > 50:
                st.warning("⚠️ High chance of extreme weather — consider postponing the parade.")
            elif prob > 20:
                st.info("⚠️ Moderate chance of extreme weather — plan with caution.")
            else:
                st.success("✅ Low chance of extreme weather — safe to go ahead.")
        
        # Unified CSV Download
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
