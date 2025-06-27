import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import mean_absolute_error, mean_squared_error

# Загрузка данных
df = pd.read_csv("data/final_test_price_data.csv", parse_dates=['date'])

# Генерация признаков (точно как в day4)
df['dayofweek'] = df['date'].dt.dayofweek
df['month'] = df['date'].dt.month
df['rolling_mean_7'] = df['price'].rolling(window=7).mean()
df['price_shift_1'] = df['price'].shift(1)
df['price_shift_2'] = df['price'].shift(2)

# Удаляем пропущенные значения после генерации признаков
df = df.dropna()

# Определяем признаки и целевую переменную
features = ['dayofweek', 'month', 'rolling_mean_7', 'price_shift_1', 'price_shift_2']
X = df[features]
y = df['price']

# Делим на train/test (например, 80/20)
split_idx = int(len(df) * 0.8)
X_test = X.iloc[split_idx:]
y_test = y.iloc[split_idx:]

# Загрузка модели
model = joblib.load("models/linear_regression_model_2.joblib")  # проверь путь и имя!

# Предсказания
y_pred = model.predict(X_test)

# Метрики
mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))

print("✅ Тестирование завершено.")
print(f"📊 MAE: {mae:.2f}")
print(f"📉 RMSE: {rmse:.2f}")

# Простейшие проверки качества
assert mae < 100, "⚠️ MAE слишком большое, возможно ошибка в признаках или данных!"
assert rmse < 150, "⚠️ RMSE слишком большое!"
