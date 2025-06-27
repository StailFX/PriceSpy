from flask import Flask, request, jsonify
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

app = Flask(__name__)

# Загружаем модель
model = joblib.load('models/linear_regression_model_2.joblib')

@app.route('/predict-price', methods=['GET'])
def predict_price():
    try:
        # Читаем параметры запроса
        horizon = int(request.args.get('horizon', 1))  # кол-во дней вперёд, по умолчанию 1

        # Загружаем CSV и готовим последние строки
        df = pd.read_csv('data/test_data.csv', parse_dates=['date'])
        df = df.sort_values('date')

        last_row = df.iloc[-1]
        future_predictions = []

        for i in range(horizon):
            day = (last_row['date'] + timedelta(days=1)).dayofweek
            month = (last_row['date'] + timedelta(days=1)).month
            rolling_mean_7 = df['price'].rolling(window=7).mean().iloc[-1]
            shift_1 = last_row['price']
            shift_2 = df.iloc[-2]['price']

            # Формируем фичи
            features = pd.DataFrame([{
                'dayofweek': day,
                'month': month,
                'rolling_mean_7': rolling_mean_7,
                'price_shift_1': shift_1,
                'price_shift_2': shift_2,
            }])

            # Прогноз
            pred = model.predict(features)[0]
            future_predictions.append(round(float(pred), 2))

            # Обновляем для следующего шага
            new_row = {
                'date': last_row['date'] + timedelta(days=1),
                'price': pred
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            last_row = new_row

        return jsonify({'predictions': future_predictions})

    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
