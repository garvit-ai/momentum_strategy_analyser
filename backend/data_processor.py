import pandas as pd
import streamlit as st

@st.cache_data
def load_data(file_data, stock_sheet_name, nifty_sheet_name, start_date, end_date):
    # Load stock data
    stock_df = pd.read_excel(file_data, sheet_name=stock_sheet_name)

    # Column validation for stock_df
    if 'Date' not in stock_df.columns:
        st.error("Error: The stock returns sheet must contain a 'Date' column.")
        st.stop()

    # Check for at least one numeric column (for stock returns)
    numeric_cols = stock_df.drop(columns=['Date']).select_dtypes(include='number').columns
    if len(numeric_cols) == 0:
        st.error("Error: The stock returns sheet must contain at least one numeric column for stock returns.")
        st.stop()

    # Date parsing with error handling
    try:
        stock_df['Date'] = pd.to_datetime(stock_df['Date'], errors='raise')
    except Exception as e:
        st.error(f"Error: Unable to parse dates in the stock returns sheet. Ensure dates are in 'YYYY-MM-DD' format. Details: {str(e)}")
        st.stop()

    # Check if stock_df is empty after filtering
    stock_df = stock_df.sort_values(by='Date')
    stock_df = stock_df[(stock_df['Date'] >= start_date) & (stock_df['Date'] <= end_date)]
    if stock_df.empty:
        st.error("Error: No data available in the stock returns sheet for the selected date range.")
        st.stop()

    # Load benchmark data (if provided)
    nifty_df = None
    if nifty_sheet_name != "None":
        nifty_df = pd.read_excel(file_data, sheet_name=nifty_sheet_name)

        # Column validation for nifty_df
        if 'Date' not in nifty_df.columns:
            st.error("Error: The benchmark sheet must contain a 'Date' column.")
            st.stop()
        if 'Return decimal' not in nifty_df.columns:
            st.error("Error: The benchmark sheet must contain a 'Return decimal' column.")
            st.stop()

        # Check if 'Return decimal' is numeric
        if not pd.api.types.is_numeric_dtype(nifty_df['Return decimal']):
            st.error("Error: The 'Return decimal' column in the benchmark sheet must contain numeric values.")
            st.stop()

        # Date parsing with error handling
        try:
            nifty_df['Date'] = pd.to_datetime(nifty_df['Date'], errors='raise')
        except Exception as e:
            st.error(f"Error: Unable to parse dates in the benchmark sheet. Ensure dates are in 'YYYY-MM-DD' format. Details: {str(e)}")
            st.stop()

        # Check if nifty_df is empty after filtering
        nifty_df = nifty_df.sort_values(by='Date')
        nifty_df = nifty_df[(nifty_df['Date'] >= start_date) & (nifty_df['Date'] <= end_date)]
        if nifty_df.empty:
            st.error("Error: No data available in the benchmark sheet for the selected date range.")
            st.stop()

    return stock_df, nifty_df