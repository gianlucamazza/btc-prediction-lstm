# data_preparation.py
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
import matplotlib.dates as mdates
import joblib
import os
import yfinance as yf

columns_to_scale = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume',
                    'MA50', 'MA200', 'Returns', 'Volatility', 'MA20',
                    'Upper', 'Lower', 'RSI', 'MACD']


def merge_data(df1, df2):
    df = pd.concat([df1, df2], axis=0)
    df = df[~df.index.duplicated(keep='last')]
    return df


def get_financial_data(ticker, file_path=None, start_date=None, end_date=None):
    df = yf.download(ticker, start=start_date, end=end_date, progress=False)
    df.reset_index(inplace=True)
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    df = df[['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']]
    df.sort_index(inplace=True)
    df.ffill(inplace=True)
    df.bfill(inplace=True)

    if file_path:
        df.to_csv(file_path, index=True)

    return df


def normalize_features(df, columns, normalize=True):
    if not normalize:
        return df, None

    missing_columns = [col for col in columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Columns not found in DataFrame: {missing_columns}")

    scaler = MinMaxScaler()
    df[columns] = scaler.fit_transform(df[columns])
    return df, scaler


def save_scaler(scaler, ticker, path=None):
    if path is None:
        path = f'scalers/scaler_{ticker}.pkl'
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(scaler, path)


def calculate_rsi(prices, n=14):
    deltas = prices.diff()
    loss = deltas.where(deltas < 0, 0)
    gain = deltas.where(deltas > 0, 0)
    avg_gain = gain.rolling(window=n, min_periods=1).mean()
    avg_loss = -loss.rolling(window=n, min_periods=1).mean()
    rs = avg_gain / avg_loss.replace(0, 1e-10)
    return 100 - (100 / (1 + rs))


def calculate_macd(prices, n_fast=12, n_slow=26):
    ema_fast = prices.ewm(span=n_fast, min_periods=n_slow).mean()
    ema_slow = prices.ewm(span=n_slow, min_periods=n_slow).mean()
    return ema_fast - ema_slow


def calculate_technical_indicators(df):
    required_columns = ['Close']
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"DataFrame must contain the following columns: {required_columns}")

    df['MA50'] = df['Close'].rolling(50).mean()
    df['MA200'] = df['Close'].rolling(200).mean()
    df['Returns'] = df['Close'].pct_change()
    df['Volatility'] = df['Returns'].rolling(50).std()
    df['MA20'] = df['Close'].rolling(20).mean()
    df['Upper'] = df['MA20'] + 2 * df['Volatility']
    df['Lower'] = df['MA20'] - 2 * df['Volatility']
    df['RSI'] = calculate_rsi(df['Close'])
    df['MACD'] = calculate_macd(df['Close'])

    return df


def plot_price_history(dates, prices, ticker):
    plt.figure(figsize=(15, 10))
    plt.plot(dates, prices, label='Close Price')
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.gcf().autofmt_xdate()
    plt.title(f'{ticker} Price History')
    plt.ylabel('Price (USD)')
    plt.xlabel('Date')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def visualize_data(df, ticker, columns, scaler_path=None):
    if scaler_path:
        scaler = joblib.load(scaler_path)
        close_index = columns.index('Close')
        non_scaled_close = scaler.inverse_transform(df[columns])[:, close_index]
        plot_price_history(df.index, non_scaled_close, ticker)
    else:
        plot_price_history(df.index, df['Close'], ticker)


def main(ticker='BTC-USD', start_date=None, end_date=None):
    get_financial_data(ticker, file_path=f'data/raw_data_{ticker}.csv', start_date=start_date, end_date=end_date)

    df = pd.read_csv(f'data/raw_data_{ticker}.csv', index_col='Date', parse_dates=True)
    df = calculate_technical_indicators(df)
    df.bfill(inplace=True)

    if df.isnull().any().any():
        raise ValueError("DataFrame still contains NaN values after preprocessing.")

    df, scaler = normalize_features(df, columns_to_scale)
    scaler_path = f'scalers/scaler_{ticker}.pkl'
    save_scaler(scaler, ticker, path=scaler_path)

    df.to_csv(f'data/processed_data_{ticker}.csv', index=True)
    visualize_data(df, ticker, columns_to_scale, scaler_path)


if __name__ == '__main__':
    main(ticker='BTC-USD', start_date='2015-01-01', end_date=None)
