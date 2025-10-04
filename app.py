import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib.dates as mdates

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
st.image("vsk_nimbus_logo.png", width=120)
st.markdown("<h1 style='text-align:center'>☁️ Vsk Nimbus: Weather Probability Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center'>Predict historical probability of weather conditions for a location and date</p>", unsafe_allow_html=True)

# ----------------------------
# Meteomatics Credentials
# ----------------------------
METEOMATICS_USERNAME = "kapileshwarkar_vivan"
METEOMATICS_PASSWORD = "2wtUESzE3C4SW9012x4y"
BASE_URL = "https://api.meteomatics.com"

# ----------------------------
# Help Button
# ----------------------------
if st.button("❓ Get Help"):
    st.info("""
**How to use Vsk Nimbus:**
1. Enter latitude and longitude for your location.  
2. Use the sidebar to select:  
   - Weather variables (temperature, precipitation, windspeed).  
   - Threshold values to define extreme conditions.  
   - Date and number of years back for historical analysis.  
3. Click 'Fetch Weather Data' to view:  
   - Time-trend graphs (red dots indicate extreme values).  
   - Probability of exceeding thresholds with colored text (green/orange/red).  
4. Download the data as CSV if needed.
""")

# ----------------------------
# Sidebar Inputs
# ----------------------------
st.sidebar.header("Settings")
lat = st.sidebar.number_input("Latitude", value=20.0, format="%.6f")
lon = st.sidebar.number_input("Longitude", value=0.0, format="%.6f")
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
# Fetch Historical Data Function
# ----------------------------
def fetch_historical(lat, lon, date, years_back, parameter):
    dfs = []
    current_year = datetime.today().year
    for y in range(current_year - years_back, current_year):
        day = date.replace(year=y)
        start = day.strftime("%Y-%m-%d")
        url = f"{BASE_URL}/{start}T00:00:00Z--{start}T23:59:59Z/{parameter}/{lat},{lon}/json"
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
# Persistent Data Storage
# ----------------------------
if "all_data" not in st.session_state:
    st.session_state.all_data = None

# Fetch data only on button click
fetch_clicked = st.button("Fetch Weather Data")
if fetch_clicked:
    st.info("Fetching historical data... ⏳")
    all_data = {}
    for var in variables_selected:
        param_code = variable_dict[var].replace(" ", "")
        df = fetch_historical(lat, lon, date, years_back, param_code)
        if df is not None and not df.empty:
            all_data[var] = df
        else:
            st.warning(f"No data available for {var}")
    st.session_state.all_data = all_data

# ----------------------------
# Display Graphs and Probability
# ----------------------------
if st.session_state.all_data:
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
        # Color-coded percentage text
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
