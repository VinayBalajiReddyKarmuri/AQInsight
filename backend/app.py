from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import joblib
import numpy as np
import requests
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key

# Load the trained model
model = joblib.load('C:\\Users\\vinay\\OneDrive\\Desktop\\aqi\\data_collection\\air_quality_model.pkl')

# AQI API Configuration
API_KEY = "a62f6911e8e0dfe87dd8e0811d5e5fd1009c059a"
AQI_API_URL = "https://api.waqi.info/feed/{city}/?token={token}"

# -------------------------------
# 🔹 USER AUTHENTICATION ROUTES
# -------------------------------
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == "admin" and password == "password":
            session['username'] = username
            return redirect(url_for('home'))
        else:
            return render_template('login.html', message='Invalid username or password.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('home.html')

# ----------------------------------------
# 🔹 PREDICT AQI FORM & LOGIC (AJAX-BASED)
# ----------------------------------------
@app.route('/predict_aqi_form')
def predict_aqi_form():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if 'username' not in session:
        return redirect(url_for('login'))

    try:
        pm25 = float(request.form['pm25'])
        pm10 = float(request.form['pm10'])
        co = float(request.form['co'])
        no2 = float(request.form['no2'])
        so2 = float(request.form['so2'])

        input_data = np.array([[pm25, pm10, so2, co, no2]])
        predicted_aqi = model.predict(input_data)[0]

        category, advice = get_aqi_category(predicted_aqi)

        return render_template('results.html',
                               predicted_aqi=round(predicted_aqi, 2),
                               category=category,
                               advice=advice)
    except (KeyError, ValueError):
        return jsonify({"error": "Invalid input values. Please enter numbers only."}), 400



# ---------------------------------------
# 🔹 CURRENT AQI FROM API & CLASSIFICATION
# ---------------------------------------
@app.route('/current_aqi', methods=['GET', 'POST'])
def current_aqi():
    aqi_data, error = None, None

    if request.method == 'POST':
        city = request.form.get('city')

        try:
            response = requests.get(AQI_API_URL.format(city=city, token=API_KEY))
            data = response.json()

            if data['status'] == 'ok':
                aqi_value = data['data']['aqi']
                aqi_data = {
                    'city': city,
                    'aqi': aqi_value,
                    'pm25': data['data']['iaqi'].get('pm25', {}).get('v', 0),
                    'pm10': data['data']['iaqi'].get('pm10', {}).get('v', 0),
                    'co': data['data']['iaqi'].get('co', {}).get('v', 0),
                    'no2': data['data']['iaqi'].get('no2', {}).get('v', 0),
                    'so2': data['data']['iaqi'].get('so2', {}).get('v', 0),
                }
                aqi_data['category'] = classify_aqi(aqi_value)
            else:
                error = "Unable to fetch AQI data for the given location."
        except Exception as e:
            error = f"API Error: {str(e)}"

    return render_template('current_aqi.html', aqi_data=aqi_data, error=error)

def classify_aqi(aqi):
    if aqi <= 50:
        return "Good 😊 (Air quality is considered satisfactory.)"
    elif aqi <= 100:
        return "Moderate 😐 (Acceptable air quality for most people.)"
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups 🤧 (People with respiratory issues should be cautious.)"
    elif aqi <= 200:
        return "Unhealthy 😷 (Everyone may start to experience health effects.)"
    elif aqi <= 300:
        return "Very Unhealthy 🛑 (Health alert! Everyone may experience serious health effects.)"
    else:
        return "Hazardous ☠️ (Emergency conditions! Stay indoors and limit outdoor activity.)"


def get_aqi_category(aqi):
    if aqi <= 50:
        return "Good", "✅ **Air quality is excellent!** No precautions needed. Enjoy outdoor activities freely."
    elif aqi <= 100:
        return "Moderate", "⚠️ **Air quality is acceptable.** However, people with respiratory issues (asthma, allergies) should limit prolonged outdoor exposure."
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups", "🛑 **Air quality may affect sensitive individuals.** Children, elderly, and people with lung or heart conditions should avoid strenuous outdoor activities."
    elif aqi <= 200:
        return "Unhealthy", "🚷 **Air pollution is at harmful levels.** Reduce outdoor activities, close windows, and consider using an air purifier indoors. If outside, wear an N95 mask."
    elif aqi <= 300:
        return "Very Unhealthy", "🔴 **Serious health risks for everyone!** Avoid outdoor activities, wear a mask if necessary, and use air purifiers. Stay hydrated and monitor symptoms like coughing or shortness of breath."
    else:
        return "Hazardous", "☠️ **Severe air pollution!** Stay indoors with windows closed, use air purifiers, wear a high-quality mask if you must go outside, and avoid physical exertion. Seek medical help if feeling unwell."



# ---------------------------------------
# 🔹 AQI ALERT NOTIFICATION SYSTEM
# ---------------------------------------
alert_settings = {}

@app.route('/alert_notification')
def alert_notification():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('alert_notification.html')

@app.route('/set_alert', methods=['POST'])
def set_alert():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized access"}), 403

    location = request.form.get('location')
    email = request.form.get('email')
    threshold = int(request.form.get('threshold'))

    if not location or not email or threshold <= 0:
        return jsonify({"error": "Invalid input"}), 400

    alert_settings[session['username']] = {
        "location": location,
        "email": email,
        "threshold": threshold
    }

    return jsonify({"message": "Alert settings saved successfully!"})

@app.route('/check_aqi')
def check_aqi():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized access"}), 403

    user = session['username']
    if user not in alert_settings:
        return jsonify({"error": "No alert settings found"}), 400

    location = alert_settings[user]["location"]
    threshold = alert_settings[user]["threshold"]
    email = alert_settings[user]["email"]

    response = requests.get(AQI_API_URL.format(city=location, token=API_KEY))
    data = response.json()

    if data['status'] != 'ok':
        return jsonify({"error": "Unable to fetch AQI data"}), 500

    current_aqi = data['data']['aqi']

    if current_aqi > threshold:
        send_email_alert(email, location, current_aqi, threshold)
        return jsonify({"alert": "AQI Alert Sent!", "aqi": current_aqi})

    return jsonify({"message": "AQI is safe", "aqi": current_aqi})

def send_email_alert(email, location, aqi, threshold):
    sender_email = "vinaybalaji007@gmail.com"  
    sender_password = "vrtgjnlqinmwuisx"  

    category, advice = get_aqi_category(aqi)  # Function to get AQI category & advice

    subject = f"🌿 Air Quality Update for {location}"

    body = f"""
    Dear User,

    The air quality in **{location}** has exceeded your set threshold. Here are the details:

    - **Current AQI:** {aqi}
    - **Your Threshold:** {threshold}
    - **Air Quality Status:** {category}

    **Recommended Actions:**
    {advice}

    Your well-being is our priority! Stay safe and take necessary precautions. 💙

    Best regards,
    Smarter Skies Team ☁️🌍
    """

    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, msg.as_string())
    except Exception as e:
        print(f"Email Error: {e}")


# ---------------------------------------
# 🔹 RUN FLASK APP
# ---------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
