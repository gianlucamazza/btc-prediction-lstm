import argparse
import sys
from pathlib import Path
import pandas as pd
import yfinance as yf

# Ensure the project directory is in the sys.path
project_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_dir))

from src.config import COLUMN_SETS
from src.data.eda import eda_pipeline
from src.logging.logger import setup_logger

# Setup logger
ROOT_DIR = project_dir
logger = setup_logger('data_preparation_logger', 'logs', 'data_preparation.log')


def download_financial_data(ticker, start_date, end_date):
    """Download financial data for a given ticker and date range."""
    logger.info(f"Downloading data for {ticker} from {start_date} to {end_date}.")
    try:
        data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if data.empty:
            error_message = f"No data returned for ticker {ticker}."
            logger.warning(error_message)
            raise ValueError(error_message)
        return data
    except Exception as e:
        logger.error(f"Error in downloading data for {ticker}: {e}")
        raise


def arrange_and_fill(df, name):
    """Arrange and fill missing data in the DataFrame."""
    logger.info(f"Arranging and filling missing data for {name}.")
    df = df.reset_index()
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    df = df[COLUMN_SETS['basic']].copy()
    df.dropna(how='all', inplace=True)
    df.sort_index(inplace=True)
    df.ffill(inplace=True)
    df.bfill(inplace=True)
    return df


def save_df_to_csv(df, file_path):
    """Save DataFrame to a CSV file."""
    file_path = f'{file_path}'
    logger.info(f"Saving DataFrame to {file_path}.")
    df.to_csv(file_path, index=True)


def get_financial_data(ticker: str, name: str, file_path=None, start_date=None, end_date=None):
    """Download, arrange, fill, and save financial data for a given ticker."""
    try:
        df = download_financial_data(ticker, start_date, end_date)
        df = arrange_and_fill(df, name)
        save_df_to_csv(df, file_path)
        logger.info(f"Data for {name} successfully processed and saved.")
        return df
    except Exception as e:
        logger.error(f"Error in processing data for {name}: {e}")
        raise


def main(ticker: str, label: str, start_date=None, end_date=None, worker=None):
    """Main function to prepare data for a given ticker."""
    logger.info(f"Starting data preparation for {label}.")
    raw_data_path = ROOT_DIR / "data" / f'raw_data_{label}.csv'
    processed_data_path = ROOT_DIR / "data" / f'processed_data_{label}.csv'
    try:
        df = get_financial_data(ticker, label, file_path=raw_data_path, start_date=start_date, end_date=end_date)
        logger.info(f"Start date: {df.index[0]}, End date: {df.index[-1]}")

        # Perform EDA
        logger.info("Performing Exploratory Data Analysis (EDA).")
        _, missing_values, low_variance_cols, target_correlation = eda_pipeline(raw_data_path, ticker,'Close')

        # Log the EDA results
        logger.info(f"Percentage of missing values:\n{missing_values}")
        logger.info(f"Columns with low variance:\n{low_variance_cols}")
        logger.info(f"Correlation with target variable:\n{target_correlation}")

        # Save the processed dataset
        save_df_to_csv(df, processed_data_path)
        logger.info(f'Finished data preparation for {label}.')
        if worker and not worker.is_running():
            return
    except Exception as e:
        logger.error(f"Failed to complete data preparation for {label}: {e}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Data Preparation')
    parser.add_argument('--yfinance_ticker', type=str, required=True, help='YFinance Symbol')
    parser.add_argument('--ticker', type=str, required=True, help='Ticker label')
    parser.add_argument('--start_date', type=str, required=True, help='Start date')
    parser.add_argument('--end_date', type=str, help='End date')

    args = parser.parse_args()
    main(ticker=args.yfinance_ticker, label=args.ticker, start_date=args.start_date, end_date=args.end_date)
