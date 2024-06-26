import time
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, TensorBoard
from tensorflow.keras.models import Model
from typing import Tuple, Optional, Dict

from config import COLUMN_SETS
import logger as logger_module
from data_utils import prepare_data
from model import build_model

BASE_DIR = Path(__file__).parent.parent
logger = logger_module.setup_logger('train_model_logger', BASE_DIR / 'logs', 'train_model.log')


def train_model(x_train: np.ndarray, y_train: np.ndarray, x_val: np.ndarray, y_val: np.ndarray, model_dir: str, ticker: str, fold_index: int, parameters: Dict, trial_id: int, worker: Optional[object] = None) -> Tuple[Model, dict]:
    """Train the LSTM model."""
    logger.info(f"Starting training for fold {fold_index} in trial {trial_id}...")
    start_time = time.time()

    model = build_model(
        input_shape=(parameters['train_steps'], len(COLUMN_SETS['to_scale'])),
        neurons=parameters['neurons'],
        dropout=parameters['dropout'],
        additional_layers=parameters['additional_layers'],
        bidirectional=parameters['bidirectional'],
        l1_reg=parameters.get('l1_reg', 1e-5),
        l2_reg=parameters.get('l2_reg', 1e-5),
        optimizer='adam'
    )

    # Use TensorFlow Addons for advanced optimizers and metrics
    model.compile(
        optimizer='adam',
        loss='mean_squared_error',
        metrics=['mean_squared_error']
    )

    tensorboard_log_dir = BASE_DIR / 'logs' / 'tensorboard' / f'fold_{fold_index}'
    tensorboard_callback = TensorBoard(log_dir=str(tensorboard_log_dir), histogram_freq=1)

    # Ensure the model directory exists
    model_dir_path = Path(model_dir)
    model_dir_path.mkdir(parents=True, exist_ok=True)

    # Callbacks
    model_checkpoint = ModelCheckpoint(
        filepath=str(model_dir_path / f"model_{ticker}_trial_{trial_id}_fold_{fold_index}.keras"),
        monitor='val_loss',
        save_best_only=True,
        save_weights_only=False,
        verbose=1
    )

    early_stopping = EarlyStopping(
        monitor='val_loss',
        patience=parameters['early_stopping_patience'],
        verbose=1,
        restore_best_weights=True
    )

    callbacks = [model_checkpoint, early_stopping, tensorboard_callback]

    history = model.fit(
        x_train, y_train,
        epochs=parameters['epochs'],
        batch_size=parameters['batch_size'],
        validation_data=(x_val, y_val),
        callbacks=callbacks,
        verbose=1
    )

    logger.info(f"Training completed for fold {fold_index} in trial {trial_id}.")
    model_path = model_dir_path / f"model_{ticker}_trial_{trial_id}_fold_{fold_index}.keras"
    model.save(model_path)
    logger.info(f"Model saved at {model_path}")

    end_time = time.time()
    logger.info(f"Training for fold {fold_index} in trial {trial_id} completed in {end_time - start_time:.2f} seconds.")
    return model, history


class ModelTrainer:
    COLUMN_TO_PREDICT = 'Close'
    DATA_FOLDER = 'data'
    SCALERS_FOLDER = 'scalers'
    MODELS_FOLDER = 'models'

    def __init__(self, ticker: str = 'BTC-USD', parameters: Optional[Dict] = None):
        self.ticker = ticker
        self.parameters = parameters
        self.data_path = BASE_DIR / f'{self.DATA_FOLDER}/scaled_data_{self.ticker}.csv'
        self.scaler_path = BASE_DIR / f'{self.SCALERS_FOLDER}/feature_scaler_{self.ticker}.pkl'

        logger.info(f"Initializing ModelTrainer for ticker {ticker}")
        logger.info(f"Data path: {self.data_path}")
        logger.info(f"Scaler path: {self.scaler_path}")

        self.feature_scaler = self.load_scaler()
        self.df = self.load_dataset()
        self.df = prepare_data(self.df, self.feature_scaler)
        self.x, self.y = self.create_windowed_data(self.df, self.parameters['train_steps'], self.COLUMN_TO_PREDICT)

    def load_scaler(self) -> object:
        """Load the feature scaler from disk."""
        logger.info(f"Loading scaler from {self.scaler_path}")
        try:
            return joblib.load(self.scaler_path)
        except FileNotFoundError as e:
            logger.error(f"Scaler file not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading scaler: {e}", exc_info=True)
            raise

    def load_dataset(self) -> pd.DataFrame:
        """Load the dataset from disk."""
        logger.info(f"Loading dataset from {self.data_path}")
        try:
            df = pd.read_csv(self.data_path, index_col='Date')
            df.ffill(inplace=True)
            if self.COLUMN_TO_PREDICT not in df.columns:
                raise ValueError(f"Column {self.COLUMN_TO_PREDICT} not found in dataset.")
            return df
        except FileNotFoundError as e:
            logger.error(f"Dataset file not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading dataset: {e}", exc_info=True)
            raise

    @staticmethod
    def create_windowed_data(df: pd.DataFrame, steps: int, target_column: str) -> Tuple[np.ndarray, np.ndarray]:
        """Create windowed data for LSTM."""
        x, y = [], []
        target_index = df.columns.get_loc(target_column)
        data = df.values
        for i in range(steps, len(data)):
            x.append(data[i - steps:i])
            y.append(data[i, target_index])
        return np.array(x), np.array(y)
