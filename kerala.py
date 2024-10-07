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
