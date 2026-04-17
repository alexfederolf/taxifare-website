
import streamlit as st
import requests
from datetime import datetime
import pandas as pd
from math import radians, sin, cos, sqrt, atan2

# ──────────────────────────────────────────────
# Page setup
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Taxi Fare Estimator",
    page_icon="🚕",
    layout="wide",
)

st.title("🚕 Taxi Fare Estimator")
st.caption("Enter your ride details on the left, preview the route on the right, then hit the button!")

st.divider()


# ──────────────────────────────────────────────
# Helper: calculate straight-line distance (km)
# ──────────────────────────────────────────────
def haversine(lat1, lon1, lat2, lon2):
    """Returns the distance in km between two GPS coordinates."""
    R = 6371  # Earth's radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


# ──────────────────────────────────────────────
# Layout: two columns
# Left  --> all user inputs
# Right --> map preview
# ──────────────────────────────────────────────
col_inputs, col_map = st.columns([1, 1.4], gap="large")

# ── LEFT COLUMN: inputs ──
with col_inputs:

    # --- Date & time ---
    st.subheader("📅 When?")
    date_col, time_col = st.columns(2)
    with date_col:
        pickup_date = st.date_input("Pickup date")
    with time_col:
        pickup_time = st.time_input("Pickup time")

    # Combining date + time into one datetime object (required by the API)
    pickup_datetime = datetime.combine(pickup_date, pickup_time)

    st.divider()

    # --- Pickup location ---
    st.subheader("📍 Pickup location")
    st.caption("Default values are set to a central Manhattan location.")

    pickup_lat_col, pickup_lon_col = st.columns(2)
    with pickup_lat_col:
        pickup_latitude = st.number_input(
            "Latitude",
            value=40.7484,
            format="%.4f",
            help="Latitude of where you're getting picked up.",
            key="pickup_lat",
        )
    with pickup_lon_col:
        pickup_longitude = st.number_input(
            "Longitude",
            value=-73.9857,
            format="%.4f",
            help="Longitude of where you're getting picked up.",
            key="pickup_lon",
        )

    st.divider()

    # --- Dropoff location ---
    st.subheader("🏁 Dropoff location")

    dropoff_lat_col, dropoff_lon_col = st.columns(2)
    with dropoff_lat_col:
        dropoff_latitude = st.number_input(
            "Latitude",
            value=40.7580,
            format="%.4f",
            help="Latitude of your destination.",
            key="dropoff_lat",
        )
    with dropoff_lon_col:
        dropoff_longitude = st.number_input(
            "Longitude",
            value=-73.9851,
            format="%.4f",
            help="Longitude of your destination.",
            key="dropoff_lon",
        )

    st.divider()

    # --- Passengers ---
    st.subheader("👥 Passengers")
    passenger_count = st.slider(
        "How many people?",
        min_value=1,
        max_value=8,
        value=1,
        help="Number of passengers in the taxi.",
    )

    st.divider()

    # --- Quick stats ---
    distance_km = haversine(
        pickup_latitude, pickup_longitude,
        dropoff_latitude, dropoff_longitude,
    )

    stat_col1, stat_col2 = st.columns(2)
    stat_col1.metric("📏 Distance", f"{distance_km:.2f} km")
    stat_col2.metric("👥 Passengers", passenger_count)

    st.markdown("")  # small spacer

    # --- Predict button ---
    predict_clicked = st.button("💰 Predict fare", use_container_width=True)


# ── RIGHT COLUMN: map ──
with col_map:
    st.subheader("🗺️ Route preview")
    st.caption("🟢 pickup      ·     🔴 dropoff")

    # Build a simple DataFrame with both points for st.map
    # st.map reads columns named "lat" and "lon"
    map_data = pd.DataFrame({
        "lat":   [pickup_latitude,  dropoff_latitude],
        "lon":   [pickup_longitude, dropoff_longitude],
        "color": [
            [0, 200, 100, 200],    # green for pickup
            [220, 50, 50, 200],    # red for dropoff
        ],
        "size":  [80, 80],
    })

    st.map(
        map_data,
        latitude="lat",
        longitude="lon",
        color="color",
        size="size",
        zoom=12,
    )


# ──────────────────────────────────────────────
# Fare result 
# ──────────────────────────────────────────────
if predict_clicked:
    st.divider()

    # Build the query parameters the API expects
    params = {
        "pickup_datetime":   pickup_datetime.strftime("%Y-%m-%d %H:%M:%S"),
        "pickup_longitude":  pickup_longitude,
        "pickup_latitude":   pickup_latitude,
        "dropoff_longitude": dropoff_longitude,
        "dropoff_latitude":  dropoff_latitude,
        "passenger_count":   passenger_count,
    }

    api_url = "https://taxifare.lewagon.ai/predict"

    with st.spinner("Asking the model for a fare estimate..."):
        try:
            response = requests.get(api_url, params=params, timeout=10)
            response.raise_for_status()  # raises an error if the server returned a bad status

            result = response.json()
            fare = float(result.get("fare", 0))

            # Show the result front and centre
            st.success(f"💰 Estimated fare: **${fare:.2f}**")

            # A bit of extra context
            st.caption(
                f"Trip: {distance_km:.2f} km · {passenger_count} passenger(s) · "
                f"Pickup at {pickup_datetime.strftime('%b %d, %Y %H:%M')}"
            )

        except requests.exceptions.Timeout:
            st.error("⏱️ The request timed out. The API might be slow right now — try again in a moment.")

        except requests.exceptions.HTTPError as e:
            st.error(f"🚫 The API returned an error: {e}")

        except Exception as e:
            st.error(f"❌ Something went wrong: {e}")
