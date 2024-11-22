import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime
import time

# Configuration
API_BASE_URL = "https://qouhox6u4d.execute-api.us-west-1.amazonaws.com"
REFRESH_INTERVAL = 60  # seconds

def load_token_data():
    """Fetch token data from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/tokens/status")
        if response.status_code == 200:
            return response.json()['tokens']
        else:
            st.error(f"Failed to fetch token data: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return []

def add_token(name, address):
    """Add new token via API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/tokens",
            json={'token_name': name, 'token_address': address}
        )
        return response.status_code == 201
    except Exception as e:
        st.error(f"Error adding token: {str(e)}")
        return False

def delete_token(address):
    """Delete token via API"""
    try:
        response = requests.delete(f"{API_BASE_URL}/tokens/{address}")
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error deleting token: {str(e)}")
        return False

def style_rsi(val):
    """Style function for RSI values"""
    if pd.isna(val):
        return ''
    try:
        val = float(val)
        if val >= 70:
            return 'background-color: #ff7f7f'
        elif val >= 60:
            return 'background-color: #ffb07f'
    except:
        pass
    return ''

def style_price_change(val):
    """Style function for price changes"""
    if pd.isna(val):
        return ''
    try:
        val = float(val)
        if val > 0:
            return 'color: #00ff00'
        elif val < 0:
            return 'color: #ff0000'
    except:
        pass
    return ''

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
                time.sleep(1)
                st.rerun()
            else:
                st.error("Failed to add token")
    
    # Main data display
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = 0
    
    current_time = time.time()
    if current_time - st.session_state.last_refresh >= REFRESH_INTERVAL:
        data = load_token_data()
        if data:
            df = pd.DataFrame(data)
            # Reorder columns for better display
            columns_order = [
                'token_name', 'token_address', 'current_price',
                'rsi_1m', 'rsi_1h', 'price_change_30m', 'price_change_24h',
                'last_update'
            ]
            df = df[columns_order]
            st.session_state.data = df
            st.session_state.last_refresh = current_time
    else:
        df = st.session_state.get('data', pd.DataFrame())
    
    if not df.empty:
        # Style the dataframe
        styled_df = df.style\
            .format({
                'current_price': '${:.4f}',
                'rsi_1m': '{:.2f}',
                'rsi_1h': '{:.2f}',
                'price_change_30m': '{:+.2f}%',
                'price_change_24h': '{:+.2f}%',
                'last_update': lambda x: pd.to_datetime(x).strftime('%Y-%m-%d %H:%M:%S')
            })\
            .map(style_rsi, subset=['rsi_1m', 'rsi_1h'])\
            .map(style_price_change, subset=['price_change_30m', 'price_change_24h'])\
            .set_properties(**{
                'background-color': 'black',
                'color': 'white',
                'border-color': 'white'
            })
        
        # Display the dataframe
        st.dataframe(
            styled_df,
            height=600,
            use_container_width=True
        )
        
        # Token management
        with st.expander("Manage Tokens"):
            for _, row in df.iterrows():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"{row['token_name']} ({row['token_address']})")
                with col2:
                    if st.button("Delete", key=row['token_address']):
                        if delete_token(row['token_address']):
                            st.success(f"Removed {row['token_name']}")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to delete token")
    
    # Auto-refresh
    time.sleep(0.1)
    st.rerun()

if __name__ == "__main__":
    main()
