import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import re
import time
import threading
import folium
from streamlit_folium import st_folium

# Initialize errors in session state
if 'errors' not in st.session_state:
    st.session_state.errors = []
if 'stop_sending' not in st.session_state:
    st.session_state.stop_sending = False

# Function to check login credentials
def check_credentials(username, password):
    return username == "admin" and password == "Sangwan@2002"

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
def send_manual_data(imei_manual, latitude, longitude, state):
    if state == 'Kerala':
        manual_api_url = 'http://103.135.130.119:80'
    elif state == 'Karnataka':
        manual_api_url = 'http://210.212.237.164:8088'
    elif state == 'West Bengal':
        manual_api_url = 'http://117.221.20.174:80?vltdata'
    
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
        st.success(f'Manual data sent successfully for IMEI: {imei_manual}')
        st.write(f"Packet Sent: {packet}")
        try:
            response_json = response.json()
            st.json(response_json)
        except ValueError:
            st.write(response.text)
    except requests.exceptions.RequestException as e:
        st.error(f'Manual data send failed for IMEI: {imei_manual}, Error: {e}')
        log_error("Send Manual Data", str(e))

# Function to handle continuous sending
def continuous_sending(imei_manual, latitude, longitude, duration, interval, state):
    end_time = datetime.now() + timedelta(minutes=duration)
    while datetime.now() < end_time:
        if st.session_state.stop_sending:
            break
        send_manual_data(imei_manual, latitude, longitude, state)
        time.sleep(interval)

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
                state_manual = st.selectbox('Select State for Manual Data', ['Kerala', 'Karnataka', 'West Bengal'])
                
                if st.button('Send Data Packets'):
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
                            except ValueError:
                                st.write(response.text)
                        except requests.exceptions.RequestException as e:
                            if "src property must be a valid json object" in str(e):
                                st.success(f'Data sent successfully for packet: {packet}')
                            else:
                                st.error(f'Data send failed for packet: {packet}, Error: {e}')
                                log_error("Send Manual Data", str(e))
