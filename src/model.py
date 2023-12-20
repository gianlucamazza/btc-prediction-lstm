# model.py
import datetime
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout, BatchNormalization
from keras.optimizers import Adam
from keras.regularizers import l1_l2
from keras.layers import Bidirectional
from keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau, TensorBoard
from data_preparation import COLUMN_SETS
from pathlib import Path
import logger as logger

logger = logger.setup_logger('model_logger', 'logs', 'model.log')


def build_model(input_shape, neurons=50, dropout=0.2, optimizer='adam', learning_rate=0.001, loss='mean_squared_error', metrics=None, l1_reg=0.0, l2_reg=0.0, additional_layers=0, bidirectional=False):
    logger.info("Building the model.")
    if metrics is None:
        metrics = ['mae']

    model = Sequential()

    lstm_layer = LSTM(neurons, return_sequences=True, kernel_regularizer=l1_l2(l1=l1_reg, l2=l2_reg), input_shape=input_shape)
    layer_to_add = Bidirectional(lstm_layer, merge_mode='concat') if bidirectional else lstm_layer
    model.add(layer_to_add)

    model.add(Dropout(dropout))
    model.add(BatchNormalization())

    for _ in range(additional_layers):
        lstm_layer = LSTM(neurons, return_sequences=True, kernel_regularizer=l1_l2(l1=l1_reg, l2=l2_reg))
        layer_to_add = Bidirectional(lstm_layer, merge_mode='concat') if bidirectional else lstm_layer
        model.add(layer_to_add)
        model.add(Dropout(dropout))
        model.add(BatchNormalization())

    lstm_layer = LSTM(neurons, return_sequences=False)
    final_layer = Bidirectional(lstm_layer, merge_mode='concat') if bidirectional else lstm_layer
    model.add(final_layer)

    model.add(Dropout(dropout))
    model.add(BatchNormalization())
    model.add(Dense(1))

    opt = Adam(learning_rate=learning_rate) if optimizer == 'adam' else optimizer
    model.compile(optimizer=opt, loss=loss, metrics=metrics)

    return model


def prepare_callbacks(ticker, monitor='val_loss', epoch=0):
    logger.info(f"Preparing callbacks for {ticker}.")
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    model_dir = Path(f'models/{ticker}')
    log_dir = Path(f'logs/{ticker}/{timestamp}')
    model_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    filepath = model_dir / f'model_{epoch:02d}-{monitor}.keras'
    callbacks = [
        EarlyStopping(monitor=monitor, patience=10, verbose=1, restore_best_weights=True),
        ModelCheckpoint(filepath=str(filepath), verbose=1, save_best_only=True),
        ReduceLROnPlateau(monitor=monitor, factor=0.1, patience=5, verbose=1),
        TensorBoard(log_dir=str(log_dir), histogram_freq=1)
    ]
    return callbacks


def main(ticker='BTC-USD', timesteps=60):
    logger.info(f"Starting model building for {ticker}.")
    input_shape = (timesteps, len(COLUMN_SETS['to_scale']))
    model = build_model(input_shape, additional_layers=1, bidirectional=True)
    model.build(input_shape=(None, *input_shape))
    model_path = f'models/model_{ticker}.keras'
    model.save(model_path)
    logger.info(f"Model saved at {model_path}.")
    model.summary()


if __name__ == "__main__":
    main()
