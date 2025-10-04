# app.py — Vsk Nimbus (fixed, robust version)
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
# App config
# ----------------------------
st.set_page_config(page_title="Vsk Nimbus 🌤️", layout="wide", initial_sidebar_state="expanded")
st.title("☁️ Vsk Nimbus — Weather Probability Dashboard")

# ----------------------------
# Logo (try load)
# ----------------------------
try:
    st.image("vsk_nimbus_logo.png", width=120)
except Exception:
    # Don't crash if logo missing
    st.info("Put your logo file as 'vsk_nimbus_logo.png' in app folder if you want it displayed.")

# ----------------------------
# Credentials (recommend using Streamlit secrets)
# ----------------------------
# Recommended: put credentials in .streamlit/secrets.toml:
# [meteomatics]
# username = "..."
# password = "..."
#
# then access with st.secrets["meteomatics"]["username"]
if "meteomatics" in st.secrets:
    METEOMATICS_USERNAME = st.secrets["meteomatics"].get("username")
    METEOMATICS_PASSWORD = st.secrets["meteomatics"].get("password")
else:
    # fallback — replace these with your credentials or set secrets
    METEOMATICS_USERNAME = "insaan_vsk"
    METEOMATICS_PASSWORD = "g1228qgzukF8nj2X5ES9"

BASE_URL = "https://api.meteomatics.com"

# quick credentials check
if not METEOMATICS_USERNAME or not METEOMATICS_PASSWORD:
    st.error("Meteomatics credentials not set. Put them in .streamlit/secrets.toml or assign in code.")
    st.stop()

# ----------------------------
# Sidebar (inputs)
# ----------------------------
st.sidebar.header("Settings")
years_back = st.sidebar.slider("Analyze how many years back?", 5, 40, 20)
variable_dict = {
    "Temperature (°C)": "t_2m:C",
    "Precipitation (mm, 24h)": "precip_24h:mm",
    "Windspeed (km/h)": "wind_speed_10m:kmh"
}
variables_selected = st.sidebar.multiselect("Select Weather Variables", list(variable_dict.keys()),
                                            default=["Temperature (°C)"])
thresholds = {}
for var in variables_selected:
    default = 30.0 if "Temperature" in var else 10.0
    thresholds[var] = st.sidebar.number_input(f"Threshold for {var}", value=float(default))
date = st.sidebar.date_input("Select date (day & month used across years)", datetime.today())

# ----------------------------
# Map: click to choose coords (interactive)
# ----------------------------
st.subheader("🌍 Click on the map to pick a location")
if "lat" not in st.session_state:
    st.session_state.lat = 20.0
if "lon" not in st.session_state:
    st.session_state.lon = 0.0

# Create a map for clicking (no marker yet)
click_map = folium.Map(location=[st.session_state.lat, st.session_state.lon], zoom_start=4, control_scale=True)
map_click = st_folium(click_map, width=800, height=450, returned_objects=["last_clicked"])

# If user clicked, update session_state and re-render a marker map below
if map_click and map_click.get("last_clicked"):
    st.session_state.lat = map_click["last_clicked"]["lat"]
    st.session_state.lon = map_click["last_clicked"]["lng"]

# Show small map with marker so user sees the pointer immediately
marker_map = folium.Map(location=[st.session_state.lat, st.session_state.lon], zoom_start=6, control_scale=True)
folium.Marker([st.session_state.lat, st.session_state.lon],
              popup=f"Lat: {st.session_state.lat:.6f}\nLon: {st.session_state.lon:.6f}",
              icon=folium.Icon(color="blue", icon="map-marker")).add_to(marker_map)
st_folium(marker_map, width=600, height=300)

# Show coords in green box (success)
st.success(f"Selected Latitude: {st.session_state.lat:.6f} , Longitude: {st.session_state.lon:.6f}")

# ----------------------------
# Helper: fetch a single year's data and reduce to one value (mean)
# ----------------------------
def fetch_one_date_mean(lat, lon, single_date_str, parameter):
    """
    Request Meteomatics for one date (00:00--23:59) and return mean value or raise.
    Returns (value, None) on success or (None, error_str) on failure.
    """
    url = f"{BASE_URL}/{single_date_str}T00:00:00Z--{single_date_str}T23:59:59Z/{parameter}/{lat},{lon}/json"
    try:
        resp = requests.get(url, auth=(METEOMATICS_USERNAME, METEOMATICS_PASSWORD), timeout=12)
    except requests.RequestException as e:
        return None, f"Request exception: {e}"
    if resp.status_code != 200:
        # Return status/text for debugging
        return None, f"HTTP {resp.status_code}: {resp.text[:300]}"
    try:
        payload = resp.json()
        # path safety
        dates = payload["data"][0]["coordinates"][0]["dates"]
        values = [d.get("value", None) for d in dates if d.get("value") is not None]
        if not values:
            return None, "No numeric values returned for this date"
        mean_val = float(np.mean(values))
        return mean_val, None
    except Exception as e:
        return None, f"Parse error: {e}"

# ----------------------------
# Fetch historical aggregated per-year (one mean per year)
# ----------------------------
def fetch_historical_by_year(lat, lon, target_date, years_back, parameter):
    """
    For each year in the range, request the target_date with that year and compute mean value for that day.
    Returns (df, errors) where df has columns ['validdate','value'] one row per successful year.
    """
    records = []
    errors = []
    current_year = datetime.today().year
    for y in range(current_year - years_back, current_year):
        # try creating date with year y (skip invalid dates)
        try:
            day_dt = target_date.replace(year=y)
        except Exception:
            errors.append((y, "invalid_date"))
            continue
        single_date_str = day_dt.strftime("%Y-%m-%d")
        val, err = fetch_one_date_mean(lat, lon, single_date_str, parameter)
        if err:
            errors.append((y, err))
            continue
        records.append({"validdate": datetime(y, target_date.month, target_date.day), "value": val, "year": y})
    if records:
        df = pd.DataFrame(records)
        df = df.sort_values("validdate").reset_index(drop=True)
        return df, errors
    else:
        return None, errors

# ----------------------------
# Fetch button placed under coords
# ----------------------------
if st.button("📊 Fetch Weather Data"):
    if not variables_selected:
        st.warning("Select at least one weather variable from the sidebar.")
    else:
        st.info("Fetching data for each year — this may take a few seconds per year depending on API speed...")
        all_data = {}
        fetch_summary = {}
        for var in variables_selected:
            param = variable_dict[var]
            df_var, errors = fetch_historical_by_year(st.session_state.lat, st.session_state.lon, date, years_back, param)
            if df_var is None:
                st.warning(f"No successful years for {var}. See details below.")
                all_data[var] = None
            else:
                all_data[var] = df_var
            fetch_summary[var] = {"years_fetched": int(0 if df_var is None else len(df_var)), "errors": errors}
        st.session_state.all_data = all_data
        st.session_state.fetch_summary = fetch_summary
        st.success("Fetch complete — results saved in session.")

# ----------------------------
# Show fetch summary / errors (if present)
# ----------------------------
if "fetch_summary" in st.session_state:
    st.subheader("Fetch summary")
    for var, info in st.session_state.fetch_summary.items():
        years = info["years_fetched"]
        st.write(f"**{var}** — years fetched: {years}")
        if info["errors"]:
            with st.expander(f"Show errors for {var} ({len(info['errors'])})"):
                for e in info["errors"]:
                    st.write(f"Year {e[0]}: {e[1]}")

# ----------------------------
# Display graphs if data exists
# ----------------------------
if "all_data" in st.session_state and st.session_state.all_data:
    any_shown = False
    for var, df in st.session_state.all_data.items():
        if df is None or df.empty:
            st.error(f"No data to display for {var}.")
            continue
        any_shown = True
        st.subheader(var)
        # Use one value per year (already prepared)
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(df["validdate"], df["value"], marker='o', linestyle='-', color='skyblue', label=var)
        # highlight exceeding years
        thr = thresholds.get(var, None)
        if thr is not None:
            df_exceed = df[df["value"] > thr]
            if not df_exceed.empty:
                ax.scatter(df_exceed["validdate"], df_exceed["value"], color='red', s=90, zorder=6, label=f'> {thr}')
        ax.set_xlabel("Year")
        ax.set_ylabel(var)
        ax.set_title(f"{var} on {date.strftime('%B %d')} — last {years_back} years")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.grid(alpha=0.2)
        ax.legend()
        st.pyplot(fig)

        # probability: years exceeding / available years
        if thr is not None:
            available_years = len(df)
            exceed_count = int((df["value"] > thr).sum())
            prob = (exceed_count / available_years) * 100 if available_years > 0 else 0.0
            color = "green" if prob <= 20 else ("orange" if prob <= 50 else "red")
            st.markdown(f"<h3 style='color:{color}'>{prob:.1f}% chance > {thr}</h3>", unsafe_allow_html=True)

            # remark
            if prob > 50:
                st.warning("⚠️ High chance of extreme weather — consider postponing outdoor activities.")
            elif prob > 20:
                st.info("⚠️ Moderate chance — plan with caution.")
            else:
                st.success("✅ Low chance — safe to proceed.")
    if not any_shown:
        st.info("No valid data available to plot. Check fetch summary for errors.")

    # Combined CSV
    # build combined DF on 'validdate'
    combined = None
    for var, df in st.session_state.all_data.items():
        if df is None:
            continue
        tmp = df[["validdate", "value"]].copy().rename(columns={"value": var})
        if combined is None:
            combined = tmp
        else:
            combined = pd.merge(combined, tmp, on="validdate", how="outer")
    if combined is not None and not combined.empty:
        csv_bytes = combined.to_csv(index=False).encode("utf-8")
        st.download_button("Download Combined CSV", csv_bytes, "vsk_nimbus_data.csv", "text/csv")

# ----------------------------
# Footer
# ----------------------------
st.markdown("---")
st.markdown("<center>Made by Vivan Kapileshwarkar</center>", unsafe_allow_html=True)
