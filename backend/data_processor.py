import pandas as pd


def load_and_filter_data(file_path, sheet_name, start_date, end_date):
    xls = pd.ExcelFile(file_path)
    df = xls.parse(sheet_name)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values(by='Date')
    df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
    return df


def load_data(file_path, start_date, end_date):
    stock_df = load_and_filter_data(
        file_path, 'stocks Monthly return', start_date, end_date)
    nifty_df = load_and_filter_data(
        file_path, 'nifty monthly returns', start_date, end_date)
    return stock_df, nifty_df
