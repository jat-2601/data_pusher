import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import pandas as pd
import re
import time
import threading
import plotly.express as px
from sklearn.linear_model import LinearRegression
import numpy as np

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

# Function to handle continuous sending
def continuous_sending(imei_manual, latitude, longitude, duration, interval):
    end_time = datetime.now() + timedelta(minutes=duration)
    while datetime.now() < end_time:
        if st.session_state.stop_sending:
            break
        send_manual_data(imei_manual, latitude, longitude)
        time.sleep(interval)

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
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Configure Endpoints", "Manual Data Sender", "Activity Logs", "Analytics", "Machine Learning"])

    # Configure Endpoints section
    with tab1:
        st.header('Configure Endpoints')
        api_url = 'http://34.194.133.72:8888/update'
        imei = st.text_input('IMEI (15 digits)', max_chars=15)
        compliance = st.selectbox('Compliance', ['CDAC', 'AIS'], index=0)
        if st.button('Send Request'):
            if len(imei) != 15 or not re.match(r'^\d{15}$', imei):
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
        input_method = st.selectbox('Input Method', ['Manual Entry', 'Extract from Format'])
        imei_manual, latitude, longitude = None, None, None
        if input_method == 'Manual Entry':
            imei_manual = st.text_input('IMEI for Manual Data (15 digits)', max_chars=15)
            latitude = st.text_input('Latitude')
            longitude = st.text_input('Longitude')
        else:
            data_format = st.text_area('Data Format')
            if st.button('Extract Data'):
                imei_manual, latitude, longitude = extract_data_from_format(data_format)
                if not imei_manual or not latitude or not longitude:
                    st.error('Failed to extract data from format.')
                    log_activity("Send Manual Data", "Failed", "Failed to extract data from format")
                else:
                    st.write(f"Extracted IMEI: {imei_manual}")
                    st.write(f"Extracted Latitude: {latitude}")
                    st.write(f"Extracted Longitude: {longitude}")
                    # Plotting the coordinates on a map using Plotly
                    fig = px.scatter_mapbox(
                        lat=[float(latitude)],
                        lon=[float(longitude)],
                        hover_name=[imei_manual],
                        hover_data={"Latitude": [latitude], "Longitude": [longitude]},
                        zoom=15,
                        mapbox_style="open-street-map",
                        title="Extracted Location"
                    )
                    st.plotly_chart(fig)

        # Continuous sending toggle
        continuous_toggle = st.checkbox('Enable Continuous Sending')
        if continuous_toggle:
            duration = st.selectbox('Duration', ['5 minutes', '10 minutes', '15 minutes', '30 minutes', '1 hour', '4 hours'])
            duration_map = {
                '5 minutes': 5,
                '10 minutes': 10,
                '15 minutes': 15,
                '30 minutes': 30,
                '1 hour': 60,
                '4 hours': 240
            }
            interval = st.selectbox('Interval', ['5 seconds', '10 seconds', '15 seconds'])
            interval_map = {
                '5 seconds': 5,
                '10 seconds': 10,
                '15 seconds': 15
            }
            selected_duration = duration_map[duration]
            selected_interval = interval_map[interval]

        if st.button('Send Manual Data'):
            if imei_manual is None or len(imei_manual) != 15 or not re.match(r'^\d{15}$', imei_manual):
                st.error('IMEI must be a 15-digit number.')
                log_activity("Send Manual Data", "Failed", f"Invalid IMEI: {imei_manual}")
            else:
                if continuous_toggle:
                    st.session_state.stop_sending = False
                    threading.Thread(target=continuous_sending, args=(
                    imei_manual, latitude, longitude, selected_duration, selected_interval)).start()
                else:
                    send_manual_data(imei_manual, latitude, longitude)

            if st.button('Stop Continuous Sending'):
                st.session_state.stop_sending = True

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

                # Analytics section
            with tab4:
                st.header('Analytics')
                st.subheader('Summary of Activities')
                if df_logs.empty:
                    st.write("No activity logs available.")
                else:
                    st.write("Total Activities:", len(df_logs))
                    st.write("Successful Activities:", len(df_logs[df_logs['Status'] == 'Success']))
                    st.write("Failed Activities:", len(df_logs[df_logs['Status'] == 'Failed']))
                    st.bar_chart(df_logs['Status'].value_counts())

                # Machine Learning section
            with tab5:
                st.header('Machine Learning')
                st.write("This section demonstrates a basic machine learning model using historical data.")

                # Example: Predicting future latitude based on past data
                if not df_logs.empty:
                    df_logs['Latitude'] = df_logs['Details'].apply(
                        lambda x: float(re.search(r'Latitude: (\d+\.\d+)', x).group(1)) if re.search(
                            r'Latitude: (\d+\.\d+)', x) else None)
                    df_logs['Longitude'] = df_logs['Details'].apply(
                        lambda x: float(re.search(r'Longitude: (\d+\.\d+)', x).group(1)) if re.search(
                            r'Longitude: (\d+\.\d+)', x) else None)
                    df_logs.dropna(subset=['Latitude', 'Longitude'], inplace=True)

                    if len(df_logs) > 1:
                        X = np.array(df_logs.index).reshape(-1, 1)
                        y = df_logs['Latitude'].values
                        model = LinearRegression()
                        model.fit(X, y)
                        future_index = np.array([[len(df_logs) + i] for i in range(1, 6)])
                        future_latitudes = model.predict(future_index)

                        st.write("Predicted future latitudes for the next 5 entries:")
                        st.write(future_latitudes)
                    else:
                        st.write("Not enough data to train the model.")
                else:
                    st.write("No data available for machine learning.")
