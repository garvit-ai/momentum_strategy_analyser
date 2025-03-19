import streamlit as st
import pandas as pd
from backend.data_processor import load_data
from backend.jk_strategy import run_jk_strategy, calculate_monthly_returns
from backend.plotting import plot_cumulative_returns_for_best_jk
from datetime import datetime

# --- Streamlit App ---
st.title("J/K Momentum Strategy Analysis")

# Load data once

@st.cache_data  # Cache to avoid reloading on every interaction
def get_data():
    file_path = r'dataset.xlsx'
    custom_start_date = pd.to_datetime("2002-01-01")
    custom_end_date = pd.to_datetime("2024-12-31")
    stock_df, nifty_df = load_data(
        file_path, custom_start_date, custom_end_date)
    return stock_df, nifty_df


stock_df, nifty_df = get_data()

# User inputs
st.markdown("### Select J and K Values")
J_options = [1, 3, 6, 9, 12]
K_options = [1, 3, 6, 9, 12]

J_values = st.multiselect("Formation Periods (J)", J_options, default=[6])
K_values = st.multiselect("Holding Periods (K)", K_options, default=[3])

# Analyse button
if st.button("Analyse"):
    if J_values and K_values:
        with st.spinner("Running J/K Strategy Analysis..."):
            # Initialize summary matrix
            summary_matrix = []

            # Compute results for all selected J/K combinations
            for J in J_values:
                for K in K_values:
                    portfolios = run_jk_strategy(
                        stock_df, J, K, pd.to_datetime("2024-12-31"))
                    if not portfolios:
                        st.error(f"No valid portfolios for J={J}, K={K}.")
                        continue

                    winner_df, loser_df = calculate_monthly_returns(
                        stock_df, portfolios)
                    final_df = pd.merge(winner_df, loser_df, on='Date')

                    # Calculate summary metrics
                    avg_winner = final_df['Winner Portfolio Avg Return'].mean()
                    avg_loser = final_df['Loser Portfolio Avg Return'].mean()
                    spread = avg_winner - avg_loser

                    summary_matrix.append(
                        [J, K, round(avg_winner, 4), round(avg_loser, 4), round(spread, 4)])

            # Display Summary Matrix
            if summary_matrix:
                summary_df = pd.DataFrame(summary_matrix, columns=[
                    'J', 'K', 'Avg Winner Return (%)', 'Avg Loser Return (%)', 'Spread (Winner - Loser) (%)'])

                # Sort the DataFrame by 'J' first, then by 'K'
                summary_df = summary_df.sort_values(by=['J', 'K']).reset_index(drop=True)

                # Add S.No column with serial numbers starting from 1 after sorting
                summary_df.insert(0, 'S.No', range(1, len(summary_df) + 1))

                # Find the index of the row with the maximum spread (after sorting)
                max_spread_idx = summary_df['Spread (Winner - Loser) (%)'].idxmax()

                # Define a styling function to highlight the row with max spread
                def highlight_max_spread(row):
                    return ['background-color: #90EE90' if row.name == max_spread_idx else '' for _ in row]

                st.subheader("Summary Matrix")
                # Apply the styling and display the sorted DataFrame
                st.dataframe(summary_df.style.apply(highlight_max_spread, axis=1),
                            use_container_width=True, hide_index=True)

                # Find J/K with maximum spread
                best_J = summary_df.loc[max_spread_idx, 'J']
                best_K = summary_df.loc[max_spread_idx, 'K']

                # Compute and display plot for best J/K only
                best_portfolios = run_jk_strategy(
                    stock_df, best_J, best_K, pd.to_datetime("2024-12-31"))
                if best_portfolios:
                    best_winner_df, best_loser_df = calculate_monthly_returns(
                        stock_df, best_portfolios)
                    best_final_df = pd.merge(
                        best_winner_df, best_loser_df, on='Date')

                    st.subheader(
                        f"Cumulative Returns Plot: J={best_J}, K={best_K} vs NIFTY (Max Spread)")
                    fig = plot_cumulative_returns_for_best_jk(
                        best_final_df, nifty_df, best_J, best_K)
                    st.pyplot(fig)

            else:
                st.error("No valid results to display.")
    else:
        st.warning("Please select at least one value for both J and K.")
else:
    st.info("Select J and K values and click 'Analyse' to see results.")
