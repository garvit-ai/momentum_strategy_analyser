import sys
import os
import pandas as pd
import streamlit as st
from datetime import datetime

# Add parent directory to sys.path for backend imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import backend modules
from backend.plotting import plot_cumulative_returns_for_best_jk
from backend.strategy import jk_strategy, calculate_monthly_returns
from backend.data_processor import load_data

# --- Sidebar for Inputs ---
with st.sidebar:
    st.header("J/K Strategy Parameters")

    # File upload with tooltip instructions
    st.markdown(
        """
        <div style="display: flex; align-items: center;">
            <span>Data File</span>
            <span style="margin-left: 5px; cursor: pointer;" title="The stock returns sheet must have a 'Date' column (YYYY-MM-DD format) and numeric return columns for stocks. The benchmark sheet (optional) must have 'Date' (YYYY-MM-DD format) and 'Return decimal' columns.">
                ℹ️
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )
    uploaded_file = st.file_uploader("Upload your Excel file (.xlsx)", type=["xlsx"])
    
    # Initialize variables
    file_data = None
    has_both_sheets = False
    stock_df = None
    nifty_df = None
    stock_sheet_name = None
    nifty_sheet_name = None
    available_sheets = ["None"]

    # Handle file selection and validation
    if uploaded_file is None:
        st.info("No file uploaded. Using default dataset.")
        dataset_path = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'dataset.xlsx')
        if not os.path.exists(dataset_path):
            st.error(f"Default dataset not found at: {dataset_path}")
            st.stop()
        file_data = dataset_path
        stock_sheet_name = "stocks monthly return"
        nifty_sheet_name = "nifty monthly return"
        has_both_sheets = True
    else:
        if not uploaded_file.name.endswith('.xlsx'):
            st.error("Please upload a valid .xlsx file.")
            st.stop()
        file_data = uploaded_file

        # Get available sheets from uploaded file
        try:
            xls = pd.ExcelFile(file_data)
            available_sheets = xls.sheet_names
            if not available_sheets:
                st.error("The uploaded Excel file contains no sheets.")
                st.stop()
        except Exception as e:
            st.error(f"Error reading the Excel file: {str(e)}")
            st.stop()

        # Let user select sheets
        st.subheader("Select Sheets")
        stock_sheet_name = st.selectbox("Select the sheet for stock returns:", available_sheets, index=0)
        nifty_sheet_name = st.selectbox("Select the sheet for benchmark returns (optional):", ["None"] + available_sheets, index=0)
        has_both_sheets = nifty_sheet_name != "None"

    # Custom date entry
    st.subheader("Backtest Period")
    default_start = pd.to_datetime("2002-01-01")
    default_end = pd.to_datetime("2024-12-31")
    start_date = st.date_input("Start Date", value=default_start, min_value=datetime(1990, 1, 1), max_value=datetime.now())
    end_date = st.date_input("End Date", value=default_end, min_value=start_date, max_value=datetime(2030, 12, 31))

    if start_date > end_date:
        st.error("Start Date must be earlier than End Date!")
        st.stop()

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # Load the data with a spinner for feedback
    with st.spinner("Loading data..."):
        try:
            stock_df, nifty_df = load_data(file_data, stock_sheet_name, nifty_sheet_name, start_date, end_date)
            if uploaded_file is None and nifty_df is None:
                st.warning("Default dataset does not contain 'nifty monthly return' sheet. Graph will not be displayed.")
                has_both_sheets = False
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            st.stop()

    # User inputs for J, K, and gap
    st.subheader("Strategy Parameters")
    J_options = [1, 3, 6, 9, 12]
    K_values = st.multiselect("Holding Periods (K)", J_options, default=[3])
    J_values = st.multiselect("Formation Periods (J)", J_options, default=[6])
    gap = st.number_input("Gap Between Formation and Holding (months)", min_value=0, max_value=12, value=0, step=1)

    # Analyse button
    analyse_button = st.button("Analyse")

# --- Main Area ---
st.title("J/K Momentum Strategy Backtesting Platform")

if analyse_button:
    if not (J_values and K_values):
        st.warning("Please select at least one value for both J and K.")
    else:
        with st.spinner("Running J/K Strategy Analysis..."):
            summary_matrix = []
            for J in J_values:
                for K in K_values:
                    portfolios = jk_strategy(stock_df, J, K, end_date, gap=gap)
                    if not portfolios:
                        st.error(f"No valid portfolios for J={J}, K={K} with gap {gap} months.")
                        continue

                    winner_df, loser_df = calculate_monthly_returns(stock_df, portfolios)
                    final_df = pd.merge(winner_df, loser_df, on='Date')

                    avg_winner = final_df['Winner Portfolio Avg Return'].mean()
                    avg_loser = final_df['Loser Portfolio Avg Return'].mean()
                    spread = avg_winner - avg_loser

                    summary_matrix.append([J, K, round(avg_winner, 4), round(avg_loser, 4), round(spread, 4)])

            if not summary_matrix:
                st.error("No valid results to display.")
            else:
                summary_df = pd.DataFrame(summary_matrix, columns=[
                    'J', 'K', 'Avg Winner Return (%)', 'Avg Loser Return (%)', 'Spread (Winner - Loser) (%)'])
                summary_df = summary_df.sort_values(by=['J', 'K']).reset_index(drop=True)
                summary_df.insert(0, 'S.No', range(1, len(summary_df) + 1))

                max_spread_idx = summary_df['Spread (Winner - Loser) (%)'].idxmax()
                def highlight_max_spread(row):
                    return ['background-color: #90EE90' if row.name == max_spread_idx else '' for _ in row]

                st.subheader("Summary Matrix")
                styled_df = (summary_df.style
                             .apply(highlight_max_spread, axis=1)
                             .format({'Avg Winner Return (%)': '{:.4f}',
                                      'Avg Loser Return (%)': '{:.4f}',
                                      'Spread (Winner - Loser) (%)': '{:.4f}'}))
                st.dataframe(styled_df, use_container_width=True, hide_index=True)

                if has_both_sheets and nifty_df is not None:
                    best_J = summary_df.loc[max_spread_idx, 'J']
                    best_K = summary_df.loc[max_spread_idx, 'K']

                    best_portfolios = jk_strategy(stock_df, best_J, best_K, end_date, gap=gap)
                    if best_portfolios:
                        best_winner_df, best_loser_df = calculate_monthly_returns(stock_df, best_portfolios)
                        best_final_df = pd.merge(best_winner_df, best_loser_df, on='Date')

                        st.subheader(f"Cumulative Returns Plot: J={best_J}, K={best_K} vs NIFTY (Max Spread)")
                        fig = plot_cumulative_returns_for_best_jk(best_final_df, nifty_df, best_J, best_K)
                        st.pyplot(fig)
                else:
                    st.info("Graph not displayed because benchmark data was not provided.")
else:
    st.info("Select parameters in the sidebar and click 'Analyse' to see results.")