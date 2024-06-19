# feature_engineering.py
import sys
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from config import COLUMN_SETS, CLOSE
from technical_indicators import calculate_technical_indicators
import joblib
from pathlib import Path
import logger as logger_module

# Add the project directory to the sys.path
project_dir = Path(__file__).resolve().parent
sys.path.append(str(project_dir))

BASE_DIR = Path(__file__).parent.parent
logger = logger_module.setup_logger('feature_engineering_logger', BASE_DIR / 'logs', 'feature_engineering.log')


def validate_input_data(df, required_columns):
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        error_message = f"Missing columns in input data: {missing_columns}"
        logger.error(error_message)
        raise ValueError(error_message)


def check_data(df, step_description):
    logger.info(f"Data after {step_description}: shape = {df.shape}")
    logger.info(f"Sample data:\n{df.head()}")


def clean_data(df):
    df.dropna(inplace=True)
    logger.info("Data cleaned. NaN values handled.")


def normalize_features(df, columns_to_normalize):
    logger.info("Normalizing features.")
    scaler = MinMaxScaler()
    df[columns_to_normalize] = scaler.fit_transform(df[columns_to_normalize])
    return df, scaler


def normalize_close(df):
    logger.info("Normalizing 'Close' column.")
    scaler = MinMaxScaler()
    df[[CLOSE]] = scaler.fit_transform(df[[CLOSE]])
    return scaler


def save_scaler(scaler, ticker, scaler_type='feature'):
    path = BASE_DIR / f'scalers/{scaler_type}_scaler_{ticker}.pkl'
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(scaler, path)
    logger.info(f"Scaler saved at {path}")


def process_and_save_features(df, ticker):
    try:
        logger.info(f"Processing features for {ticker}.")

        df = calculate_technical_indicators(df)
        check_data(df, "calculating technical indicators")

        required_columns = COLUMN_SETS['to_scale'] + COLUMN_SETS['required']
        validate_input_data(df, required_columns)

        clean_data(df)

        columns_to_normalize = [col for col in df.columns if col != CLOSE]
        df, feature_scaler = normalize_features(df, columns_to_normalize)
        check_data(df, "normalizing features")

        close_scaler = normalize_close(df)
        check_data(df, "normalizing 'Close' column")

        save_scaler(close_scaler, ticker, scaler_type='close')
        save_scaler(feature_scaler, ticker, scaler_type='feature')

        scaled_data_path = BASE_DIR / f'data/scaled_data_{ticker}.csv'
        df.to_csv(scaled_data_path, index=True)
        logger.info(f"Scaled data saved at {scaled_data_path}")
    except Exception as e:
        logger.error(f"Error in process_and_save_features: {e}")
        raise


def main(ticker='BTC-USD', worker=None):
    logger.info(f"Starting feature engineering for {ticker}.")
    file_path = Path(BASE_DIR / f'data/processed_data_{ticker}.csv')
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return
    try:
        df = pd.read_csv(file_path, index_col='Date', parse_dates=True)
        process_and_save_features(df, ticker)
        logger.info(f"Feature engineering completed for {ticker}.")
    except Exception as e:
        logger.error(f"Failed to complete feature engineering for {ticker}: {e}")

    if worker and hasattr(worker, 'is_running') and not worker.is_running():
        return


if __name__ == '__main__':
    main(ticker='BTC-USD')
