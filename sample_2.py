import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import re
import time
import threading
import folium
from streamlit_folium import st_folium

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

# Function to send manual data for Kerala
def send_manual_data_kerala(imei_manual, latitude, longitude):
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
        st.success(f'Manual data sent successfully for IMEI: {imei_manual}')
        st.write(f"Packet Sent: {packet}")
        try:
            response_json = response.json()
            st.json(response_json)
            log_activity("Send Manual Data", "Success", f"IMEI: {imei_manual}, Latitude: {latitude}, Longitude: {longitude}, Response: {response_json}")
        except ValueError:
            st.write(response.text)
            log_activity("Send Manual Data", "Success", f"IMEI: {imei_manual}, Latitude: {latitude}, Longitude: {longitude}, Response: {response.text}")
    except requests.exceptions.RequestException as e:
        st.error(f'Manual data send failed for IMEI: {imei_manual}, Error: {e}')
        log_activity("Send Manual Data", "Failed", f"IMEI: {imei_manual}, Latitude: {latitude}, Longitude: {longitude}, Error: {e}")
        log_error("Send Manual Data", str(e))

# Function to send manual data for Karnataka
def send_manual_data_karnataka(imei_manual, latitude, longitude):
    manual_api_url = 'http://210.212.237.164:8088'
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
            log_activity("Send Manual Data", "Success", f"IMEI: {imei_manual}, Latitude: {latitude}, Longitude: {longitude}, Response: {response_json}")
        except ValueError:
            st.write(response.text)
            log_activity("Send Manual Data", "Success", f"IMEI: {imei_manual}, Latitude: {latitude}, Longitude: {longitude}, Response: {response.text}")
    except requests.exceptions.RequestException as e:
        st.error(f'Manual data send failed for IMEI: {imei_manual}, Error: {e}')
        log_activity("Send Manual Data", "Failed", f"IMEI: {imei_manual}, Latitude: {latitude}, Longitude: {longitude}, Error: {e}")
        log_error("Send Manual Data", str(e))

# Function to send manual data for West Bengal
def send_manual_data_west_bengal(imei_manual, latitude, longitude):
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
            log_activity("Send Manual Data", "Success", f"IMEI: {imei_manual}, Latitude: {latitude}, Longitude: {longitude}, Response: {response_json}")
        except ValueError:
            st.write(response.text)
            log_activity("Send Manual Data", "Success", f"IMEI: {imei_manual}, Latitude: {latitude}, Longitude: {longitude}, Response: {response.text}")
    except requests.exceptions.RequestException as e:
        st.error(f'Manual data send failed for IMEI: {imei_manual}, Error: {e}')
        log_activity("Send Manual Data", "Failed", f"IMEI: {imei_manual}, Latitude: {latitude}, Longitude: {longitude}, Error: {e}")
        log_error("Send Manual Data", str(e))

# Function to handle continuous sending
def continuous_sending(imei_manual, latitude, longitude, duration, interval, state):
    end_time = datetime.now() + timedelta(minutes=duration)
    while datetime.now() < end_time:
        if st.session_state.stop_sending:
            break
        if state == 'Kerala':
            send_manual_data_kerala(imei_manual, latitude, longitude)
        elif state == 'Karnataka':
            send_manual_data_karnataka(imei_manual, latitude, longitude)
        elif state == 'West Bengal':
            send_manual_data_west_bengal(imei_manual, latitude, longitude)
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
    # Tabs for different functionalitie
        tab4 = st.tabs(["Configure Endpoints", "Manual Data Sender", "Activity Logs", "Error Logs"])

    with tab1:
        st.header("Configure Endpoints")
        st.write("Endpoint configuration settings will go here.")

    with tab2:
        st.header("Manual Data Sender")
        imei_manual = st.text_input('IMEI')
        latitude = st.text_input('Latitude')
        longitude = st.text_input('Longitude')
        state = st.selectbox('State', ['Kerala', 'Karnataka', 'West Bengal'])
        if st.button('Send Data'):
            if state == 'Kerala':
                send_manual_data_kerala(imei_manual, latitude, longitude)
            elif state == 'Karnataka':
                send_manual_data_karnataka(imei_manual, latitude, longitude)
            elif state == 'West Bengal':
                send_manual_data_west_bengal(imei_manual, latitude, longitude)

        duration = st.number_input('Duration (minutes)', min_value=1, max_value=60, value=10)
        interval = st.number_input('Interval (seconds)', min_value=1, max_value=60, value=10)
        if st.button('Start Continuous Sending'):
            st.session_state.stop_sending = False
            threading.Thread(target=continuous_sending, args=(imei_manual, latitude, longitude, duration, interval, state)).start()
        if st.button('Stop Continuous Sending'):
            st.session_state.stop_sending = True

    with tab3:
        st.header("Activity Logs")
        st.write(st.session_state.logs)

    with tab4:
        st.header("Error Logs")
        st.write(st.session_state.errors)
