import torch
from torch import nn
import pandas as pd
import joblib


class LSTMModel(nn.Module):
    def __init__(self, input_size=9, hidden_size=45, num_layers=1, drop_out=0.2):
        super(LSTMModel, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size,
                            num_layers, batch_first=True)
        self.dropout = nn.Dropout(drop_out)
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.dropout(out[:, -1, :])
        return self.fc(out)

# Function define, load the model and scaler


def load_LSTM():

    # Load the model architecture and weights
    model = LSTMModel()
    model.load_state_dict(torch.load("lstm_model_weights.pth"))

    # Load the scaler to transform the input data
    scaler = joblib.load('lstm_scaler.pkl')

    return [model, scaler]

# Function to process the data then predict the next price using the LSTM


def predict_price(model, scaler, window_data):

    # Reorder the data to start from the oldest date
    window_reverse = window_data.iloc[::-1].reset_index(drop=True)

    # Scale features
    window_scaled = scaler.transform(window_reverse)

    # Determine target column index
    target_col = 'Close'
    target_index = window_reverse.columns.get_loc(target_col)

    # Convert to tensors
    window_tensor = torch.tensor(window_scaled.reshape(
        1, 10, window_scaled.shape[1]), dtype=torch.float32)

    # Test
    model.eval()
    with torch.no_grad():
        price_pred = model(window_tensor).squeeze().numpy()

    # Inverse transform the predicted value
    # Get the last input for inverse transformation
    last_input = window_scaled[-1].copy()
    # Set the predicted value in the last input
    last_input[target_index] = price_pred

    # Save last known day stock price to compute change percentage calculation
    today_price = window_data["Close"].iloc[0]

    pred_inv = round(scaler.inverse_transform(
        last_input.reshape(1, -1))[0, target_index], 2)
    change = round(((pred_inv - today_price)/today_price) * 100, 2)

    print(f"Next estimated Stock Price: {pred_inv}")

    # Get the testing standard deviation
    std = pd.read_csv("lstm_std.csv")["Std"].values[0]

    # Compute prediction intervals
    lower = round(pred_inv - std, 2)
    upper = round(pred_inv + std, 2)

    # Return a list of today's price, predicted price, change percentage, and prediction interval bounds
    return [today_price, pred_inv, change, lower, upper]
