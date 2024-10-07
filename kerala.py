import streamlit as st
import requests
from datetime import datetime
import pytz
import pandas as pd
import re
import plotly.express as px
from streamlit_elements import elements, mui, html
from st_aggrid import AgGrid

# Custom CSS
custom_css = """
<style>
body {
    background-color: #f0f0f0;
    font-family: 'Arial', sans-serif;
}

.stButton>button {
    background-color: #4CAF50;
    color: white;
    border: none;
    padding: 10px 20px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 16px;
    margin: 4px 2px;
    cursor: pointer;
    border-radius: 8px;
}
</style>
"""

# Load custom CSS
st.markdown(custom_css, unsafe_allow_html=True)

# Initialize logs, errors, and users in session state
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'errors' not in st.session_state:
    st.session_state.errors = []
if 'users' not in st.session_state:
    st.session_state.users = {'admin': 'Sangwan@2002'}

# Function to check login credentials
def check_credentials(username, password):
    return username in st.session_state.users and st.session_state.users[username] == password

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
        imei = re.search(r'#(\\d{15})#', data_format).group(1)
        lat = re.search(r'#(\\d+\\.\\d+),N,', data_format).group(1)
        long = re.search(r',N,(\\d+\\.\\d+),E,', data_format).group(1)
        # Ensure latitude and longitude are correctly formatted
        lat = f"{float(lat):09.6f}"
        long = f"{float(long):09.6f}"
        return imei, lat, long
    except AttributeError:
        st.error('Invalid format. Please ensure the format is correct.')
        log_error("Extract Data", "Invalid format")
        return None, None, None

# Main app
st.title('State Backend Kerala Tool')

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
            log_activity("Login", "Success", f"User: {username}")
        else:
            st.error('Invalid credentials')
            log_activity("Login", "Failed", f"User: {username}")
else:
    # Tabs for different functionalities
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Configure Endpoints", "Manual Data Sender", "Activity Logs", "User Management", "Analytics"])

    # Configure Endpoints section
    with tab1:
        st.header('Configure Endpoints')
        # Hardcoded API URL
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
        # Hardcoded API URL for manual data sender
        manual_api_url = 'http://103.135.130.119:80'
        # Dropdown to choose input method
        input_method = st.selectbox('Input Method', ['Manual Entry', 'Extract from Format'])
        if input_method == 'Manual Entry':
            # Input fields for parameters
            imei_manual = st.text_input('IMEI for Manual Data (15 digits)', max_chars=15)
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
                    pass
            
            if imei_manual is None or len(imei_manual) != 15 or not imei_manual.isdigit():
                st.error('IMEI must be a 15-digit number.')
                log_activity("Send Manual Data", "Failed", f"Invalid IMEI: {imei_manual}")
            else:
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
                    response = requests.post(manual_api_url, data=data, headers=headers)
                    response.raise_for_status()
                    st.success('Manual data sent successfully!')
                    st.write(f"Packet Sent: {packet}")
                    try:
                        response_json = response.json()
                        st.json(response_json)
                        log_activity("Send Manual Data", "Success",
                                     f"IMEI: {imei_manual}, Latitude: {latitude}, Longitude: {longitude}, Response: {response_json}")
                    except ValueError:
                        st.write(response.text)
                        log_activity("Send Manual Data", "Success",
                                     f"IMEI: {imei_manual}, Latitude: {latitude}, Longitude: {longitude}, Response: {response.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f'Manual data send failed: {e}')
                    log_activity("Send Manual Data", "Failed",
                                 f"IMEI: {imei_manual}, Latitude: {latitude}, Longitude: {longitude}, Error: {e}")
                    log_error("Send Manual Data", str(e))

    # Activity Logs section
    with tab3:
        st.header('Activity Logs')
        # Display logs
        df_logs = pd.DataFrame(st.session_state.logs)
        st.subheader('Activity Logs')
        AgGrid(df_logs)
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
        AgGrid(df_errors)
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

    # User Management section
    with tab4:
        st.header('User Management')
        st.subheader('Add New User')
        new_username = st.text_input('New Username')
        new_password = st.text_input('New Password', type='password')
        if st.button('Add User'):
            if new_username in st.session_state.users:
                st.error('Username already exists.')
                log_activity("Add User", "Failed", f"Username: {new_username} already exists")
            else:
                st.session_state.users[new_username] = new_password
                st.success('User added successfully!')
                log_activity("Add User", "Success", f"Username: {new_username}")

        st.subheader('Update User Password')
        update_username = st.text_input('Username to Update')
        update_password = st.text_input('New Password for User', type='password')
        if st.button('Update Password'):
            if update_username in st.session_state.users:
                st.session_state.users[update_username] = update_password
                st.success('Password updated successfully!')
                log_activity("Update Password", "Success", f"Username: {update_username}")
            else:
                st.error('Username does not exist.')
                log_activity("Update Password", "Failed", f"Username: {update_username} does not exist")

        st.subheader('Delete User')
        delete_username = st.text_input('Username to Delete')
        if st.button('Delete User'):
            if delete_username in st.session_state.users:
                del st.session_state.users[delete_username]
                st.success('User deleted successfully!')
                log_activity("Delete User", "Success", f"Username: {delete_username}")
            else:
                st.error('Username does not exist.')
                log_activity("Delete User", "Failed", f"Username: {delete_username} does not exist")

    # Analytics section
    with tab5:
        st.header('Analytics')
        if st.session_state.logs:
            df_logs = pd.DataFrame(st.session_state.logs)
            fig = px.histogram(df_logs, x='Action', title='Activity Distribution')
            st.plotly_chart(fig)
        else:
            st.write('No logs available for analytics.')
        
