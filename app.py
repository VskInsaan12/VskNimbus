# app.py — Vsk Nimbus (single-fast-map, robust final)
import streamlit as st
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib.dates as mdates
import folium
from streamlit_folium import st_folium

# ----------------------------
# App configuration
# ----------------------------
st.set_page_config(page_title="Vsk Nimbus 🌤️", layout="wide", initial_sidebar_state="expanded")
st.title("☁️ Vsk Nimbus — Weather Probability Dashboard")

# ----------------------------
# Logo
# ----------------------------
try:
    st.image("vsk_nimbus_logo.png", width=120)
except Exception:
    # silent if missing
    pass

# ----------------------------
# Credentials
# ----------------------------
if "meteomatics" in st.secrets:
    METEOMATICS_USERNAME = st.secrets["meteomatics"].get("username")
    METEOMATICS_PASSWORD = st.secrets["meteomatics"].get("password")
else:
    METEOMATICS_USERNAME = "insaan_vsk"
    METEOMATICS_PASSWORD = "g1228qgzukF8nj2X5ES9"


BASE_URL = "https://api.meteomatics.com"

# Credentials check
if not METEOMATICS_USERNAME or not METEOMATICS_PASSWORD or "<YOUR_METEOMATICS" in METEOMATICS_USERNAME:
    st.warning("Meteomatics credentials are not set. Add them to .streamlit/secrets.toml or edit variables in code.")
    st.info("Without valid credentials, the app will attempt requests but likely return errors from the API.")

# ----------------------------
# Sidebar controls
# ----------------------------
st.sidebar.header("Settings")
years_back = st.sidebar.slider("Analyze how many years back?", min_value=5, max_value=40, value=20, step=1)

variable_dict = {
    "Temperature (°C)": "t_2m:C",
    "Precipitation (mm, 24h)": "precip_24h:mm",
    "Windspeed (km/h)": "wind_speed_10m:kmh"
}
variables_selected = st.sidebar.multiselect("Select Weather Variables", list(variable_dict.keys()),
                                            default=["Temperature (°C)"])

# per-variable thresholds
thresholds = {}
for var in variables_selected:
    default = 30.0 if "Temperature" in var else 10.0
    thresholds[var] = st.sidebar.number_input(f"Threshold for {var}", value=float(default))

date = st.sidebar.date_input("Select date (day & month used across years)", datetime.today())

# ----------------------------
# Session state defaults
# ----------------------------
if "lat" not in st.session_state:
    st.session_state.lat = 20.0
if "lon" not in st.session_state:
    st.session_state.lon = 0.0
if "all_data" not in st.session_state:
    st.session_state.all_data = {}
if "fetch_summary" not in st.session_state:
    st.session_state.fetch_summary = {}

# ----------------------------
# Single interactive Folium map (click -> move marker)
# ----------------------------
st.subheader("🌍 Click on the map to select a location")

# Build map centered at current session coords and add a marker there
m = folium.Map(location=[st.session_state.lat, st.session_state.lon], zoom_start=5, control_scale=True)
folium.TileLayer("OpenStreetMap").add_to(m)
folium.Marker(
    [st.session_state.lat, st.session_state.lon],
    popup=f"Selected: {st.session_state.lat:.6f}, {st.session_state.lon:.6f}",
    icon=folium.Icon(color="blue", icon="map-marker")
).add_to(m)

# st_folium returns the last click in 'last_clicked'
map_data = st_folium(m, width=900, height=500, returned_objects=["last_clicked"])

# Update coords immediately if clicked
if map_data and map_data.get("last_clicked"):
    clicked = map_data["last_clicked"]
    # update only when click exists
    st.session_state.lat = float(clicked["lat"])
    st.session_state.lon = float(clicked["lng"])

# Show coords under the map in a green box
st.success(f"📍 Selected Latitude: {st.session_state.lat:.6f} , Longitude: {st.session_state.lon:.6f}")

# ----------------------------
# Helper functions to fetch Meteomatics data
# ----------------------------
def fetch_one_date_mean(lat, lon, single_date_str, parameter):
    """
    Fetch values for a single day's full-time window and return mean value.
    Returns (value, error_message). On success, error_message is None.
    """
    url = f"{BASE_URL}/{single_date_str}T00:00:00Z--{single_date_str}T23:59:59Z/{parameter}/{lat},{lon}/json"
    try:
        resp = requests.get(url, auth=(METEOMATICS_USERNAME, METEOMATICS_PASSWORD), timeout=12)
    except Exception as e:
        return None, f"Request exception: {e}"
    if resp.status_code != 200:
        return None, f"HTTP {resp.status_code}: {resp.text[:400]}"
    try:
        payload = resp.json()
        dates = payload["data"][0]["coordinates"][0]["dates"]
        values = [d["value"] for d in dates if ("value" in d and d["value"] is not None)]
        if not values:
            return None, "No numeric values for this date"
        return float(np.mean(values)), None
    except Exception as e:
        return None, f"Parse error: {e}"

def fetch_historical_by_year(lat, lon, target_date, years_back, parameter):
    """
    Loop over years and request the given month/day for each year; return DataFrame and error list.
    DataFrame columns: ['validdate','value','year'] sorted by year asc.
    """
    records = []
    errors = []
    current_year = datetime.today().year
    for y in range(current_year - years_back, current_year):
        try:
            day_dt = target_date.replace(year=y)
        except Exception:
            errors.append((y, "invalid_date_for_year"))
            continue
        date_str = day_dt.strftime("%Y-%m-%d")
        val, err = fetch_one_date_mean(lat, lon, date_str, parameter)
        if err:
            errors.append((y, err))
            continue
        records.append({"validdate": datetime(y, target_date.month, target_date.day), "value": val, "year": y})
    if records:
        df = pd.DataFrame(records).sort_values("validdate").reset_index(drop=True)
        return df, errors
    else:
        return None, errors

# ----------------------------
# Fetch button (below coords)
# ----------------------------
if st.button("📊 Fetch Weather Data"):
    if not variables_selected:
        st.warning("Select at least one weather variable in the sidebar.")
    else:
        st.info("Fetching historical data — this may take a few seconds per year depending on API speed and your quota...")
        all_data = {}
        summary = {}
        # iterate variables
        for var in variables_selected:
            param = variable_dict[var]
            df_var, errors = fetch_historical_by_year(st.session_state.lat, st.session_state.lon, date, years_back, param)
            # store results and summary
            all_data[var] = df_var  # can be None
            summary[var] = {"years_fetched": 0 if df_var is None else len(df_var), "errors": errors}
        st.session_state.all_data = all_data
        st.session_state.fetch_summary = summary
        st.success("Fetch finished and stored in session state.")

# ----------------------------
# Show fetch summary and possible errors (expanders)
# ----------------------------
if st.session_state.get("fetch_summary"):
    st.subheader("Fetch summary")
    for var, info in st.session_state.fetch_summary.items():
        st.write(f"**{var}** — years fetched: {info['years_fetched']}")
        if info["errors"]:
            with st.expander(f"Show errors for {var} ({len(info['errors'])})"):
                for yr, err in info["errors"]:
                    st.write(f"- Year {yr}: {err}")

# ----------------------------
# Display graphs & probability (persistent)
# ----------------------------
if st.session_state.get("all_data"):
    displayed_any = False
    for var, df in st.session_state.all_data.items():
        if df is None or df.empty:
            st.error(f"No data available to plot for {var}.")
            continue
        displayed_any = True
        st.subheader(var)
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(df["validdate"], df["value"], marker='o', linestyle='-', color='skyblue', label=var)
        thr = thresholds.get(var, None)
        if thr is not None:
            df_exceed = df[df["value"] > thr]
            if not df_exceed.empty:
                ax.scatter(df_exceed["validdate"], df_exceed["value"], color='red', s=90, zorder=6, label=f'> {thr}')
        ax.set_xlabel("Year")
        ax.set_ylabel(var)
        ax.set_title(f"{var} on {date.strftime('%B %d')} — last {years_back} years")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.grid(alpha=0.25)
        ax.legend()
        st.pyplot(fig)

        # probability
        if thr is not None:
            available_years = len(df)
            exceed = int((df["value"] > thr).sum())
            prob = (exceed / available_years) * 100 if available_years > 0 else 0.0
            color = "green" if prob <= 20 else ("orange" if prob <= 50 else "red")
            st.markdown(f"<h3 style='color:{color}'>{prob:.1f}% chance > {thr}</h3>", unsafe_allow_html=True)
            if prob > 50:
                st.warning("⚠️ High chance of extreme weather — consider postponing outdoor activities.")
            elif prob > 20:
                st.info("⚠️ Moderate chance — plan with caution.")
            else:
                st.success("✅ Low chance — safe to proceed.")

    if displayed_any:
        # combined CSV
        combined = None
        for var, df in st.session_state.all_data.items():
            if df is None or df.empty:
                continue
            tmp = df[["validdate", "value"]].copy().rename(columns={"value": var})
            if combined is None:
                combined = tmp
            else:
                combined = pd.merge(combined, tmp, on="validdate", how="outer")
        if combined is not None and not combined.empty:
            csv_bytes = combined.to_csv(index=False).encode("utf-8")
            st.download_button("Download combined CSV", csv_bytes, "vsk_nimbus_data.csv", "text/csv")
    else:
        st.info("No valid data to display. Check the fetch summary for errors (likely authentication or data availability).")

# ----------------------------
# Footer
# ----------------------------
st.markdown("---")
st.markdown("<center>Made by Vivan Kapileshwarkar</center>", unsafe_allow_html=True)



