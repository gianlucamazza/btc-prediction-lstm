import sys
import datetime
from pathlib import Path
from keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau, TensorBoard
from src.logging.logger import setup_logger

# Ensure the project directory is in the sys.path
project_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_dir))

ROOT_DIR = project_dir
logger = setup_logger('callback_logger', 'logs', 'callback_logger.log')


def prepare_callbacks(model_dir: Path, ticker: str, monitor: str = 'val_loss', fold_index: int = 0):
    """
    Prepare callbacks for training the model.

    Parameters:
    - model_dir: Directory where the model will be saved.
    - ticker: Ticker symbol for logging and file naming.
    - monitor: Metric to monitor for early stopping and checkpoints.
    - fold_index: Index of the fold for cross-validation.

    Returns:
    - List of configured callbacks.
    """
    logger.info(f"Preparing callbacks for {ticker}.")
    logger.info(f"  - Monitor metric: {monitor}")
    logger.info(f"  - Fold index: {fold_index}")

    # Create a timestamp for the log directory
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    log_dir = ROOT_DIR / 'logs' / ticker / timestamp
    log_dir.mkdir(parents=True, exist_ok=True)

    # Define the file path for the model checkpoints
    filepath = model_dir / f"{ticker}_fold_{fold_index}_{monitor}.keras"

    # List of callbacks
    callbacks = [
        EarlyStopping(monitor=monitor, patience=10, verbose=1, restore_best_weights=True),
        ModelCheckpoint(filepath=str(filepath), monitor=monitor, save_best_only=True, verbose=1),
        ReduceLROnPlateau(monitor=monitor, factor=0.1, patience=5, verbose=1),
        TensorBoard(log_dir=str(log_dir), histogram_freq=1)
    ]

    return callbacks
