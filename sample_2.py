import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import pandas as pd
import re
import time
import threading
import folium
from streamlit_folium import st_folium
import plotly.express as px

# Initialize logs and errors in session state
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'errors' not in st.session_state:
    st.session_state.errors = []
if 'stop_sending' not in st.session_state:
    st.session_state.stop_sending = False

# Function to check login credentials
def check_credentials(username, password):
    return username == "admin" and password == "Sangwan@2002"

# Function to log activity
def log_activity(action, status, details):
    now = datetime.now(pytz.timezone('Asia/Kolkata'))
    log_entry = {
        "Timestamp": now.strftime('%Y-%m-%d %H:%M:%S'),
        "Action": action,
        "Status": status,
        "Details": details
    }
    st.session_state.logs.append(log_entry)

# Function to log errors
def log_error(action, error_message):
    now = datetime.now(pytz.timezone('Asia/Kolkata'))
    error_entry = {
        "Timestamp": now.strftime('%Y-%m-%d %H:%M:%S'),
        "Action": action,
        "Error": error_message
    }
    st.session_state.errors.append(error_entry)

# Function to extract IMEI, latitude, and longitude from the provided format
def extract_data_from_format(data_format):
    try:
        imei = re.search(r'#(\d{15})#', data_format).group(1)
        lat = re.search(r'#(\d+\.\d+),N,', data_format).group(1)
        long = re.search(r',N,(\d+\.\d+),E,', data_format).group(1)
        # Ensure latitude and longitude are correctly formatted
        lat = f"{float(lat):09.6f}"
        long = f"{float(long):09.6f}"
        return imei, lat, long
    except AttributeError:
        st.error('Invalid format. Please ensure the format is correct.')
        log_error("Extract Data", "Invalid format")
        return None, None, None

# Function to send manual data
def send_manual_data(imei_manual, latitude, longitude):
    manual_api_url = 'http://103.135.130.119:80'
    delhi_tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(delhi_tz)
    date_str = now.strftime('%d%m%y')
    time_str = now.strftime('%H%M%S')
    packet = f'NRM{imei_manual}01L1{date_str}{time_str}0{latitude}N0{longitude}E404x950D2900DC06A72000.00000.0053001811M0827.00airtel'
    data = {'vltdata': packet}
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    try:
        response = requests.post(manual_api_url, data=data, headers=headers)
        response.raise_for_status()
        st.success('Manual data sent successfully!')
        st.write(f"Packet Sent: {packet}")
        try:
            response_json = response.json()
            st.json(response_json)
            log_activity("Send Manual Data", "Success", f"IMEI: {imei_manual}, Latitude: {latitude}, Longitude: {longitude}, Response: {response_json}")
        except ValueError:
            st.write(response.text)
            log_activity("Send Manual Data", "Success", f"IMEI: {imei_manual}, Latitude: {latitude}, Longitude: {longitude}, Response: {response.text}")
    except requests.exceptions.RequestException as e:
        st.error(f'Manual data send failed: {e}')
        log_activity("Send Manual Data", "Failed", f"IMEI: {imei_manual}, Latitude: {latitude}, Longitude: {longitude}, Error: {e}")
        log_error("Send Manual Data", str(e))

# Function to handle continuous sending
def continuous_sending(imei_manual, latitude, longitude, duration, interval):
    end_time = datetime.now() + timedelta(minutes=duration)
    while datetime.now() < end_time:
        if st.session_state.stop_sending:
            break
        send_manual_data(imei_manual, latitude, longitude)
        time.sleep(interval)

# Function to get coordinates from Google Maps Geocoding API
def get_coordinates(location):
    api_key = 'YOUR_GOOGLE_MAPS_API_KEY'  # Replace with your Google Maps API key
    base_url = 'https://maps.googleapis.com/maps/api/geocode/json'
    params = {'address': location, 'key': api_key}
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'OK':
            lat = data['results'][0]['geometry']['location']['lat']
            lng = data['results'][0]['geometry']['location']['lng']
            return lat, lng
        else:
            st.error('Error fetching coordinates: ' + data['status'])
    else:
        st.error('Error fetching coordinates: ' + response.reason)
    return None, None

# Main app
st.title('State Backend Tool')

# Basic Authentication
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    username = st.text_input('Username')
    password = st.text_input('Password', type='password')
    if st.button('Login'):
        if check_credentials(username, password):
            st.session_state.logged_in = True
            st.success('Login successful!')
        else:
            st.error('Invalid credentials')
else:
    # Single tab for IMEI input and map interaction
    st.header('IMEI Input and Location Selection')

    # Input field for IMEI
    imei_list = st.text_area('IMEIs (comma-separated)')

    # Map for selecting coordinates
    st.subheader('Select Location on Map')
    map_center = [20.5937, 78.9629]  # Center of India
    m = folium.Map(location=map_center, zoom_start=5)
    
    # Add a search button for location search
    location_search = st.text_input('Search Location')
    if st.button('Search'):
        latitude, longitude = get_coordinates(location_search)
        if latitude and longitude:
            map_center = [latitude, longitude]
            m = folium.Map(location=map_center, zoom_start=15)
            folium.Marker(location=map_center, popup=location_search).add_to(m)
        else:
            st.error('Location not found. Please try again.')

    map_data = st_folium(m, width=700, height=500)
    
    if map_data['last_clicked']:
        latitude = map_data['last_clicked']['lat']
        longitude = map_data['last_clicked']['lng']
        st.write(f"Selected Coordinates: Latitude = {latitude}, Longitude = {longitude}")
        
        # Generate data packet based on selected coordinates and IMEI list
        if st.button('Generate Data Packet'):
            imei_list_cleaned = [imei.strip() for imei in imei_list.split(',')]
            packets = []
            for imei in imei_list_cleaned:
                if len(imei) == 15 and imei.isdigit():
                    delhi_tz = pytz.timezone('Asia/Kolkata')
                    now = datetime.now(delhi_tz)
                    date_str = now.strftime('%d%m%y')
                    time_str = now.strftime('%H%M%S')
                    packet = f'NRM{imei}01L1{date_str}{time_str}0{latitude}N0{longitude}E404x950D2900DC06A72000.00000.0053001811M0827.00airtel'
                    packets.append(packet)
                else:
                    st.error(f'Invalid IMEI: {imei}')
            
            if packets:
                st.write("Generated Data Packets:")
                for packet in packets:
                    st.write(packet)
                
                # Send data packets to the server
                                if st.button('Send Data Packets'):
                    state_manual = st.selectbox('Select State for Manual Data', ['Kerala', 'Karnataka', 'Bengal'])
                    
                    # Set API URL based on selected state
                    if state_manual == 'Kerala':
                        manual_api_url = 'http://103.135.130.119:80'
                    elif state_manual == 'Karnataka':
                        manual_api_url = 'http://210.212.237.164:8088'
                    elif state_manual == 'Bengal':
                        manual_api_url = 'http://117.221.20.174:80?vltdata'
                    
                    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
                    
                    for packet in packets:
                        data = {'vltdata': packet}
                        try:
                            response = requests.post(manual_api_url, data=data, headers=headers)
                            response.raise_for_status()
                            st.success(f'Data sent successfully for packet: {packet}')
                            try:
                                response_json = response.json()
                                st.json(response_json)
                                log_activity("Send Manual Data", "Success", f"Packet: {packet}, Response: {response_json}")
                            except ValueError:
                                st.write(response.text)
                                log_activity("Send Manual Data", "Success", f"Packet: {packet}, Response: {response.text}")
                        except requests.exceptions.RequestException as e:
                            if "src property must be a valid json object" in str(e):
                                st.success(f'Data sent successfully for packet: {packet}')
                                log_activity("Send Manual Data", "Success", f"Packet: {packet}, Response: {e}")
                            else:
                                st.error(f'Data send failed for packet: {packet}, Error: {e}')
                                log_activity("Send Manual Data", "Failed", f"Packet: {packet}, Error: {e}")
                                log_error("Send Manual Data", str(e))

    # Activity Logs section
    st.header('Activity Logs')
    # Display logs
    df_logs = pd.DataFrame(st.session_state.logs)
    st.subheader('Activity Logs')
    st.dataframe(df_logs)
    # Download logs as CSV or text
    csv_logs = df_logs.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download logs as CSV",
        data=csv_logs,
        file_name='activity_logs.csv',
        mime='text/csv',
    )
    text_logs = df_logs.to_string(index=False)
    st.download_button(
        label="Download logs as Text",
        data=text_logs,
        file_name='activity_logs.txt',
        mime='text/plain',
    )
    # Display error logs
    df_errors = pd.DataFrame(st.session_state.errors)
    st.subheader('Error Logs')
    st.dataframe(df_errors)
    # Download error logs as CSV or text
    csv_errors = df_errors.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download error logs as CSV",
        data=csv_errors,
        file_name='error_logs.csv',
        mime='text/csv',
    )
    text_errors = df_errors.to_string(index=False)
    st.download_button(
        label="Download error logs as Text",
        data=text_errors,
        file_name='error_logs.txt',
        mime='text/plain',
    )
