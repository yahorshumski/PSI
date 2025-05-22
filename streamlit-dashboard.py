import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime
import time

# Configuration
API_BASE_URL = "https://qouhox6u4d.execute-api.us-west-1.amazonaws.com"
REFRESH_INTERVAL = 60  # seconds

# Add custom CSS for better address display
def add_custom_css():
    st.markdown("""
        <style>
        .address-container {
            background-color: #1E1E1E;
            padding: 8px;
            border-radius: 4px;
            font-family: monospace;
            cursor: pointer;
            margin: 4px 0;
        }
        .token-name {
            color: #4CAF50;
            font-weight: bold;
        }
        .copy-hint {
            color: #666;
            font-size: 0.8em;
            font-style: italic;
        }
        </style>
    """, unsafe_allow_html=True)

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

def init_session_state():
    """Initialize session state variables"""
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = 0
    if 'data' not in st.session_state:
        st.session_state.data = pd.DataFrame()

def safe_format_number(val, format_string):
    """Safely format numeric values, handling None/NaN"""
    if val is None or pd.isna(val):
        return 'N/A'
    try:
        return format_string.format(float(val))
    except (ValueError, TypeError):
        return 'N/A'

def safe_format_datetime(val):
    """Safely format datetime values"""
    if val is None or pd.isna(val):
        return 'N/A'
    try:
        return pd.to_datetime(val).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return 'N/A'

def style_dataframe(df):
    """Apply styling to dataframe safely"""
    try:
        # Clean the data first
        df_clean = df.copy()
        
        # Replace None/NaN values with appropriate defaults for styling
        numeric_columns = ['current_price', 'rsi_1m', 'rsi_1h', 'price_change_30m', 'price_change_24h']
        for col in numeric_columns:
            if col in df_clean.columns:
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
        
        # Define style functions
        def style_rsi(val):
            try:
                if pd.isna(val) or val is None:
                    return ''
                val = float(val)
                if val >= 70:
                    return 'background-color: #ff7f7f'
                elif val >= 60:
                    return 'background-color: #ffb07f'
            except:
                return ''
            return ''

        def style_price_change(val):
            try:
                if pd.isna(val) or val is None:
                    return ''
                val = float(val)
                if val > 0:
                    return 'color: #00ff00'
                elif val < 0:
                    return 'color: #ff0000'
            except:
                return ''
            return ''

        # Custom formatter function
        def format_currency(val):
            return safe_format_number(val, '${:.4f}')
        
        def format_percentage(val):
            return safe_format_number(val, '{:+.2f}%')
        
        def format_decimal(val):
            return safe_format_number(val, '{:.2f}')

        # Apply formatting and styling
        styler = df_clean.style.format({
            'current_price': format_currency,
            'rsi_1m': format_decimal,
            'rsi_1h': format_decimal,
            'price_change_30m': format_percentage,
            'price_change_24h': format_percentage,
            'last_update': safe_format_datetime
        })
        
        # Apply conditional styling only to columns that exist
        if 'rsi_1m' in df_clean.columns or 'rsi_1h' in df_clean.columns:
            rsi_cols = [col for col in ['rsi_1m', 'rsi_1h'] if col in df_clean.columns]
            if rsi_cols:
                styler = styler.map(style_rsi, subset=rsi_cols)
        
        if 'price_change_30m' in df_clean.columns or 'price_change_24h' in df_clean.columns:
            price_cols = [col for col in ['price_change_30m', 'price_change_24h'] if col in df_clean.columns]
            if price_cols:
                styler = styler.map(style_price_change, subset=price_cols)
        
        # Apply general styling
        styler = styler.set_properties(**{
            'background-color': 'black',
            'color': 'white',
            'border-color': 'white'
        })
        
        return styler
        
    except Exception as e:
        st.error(f"Error styling dataframe: {str(e)}")
        return df.style

def main():
    st.set_page_config(page_title="Token Monitor", layout="wide")
    add_custom_css()
    init_session_state()
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
    current_time = time.time()
    if current_time - st.session_state.last_refresh >= REFRESH_INTERVAL:
        data = load_token_data()
        if data:
            try:
                df = pd.DataFrame(data)
                # Ensure all required columns exist with proper defaults
                required_columns = [
                    'token_name', 'token_address', 'current_price',
                    'price_change_30m', 'price_change_24h',
                    'last_update'
                ]
                
                # Only include RSI columns if they exist in the data
                if any('rsi_' in str(col) for col in df.columns):
                    if 'rsi_1m' in df.columns:
                        required_columns.insert(-1, 'rsi_1m')
                    if 'rsi_1h' in df.columns:
                        required_columns.insert(-1, 'rsi_1h')
                
                # Add missing columns with None values
                for col in required_columns:
                    if col not in df.columns:
                        df[col] = None
                
                # Reorder columns
                df = df[required_columns]
                st.session_state.data = df
                st.session_state.last_refresh = current_time
            except Exception as e:
                st.error(f"Error processing data: {str(e)}")
                return
    
    df = st.session_state.data
    
    if not df.empty:
        try:
            # Display main dataframe
            styled_df = style_dataframe(df)
            st.dataframe(styled_df, height=600, use_container_width=True)
            
            # Token management with selectable addresses
            with st.expander("Manage Tokens"):
                for _, row in df.iterrows():
                    col1, col2, col3 = st.columns([2, 2, 1])
                    with col1:
                        st.markdown(f"<div class='token-name'>{row['token_name']}</div>", 
                                  unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"""
                            <div class='address-container' 
                                 title='Click to copy' 
                                 onclick="navigator.clipboard.writeText('{row['token_address']}')">
                                {row['token_address']}
                                <span class='copy-hint'>(Click to copy)</span>
                            </div>
                        """, unsafe_allow_html=True)
                    with col3:
                        if st.button("Delete", key=row['token_address']):
                            if delete_token(row['token_address']):
                                st.success(f"Removed {row['token_name']}")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Failed to delete token")
            
            # Quick reference section
            with st.expander("Quick Reference"):
                st.markdown("### Token Addresses")
                cols = st.columns(2)
                for i, (_, row) in enumerate(df.iterrows()):
                    with cols[i % 2]:
                        st.markdown(f"""
                            <div style='margin: 10px 0;'>
                                <div class='token-name'>{row['token_name']}</div>
                                <div class='address-container' 
                                     title='Click to copy'
                                     onclick="navigator.clipboard.writeText('{row['token_address']}')">
                                    {row['token_address']}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
        
        except Exception as e:
            st.error(f"Error displaying data: {str(e)}")
    
    # Auto-refresh
    time.sleep(0.1)
    st.rerun()

if __name__ == "__main__":
    main()
