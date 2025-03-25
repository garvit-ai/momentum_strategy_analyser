import pandas as pd

def jk_strategy(df, J, K, custom_end_date, gap=0):
    filtered_portfolios = []
    for i in range(len(df) - J - K - gap + 1):  # Adjust range to account for gap
        formation_start = df.iloc[i]['Date']
        formation_end = df.iloc[i + J - 1]['Date']
        # Shift holding start by gap
        holding_start = df.iloc[i + J + gap]['Date']
        # Adjust holding end accordingly
        holding_end = df.iloc[i + J + gap + K - 1]['Date']

        if holding_end > custom_end_date:
            break

        formation_period = df.iloc[i:i + J, 1:]
        holding_period = df.iloc[i + J + gap:i + J +
                                 gap + K, 1:]  # Shift holding period by gap

        valid_stocks = formation_period.columns[
            ~formation_period.isna().any() & ~holding_period.isna().any()
        ]

        cumulative_returns = (
            1 + formation_period[valid_stocks] / 100).prod() - 1

        if len(cumulative_returns) >= 50:
            top_50_stocks = cumulative_returns.nlargest(50).sort_values()
            deciles = [top_50_stocks.iloc[i:i + 5].index.tolist()
                       for i in range(0, 50, 5)]

            filtered_portfolios.append({
                'Formation Start': formation_start,
                'Formation End': formation_end,
                'Holding Start': holding_start,
                'Holding End': holding_end,
                'Loser Portfolio': deciles[0],
                'Winner Portfolio': deciles[-1]
            })

    return filtered_portfolios


def calculate_monthly_returns(df, portfolios):
    all_dates = df['Date'].unique()
    winner_returns, loser_returns = {}, {}

    for date in all_dates:
        active = [p for p in portfolios if p['Holding Start']
                  <= date <= p['Holding End']]
        monthly = df[df['Date'] == date].set_index('Date')
        win_ret, lose_ret = [], []

        for p in active:
            if set(p['Winner Portfolio']).issubset(monthly.columns):
                win_ret.append(
                    monthly[p['Winner Portfolio']].mean(axis=1).values[0])
            if set(p['Loser Portfolio']).issubset(monthly.columns):
                lose_ret.append(
                    monthly[p['Loser Portfolio']].mean(axis=1).values[0])

        if win_ret:
            winner_returns[date] = sum(win_ret) / len(win_ret)
        if lose_ret:
            loser_returns[date] = sum(lose_ret) / len(lose_ret)

    winner_df = pd.DataFrame(list(winner_returns.items()), columns=[
                             'Date', 'Winner Portfolio Avg Return'])
    loser_df = pd.DataFrame(list(loser_returns.items()), columns=[
                            'Date', 'Loser Portfolio Avg Return'])
    return winner_df, loser_df
