Vsk Nimbus 🌤️

An interactive weather probability dashboard using NASA Earth observation data.

Project Overview

Vsk Nimbus allows users to explore historical weather data for any location and date. Users can:

Pinpoint a location on an interactive map.

Select weather variables like temperature, precipitation, and windspeed.

Set thresholds for extreme conditions.

Fetch historical data spanning multiple years.

Visualize trends via graphs with extreme event markers.

Calculate probability of exceeding thresholds and receive actionable remarks.

Download historical datasets as CSV for further analysis.

The app provides insights that help plan outdoor activities safely by highlighting likely extreme weather events.

AI Tools Used

AI tools (ChatGPT/GPT-5) were utilized to:

Generate and optimize Python/Streamlit code.

Suggest UI/UX design improvements and layout structure.

Draft project documentation, summaries, and explanations.

All AI-generated code and documentation were reviewed and modified to ensure correctness, originality, and functionality.

No NASA branding, logos, or mission identifiers were used or modified.

Features

Interactive Folium map with click-to-update coordinates.

Marker updates instantly when location is clicked.

Latitude and longitude displayed above the “Fetch Data” button.

Graphs with red dots for threshold exceedances.

Probability calculations with color-coded remarks.

Downloadable CSV of historical weather data.

Responsive design for mobile, tablet, desktop, TV, and smartwatches.

Help popup explaining how to use the app.

Footer crediting the developer.

Tools & Technologies

Python 3.10+

Streamlit – interactive web interface

Folium & streamlit_folium – interactive maps

Pandas – data handling

Matplotlib – plotting and visualization

Meteomatics API – NASA Earth observation weather data

Session state management for persistent data

Installation

Clone the repository:

git clone https://github.com/yourusername/vsk-nimbus.git
cd vsk-nimbus


Create and activate a virtual environment:

python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows


Install dependencies:

pip install -r requirements.txt


Add Meteomatics credentials in app.py or secrets.toml.

Run the app:

streamlit run app.py

File Structure
vsk-nimbus/
│
├── app.py                  # Main Streamlit app
├── requirements.txt        # Python dependencies
├── vsk_nimbus_logo.png     # App logo (optional)
├── README.md               # Project documentation
└── secrets.toml            # Meteomatics credentials (optional)

License & Credits

Made by Vivan Kapileshwarkar.

AI tools were used to accelerate development and document the project, fully acknowledged above. All AI-generated content has been reviewed and modified.
