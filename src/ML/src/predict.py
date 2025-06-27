from flask import Flask, request, jsonify
import joblib
import pandas as pd
from datetime import timedelta
import os

# Configuration via environment variables
MODEL_PATH = os.getenv('MODEL_PATH', 'models/linear_regression_model_2.joblib')
DATA_PATH = os.getenv('DATA_PATH', 'data/main_data.csv')

# Initialize Flask app
app = Flask(__name__)

# Load trained model and historical data
model = joblib.load(MODEL_PATH)
df = pd.read_csv(DATA_PATH, parse_dates=['date'])

@app.route('/predict-price', methods=['GET'])
def predict_price():
    try:
        horizon = int(request.args.get('horizon', 1))
        # Ensure DataFrame sorted by date
        df_sorted = df.sort_values('date').reset_index(drop=True)
        future_preds = []
        history = df_sorted.copy()

        for _ in range(horizon):
            last_row = history.iloc[-1]
            features = {
                'dayofweek': last_row['date'].dayofweek,
                'month': last_row['date'].month,
                'rolling_mean_7': history['price'].tail(7).mean(),
                'price_shift_1': last_row['price'],
                'price_shift_2': history['price'].shift(1).iloc[-1]
            }
            X = pd.DataFrame([features])
            pred = model.predict(X)[0]
            next_date = last_row['date'] + timedelta(days=1)
            future_preds.append({'date': next_date.strftime('%Y-%m-%d'), 'predicted_price': float(pred)})
            # Append to history for iterative prediction
            history = history.append({'date': next_date, 'price': pred}, ignore_index=True)

        return jsonify({'predictions': future_preds})

    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)
