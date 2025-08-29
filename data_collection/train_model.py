import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import joblib

# Load your dataset with the correct path
data = pd.read_csv('C:\\Users\\vinay\\OneDrive\\Desktop\\aqi\\data_collection\\city_day.csv')

# Define your features and target
X = data[['PM2.5', 'PM10', 'SO2', 'CO', 'NO2']]
y = data['AQI']

# Split the data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train the model
model = RandomForestRegressor()
model.fit(X_train, y_train)

# Save the model
joblib.dump(model, 'C:\\Users\\vinay\\OneDrive\\Desktop\\aqi\\data_collection\\air_quality_model.pkl')
