from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required
import requests
from datetime import datetime
from ..models.dataset import WeatherLog
from .. import db

weather_bp = Blueprint('weather', __name__)


def classify_severity(temp_c):
    """Classify temperature severity for EV range impact"""
    if temp_c <= -20:
        return 'extreme'
    elif temp_c <= -10:
        return 'severe'
    elif temp_c <= 0:
        return 'moderate'
    elif temp_c <= 10:
        return 'mild'
    else:
        return 'normal'


def fetch_openweathermap(city, api_key):
    """Fetch weather from OpenWeatherMap API"""
    url = f"https://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': city,
        'appid': api_key,
        'units': 'metric'
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            weather = {
                'city': data.get('name', city),
                'country': data.get('sys', {}).get('country', ''),
                'temperature_c': data['main']['temp'],
                'feels_like_c': data['main']['feels_like'],
                'humidity': data['main']['humidity'],
                'wind_speed_kmh': data['wind']['speed'] * 3.6,  # m/s to km/h
                'pressure_hpa': data['main']['pressure'],
                'weather_condition': data['weather'][0]['main'] if data.get('weather') else 'Unknown',
                'description': data['weather'][0]['description'] if data.get('weather') else '',
                'icon': data['weather'][0]['icon'] if data.get('weather') else '01d',
            }
            # Determine precipitation
            if 'rain' in weather['weather_condition'].lower():
                weather['precipitation'] = 'rain'
            elif 'snow' in weather['weather_condition'].lower():
                weather['precipitation'] = 'snow'
            else:
                weather['precipitation'] = 'none'

            weather['severity'] = classify_severity(weather['temperature_c'])
            return weather, None
        else:
            return None, f"API returned status {response.status_code}"
    except Exception as e:
        return None, str(e)


def get_demo_weather(city):
    """Generate demo weather data when API key is not available"""
    import random
    temp = random.uniform(-25, 35)
    return {
        'city': city,
        'country': 'US',
        'temperature_c': round(temp, 1),
        'feels_like_c': round(temp - random.uniform(2, 8), 1),
        'humidity': round(random.uniform(30, 95), 1),
        'wind_speed_kmh': round(random.uniform(0, 50), 1),
        'pressure_hpa': round(random.uniform(990, 1030), 1),
        'weather_condition': 'Clear' if temp > 5 else ('Snow' if temp < -5 else 'Cloudy'),
        'description': 'demo weather data',
        'icon': '01d',
        'precipitation': 'snow' if temp < -5 else ('rain' if temp < 10 and random.random() > 0.5 else 'none'),
        'severity': classify_severity(temp),
    }


@weather_bp.route('/')
@login_required
def index():
    return render_template('weather/index.html')


@weather_bp.route('/api/current')
@login_required
def get_current_weather():
    city = request.args.get('city', 'New York')
    print(f"[DEBUG] Fetching weather for city: {city}")
    api_key = current_app.config.get('OPENWEATHERMAP_API_KEY', 'demo')

    if api_key and api_key != 'demo':
        weather, error = fetch_openweathermap(city, api_key)
        if error:
            weather = get_demo_weather(city)
            weather['note'] = f'Using demo data. API error: {error}'
    else:
        weather = get_demo_weather(city)
        weather['note'] = 'Using demo data. Set OPENWEATHERMAP_API_KEY for real data.'

    # Log weather
    try:
        log = WeatherLog(
            city=weather['city'],
            country=weather.get('country', ''),
            temperature_c=weather['temperature_c'],
            feels_like_c=weather.get('feels_like_c'),
            humidity=weather.get('humidity'),
            wind_speed_kmh=weather.get('wind_speed_kmh'),
            pressure_hpa=weather.get('pressure_hpa'),
            weather_condition=weather.get('weather_condition'),
            precipitation=weather.get('precipitation'),
            severity=weather.get('severity'),
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()

    return jsonify(weather)


@weather_bp.route('/api/forecast')
@login_required
def get_forecast():
    city = request.args.get('city', 'New York')
    api_key = current_app.config.get('OPENWEATHERMAP_API_KEY', 'demo')

    if api_key and api_key != 'demo':
        url = f"https://api.openweathermap.org/data/2.5/forecast"
        params = {'q': city, 'appid': api_key, 'units': 'metric', 'cnt': 40}
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                forecasts = []
                for item in data.get('list', []):
                    forecasts.append({
                        'datetime': item['dt_txt'],
                        'temperature_c': item['main']['temp'],
                        'humidity': item['main']['humidity'],
                        'wind_speed_kmh': item['wind']['speed'] * 3.6,
                        'weather': item['weather'][0]['main'] if item.get('weather') else 'Unknown',
                        'severity': classify_severity(item['main']['temp']),
                    })
                return jsonify({'city': city, 'forecasts': forecasts})
        except Exception:
            pass

    # Demo forecast
    import random
    forecasts = []
    base_temp = random.uniform(-15, 20)
    for i in range(24):
        temp = base_temp + random.uniform(-5, 5)
        forecasts.append({
            'datetime': f'2024-01-{15 + i // 8:02d} {(i * 3) % 24:02d}:00:00',
            'temperature_c': round(temp, 1),
            'humidity': round(random.uniform(40, 90), 1),
            'wind_speed_kmh': round(random.uniform(5, 40), 1),
            'weather': 'Snow' if temp < -5 else ('Rain' if temp < 5 else 'Clear'),
            'severity': classify_severity(temp),
        })
    return jsonify({'city': city, 'forecasts': forecasts, 'note': 'Demo data'})


@weather_bp.route('/api/history')
@login_required
def get_history():
    city = request.args.get('city', '')
    limit = request.args.get('limit', 50, type=int)

    query = WeatherLog.query
    if city:
        query = query.filter(WeatherLog.city.ilike(f'%{city}%'))

    logs = query.order_by(WeatherLog.fetched_at.desc()).limit(limit).all()
    return jsonify([l.to_dict() for l in logs])
