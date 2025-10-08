# Vsk Nimbus 🌤️

An interactive weather probability dashboard using NASA Earth observation data.

---

## Project Overview

**Vsk Nimbus** allows users to explore historical weather data for any location and date. Users can:

- Pinpoint a location on an interactive map.
- Select weather variables such as temperature, precipitation, and windspeed.
- Set thresholds for extreme conditions.
- Fetch historical data spanning multiple years.
- Visualize trends via graphs with extreme event markers.
- Calculate the probability of exceeding thresholds and receive actionable remarks.
- Download historical datasets as CSV for further analysis.

The app provides insights to help plan outdoor activities safely by highlighting likely extreme weather events.

---

## AI Tools Used

AI tools (ChatGPT/GPT-5) were utilized to:

- optimize Python/Streamlit code.
- Suggest UI/UX design improvements and layout structure.
- Draft project documentation, summaries, and explanations.
- For Improving the English language used in the project

> All AI-generated code and documentation were reviewed and modified to ensure correctness, originality, and functionality.  
> No NASA branding, logos, or mission identifiers were used or modified.

---

## Features

- Interactive Folium map with click-to-update coordinates.
- Instant marker update when a location is clicked.
- Latitude and longitude displayed above the **Fetch Data** button.
- Graphs with red dots for threshold exceedances.
- Probability calculations with color-coded remarks.
- Downloadable CSV of historical weather data.
- Responsive design for mobile, tablet, desktop, TV, and smartwatches.
- Help popup explaining how to use the app.
- Footer crediting the developer.

---

## Tools & Technologies

- **Python 3.10+**
- **Streamlit** – interactive web interface
- **Folium & streamlit_folium** – interactive maps
- **Pandas** – data handling
- **Matplotlib** – plotting and visualization
- **Meteomatics API** – NASA Earth observation weather data
- Session state management for persistent data

---

## Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/vsk-nimbus.git
cd vsk-nimbus
