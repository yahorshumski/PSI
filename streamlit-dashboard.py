import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

# Configuration
API_BASE_URL = "https://qouhox6u4d.execute-api.us-west-1.amazonaws.com"
REFRESH_INTERVAL = 60  # seconds

def load_token_data():
    """Fetch token data from API"""
    response = requests.get(f"{API_BASE_URL}/tokens/status")
    return response.json()['tokens']

def add_token(name, address):
    """Add new token via API"""
    response = requests.post(
        f"{API_BASE_URL}/tokens",
        json={'token_name': name, 'token_address': address}
    )
    return response.status_code == 201

def update_token_status(address, active):
    """Update token active status"""
    response = requests.put(
        f"{API_BASE_URL}/tokens/{address}",
        json={'active': active}
    )
    return response.status_code == 200

def main():
    st.set_page_config(page_title="Token Monitor", layout="wide")
    st.title("Token Performance Monitor")
    
    # Add new token section
    with st.expander("Add New Token"):
        col1, col2 = st.columns(2)
        with col1:
            token_name = st.text_input("Token Name")
        with col2:
            token_address = st.text_input("Token Address")
        
        if st.button("Add Token"):
            if add_token(token_name, token_address):
                st.success(f"Added {token_name}")
            else:
                st.error("Failed to add token")
    
    # Main data display
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = 0
    
    current_time = time.time()
    if current_time - st.session_state.last_refresh >= REFRESH_INTERVAL:
        data = load_token_data()
        df = pd.DataFrame(data)
        st.session_state.data = df
        st.session_state.last_refresh = current_time
    else:
        df = st.session_state.data
    
    # Style the dataframe
    def highlight_rsi(val):
        if pd.isna(val):
            return ''
        elif val >= 70:
            return 'background-color: #ff7f7f'
        elif val >= 60:
            return 'background-color: #ffb07f'
        return ''
    
    # Display table with styling
    st.dataframe(
        df.style\
        .format({
            'current_price': '${:.4f}',
            'rsi_1m': '{:.2f}',
            'rsi_1h': '{:.2f}',
            'price_change_30m': '{:.2f}%'
        })\
        .applymap(highlight_rsi, subset=['rsi_1m', 'rsi_1h'])\
        .set_properties(**{
            'background-color': 'black',
            'color': 'white',
            'border-color': 'white'
        }),
        height=600
    )
    
    # Token management
    with st.expander("Manage Tokens"):
        for _, row in df.iterrows():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"{row['token_name']} ({row['token_address']})")
            with col2:
                active = st.toggle("Active", row['active'], key=row['token_address'])
                if active != row['active']:
                    if update_token_status(row['token_address'], active):
                        st.success("Status updated")
                    else:
                        st.error("Update failed")
    
    # Auto-refresh
    time.sleep(0.1)  # Prevent excessive refreshes
    st.rerun()

if __name__ == "__main__":
    main()
