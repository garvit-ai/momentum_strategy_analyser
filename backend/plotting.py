import matplotlib.pyplot as plt
import pandas as pd
def plot_cumulative_returns_for_best_jk(final_df, nifty_df, J, K):
    final_df['Winner-Loser Spread'] = final_df['Winner Portfolio Avg Return'] - \
        final_df['Loser Portfolio Avg Return']
    nifty_filtered = nifty_df[nifty_df['Date'].between(
        final_df['Date'].min(), final_df['Date'].max())]
    combined_df = pd.merge(final_df[['Date', 'Winner-Loser Spread']], nifty_filtered[['Date', 'Return decimal']],
                           on='Date', how='inner')

    combined_df['Cumulative Spread'] = (
        1 + combined_df['Winner-Loser Spread'] / 100).cumprod()
    combined_df['Cumulative NIFTY'] = (
        1 + combined_df['Return decimal']).cumprod()

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(combined_df['Date'], combined_df['Cumulative Spread'],
            label='Winner-Loser Spread Strategy', linewidth=2)
    ax.plot(combined_df['Date'], combined_df['Cumulative NIFTY'],
            label='NIFTY 50 Index', linewidth=2, color='black')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Cumulative Return', fontsize=12)
    ax.set_title(
        f'Cumulative Returns: J={J}, K={K} (Best Winner-Loser Spread) vs NIFTY', fontsize=14)
    ax.legend(fontsize=12)
    ax.grid(True)
    return fig
