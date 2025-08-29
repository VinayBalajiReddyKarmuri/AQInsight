document.getElementById('predictButton').addEventListener('click', function() {
    const pm25 = parseFloat(document.getElementById('pm25').value);
    const pm10 = parseFloat(document.getElementById('pm10').value);
    const co = parseFloat(document.getElementById('co').value);
    const no2 = parseFloat(document.getElementById('no2').value);
    const so2 = parseFloat(document.getElementById('so2').value);

    fetch('/predict', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ pm25, pm10, co, no2, so2 })
    })
    .then(response => response.json())
    .then(data => {
        const aqi = data.predicted_aqi;
        const category = getAQICategory(aqi);
        document.getElementById('result').innerText = `Predicted AQI: ${aqi} - ${category}`;
    })
    .catch(error => {
        console.error('Error:', error);
    });
});

function getAQICategory(aqi) {
    if (aqi <= 50) {
        return "Good";
    } else if (aqi <= 100) {
        return "Moderate";
    } else if (aqi <= 150) {
        return "Unhealthy for Sensitive People";
    } else if (aqi <= 200) {
        return "Unhealthy";
    } else if (aqi <= 300) {
        return "Very Unhealthy";
    } else {
        return "Hazardous";
    }
}
