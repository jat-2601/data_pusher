import streamlit as st
import requests
from datetime import datetime
import pytz
import pandas as pd
import re

# Initialize logs and errors in session state
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'errors' not in st.session_state:
    st.session_state.errors = []

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
    # Tabs for different functionalities
    tab1, tab2 = st.tabs(["Configure Endpoints", "Manual Data Sender"])
    
    # Configure Endpoints section
    with tab1:
        st.header('Configure Endpoints')

        # Set API URL (same for all states)
        api_url = 'http://34.194.133.72:8888/update'

        # Input fields for parameters
        imei = st.text_input('IMEI (15 digits)', max_chars=15)
        compliance = st.selectbox('Compliance', ['CDAC', 'AIS'], index=0)

        if st.button('Send Request'):
            if len(imei) != 15 or not imei.isdigit():
                st.error('IMEI must be a 15-digit number.')
                log_activity("Send Request", "Failed", f"Invalid IMEI: {imei}")
            else:
                data = {'imei': imei, 'compliance': compliance}
                headers = {'Content-Type': 'application/x-www-form-urlencoded'}
                try:
                    response = requests.post(api_url, data=data, headers=headers)
                    response.raise_for_status()
                    st.success('Request successful!')
                    try:
                        response_json = response.json()
                        st.json(response_json)
                        log_activity("Send Request", "Success",
                                     f"IMEI: {imei}, Compliance: {compliance}, Response: {response_json}")
                    except ValueError:
                        st.write(response.text)
                        log_activity("Send Request", "Success",
                                     f"IMEI: {imei}, Compliance: {compliance}, Response: {response.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f'Request failed: {e}')
                    log_activity("Send Request", "Failed", f"IMEI: {imei}, Compliance: {compliance}, Error: {e}")
                    log_error("Send Request", str(e))

    # Manual Data Sender section
with tab2:
    st.header('Manual Data Sender')

    # Dropdown to choose input method
    input_method = st.selectbox('Input Method', ['Manual Entry', 'Extract from Format'])

    if input_method == 'Manual Entry':
        # Input fields for parameters
        imei_list = st.text_area('IMEIs (comma-separated)')
        latitude = st.text_input('Latitude')
        longitude = st.text_input('Longitude')
    else:
        data_format = st.text_area('Data Format')

    if st.button('Send Manual Data'):
        if input_method == 'Extract from Format':
            imei_manual, latitude, longitude = extract_data_from_format(data_format)
            if not imei_manual or not latitude or not longitude:
                st.error('Failed to extract data from format.')
                log_activity("Send Manual Data", "Failed", "Failed to extract data from format")
                return  # Exit early if extraction fails

        # Check if imei_list is not empty or None
        if imei_list:
            # Clean and split IMEI list
            imei_list = [imei.strip() for imei in imei_list.split(',')]
        else:
            st.error('Please enter at least one IMEI number.')
            log_activity("Send Manual Data", "Failed", "No IMEI numbers provided")
            return  # Exit early if no IMEI is provided

        for imei_manual in imei_list:
            if len(imei_manual) != 15 or not imei_manual.isdigit():
                st.error(f'IMEI must be a 15-digit number: {imei_manual}')
                log_activity("Send Manual Data", "Failed", f"Invalid IMEI: {imei_manual}")
                continue  # Skip to the next IMEI

            # Get current date and time in Delhi timezone
            delhi_tz = pytz.timezone('Asia/Kolkata')
            now = datetime.now(delhi_tz)
            date_str = now.strftime('%d%m%y')
            time_str = now.strftime('%H%M%S')

            # Format the packet
            packet = f'NRM{imei_manual}01L1{date_str}{time_str}0{latitude}N0{longitude}E404x950D2900DC06A72000.00000.0053001811M0827.00airtel'
            data = {'vltdata': packet}
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}

            try:
                response = requests.post(api_url, data=data, headers=headers)
                response.raise_for_status()
                st.success(f'Manual data sent successfully for IMEI: {imei_manual}')
                st.write(f"Packet Sent: {packet}")
                response_json = response.json()
                st.json(response_json)
                log_activity("Send Manual Data", "Success",
                             f"IMEI: {imei_manual}, Latitude: {latitude}, Longitude: {response_json}")
            except requests.exceptions.RequestException as e:
                st.error(f'Manual data send failed for IMEI: {imei_manual}, Error: {e}')
                log_activity("Send Manual Data", "Failed",
                             f"IMEI: {imei_manual}, Latitude: {latitude}, Longitude: {e}")
                log_error("Send Manual Data", str(e))

                # Get current date and time in Delhi timezone
                delhi_tz = pytz.timezone('Asia/Kolkata')
                now = datetime.now(delhi_tz)
                date_str = now.strftime('%d%m%y')
                time_str = now.strftime('%H%M%S')

                # Format the packet
                packet = f'NRM{imei_manual}01L1{date_str}{time_str}0{latitude}N0{longitude}E404x950D2900DC06A72000.00000.0053001811M0827.00airtel'
                data = {'vltdata': packet}
                headers = {'Content-Type': 'application/x-www-form-urlencoded'}

                try:
                    response = requests.post(api_url, data=data, headers=headers)
                    response.raise_for_status()
                    st.success(f'Manual data sent successfully for IMEI: {imei_manual}')
                    st.write(f"Packet Sent: {packet}")
                    response_json = response.json()
                    st.json(response_json)
                    log_activity("Send Manual Data", "Success",
                                 f"IMEI: {imei_manual}, Latitude: {latitude}, Longitude: {response_json}")
                except requests.exceptions.RequestException as e:
                    st.error(f'Manual data send failed for IMEI: {imei_manual}, Error: {e}')
                    log_activity("Send Manual Data", "Failed",
                                 f"IMEI: {imei_manual}, Latitude: {latitude}, Longitude: {e}")
                    log_error("Send Manual Data", str(e))

    # Activity Logs section
    with st.expander('View Activity Logs'):
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
    with st.expander('View Error Logs'):
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
