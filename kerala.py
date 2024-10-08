import streamlit as st
import requests
from datetime import datetime
import pytz
import pandas as pd
import re
import plotly.express as px

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


# Function to create a Plotly geo graph highlighting the location
def create_geo_graph(lat, long):
    fig = px.scatter_geo(lat=[lat], lon=[long], scope='asia', title='IMEI Location')
    fig.update_traces(marker=dict(size=20, symbol='circle-open'))
    fig.add_scattergeo(lat=[lat], lon=[long], marker=dict(size=30, symbol='circle-open'))
    return fig


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
        else:
            st.error('Invalid credentials')
else:
    # Tabs for different functionalities
    tab1, tab2, tab3, tab4 = st.tabs(["Configure Endpoints", "Manual Data Sender", "Activity Logs", "Analytics"])

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
        st.dataframe(df_logs)
        # Download logs as CSV or text
        csv_logs = df_logs.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download logs as CSV",
            data=csv_logs,
            file_name='activity_logs.csv',
            mime='text/csv',
            key='download-logs-csv'
        )
        text_logs = df_logs.to_string(index=False)
        st.download_button(
            label="Download logs as Text",
            data=text_logs,
            file_name='activity_logs.txt',
            mime='text/plain',
            key='download-logs-text'
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
            key='download-errors-csv'
        )
        text_errors = df_errors.to_string(index=False)
        st.download_button(
            label="Download error logs as Text",
            data=text_errors,
            file_name='error_logs.txt',
            mime='text/plain',
            key='download-errors-text'
        )

        # Analytics section
        with tab4:
            st.header('Analytics')
            # Plot activity logs
            if not df_logs.empty:
                fig = px.line(df_logs, x='Timestamp', y='Action', title='User Activities Over Time')
                st.plotly_chart(fig)
            else:
                st.write("No activity logs to display.")

            # Plot IMEI locations on a map
            if not df_logs.empty:
                imei_locations = df_logs[['Details']].dropna()
                imei_locations = imei_locations[imei_locations['Details'].str.contains('IMEI')]
                imei_locations['Latitude'] = imei_locations['Details'].apply(
                    lambda x: re.search(r'Latitude: (\d+\.\d+)', x).group(1) if re.search(r'Latitude: (\d+\.\d+)',
                                                                                          x) else None)
                imei_locations['Longitude'] = imei_locations['Details'].apply(
                    lambda x: re.search(r'Longitude: (\d+\.\d+)', x).group(1) if re.search(r'Longitude: (\d+\.\d+)',
                                                                                           x) else None)
                imei_locations = imei_locations.dropna(subset=['Latitude', 'Longitude'])

                if not imei_locations.empty:
                    fig = px.scatter_geo(imei_locations, lat='Latitude', lon='Longitude', title='IMEI Locations')
                    fig.update_traces(marker=dict(size=20, symbol='circle-open'))
                    st.plotly_chart(fig)
                else:
                    st.write("No IMEI locations to display.")

