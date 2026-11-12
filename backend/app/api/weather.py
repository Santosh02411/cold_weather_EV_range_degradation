from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required
import requests
from datetime import datetime, timedelta
from ..models.dataset import WeatherLog
from .. import db
from ..services import cache

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


def _parse_owm_response(data, fallback_label):
    weather = {
        'city': data.get('name', fallback_label),
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
    if 'rain' in weather['weather_condition'].lower():
        weather['precipitation'] = 'rain'
    elif 'snow' in weather['weather_condition'].lower():
        weather['precipitation'] = 'snow'
    else:
        weather['precipitation'] = 'none'
    weather['severity'] = classify_severity(weather['temperature_c'])
    weather['data_source'] = 'live'
    return weather


def fetch_openweathermap(city, api_key):
    """Fetch weather from OpenWeatherMap API by city name"""
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {'q': city, 'appid': api_key, 'units': 'metric'}
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return _parse_owm_response(response.json(), city), None
        else:
            return None, f"API returned status {response.status_code}"
    except Exception as e:
        return None, str(e)


def fetch_openweathermap_by_coords(lat, lon, api_key):
    """RT-6: fetch weather by lat/lon instead of a city name -- needed
    for route waypoints, which only have coordinates (no place name).
    More precise than a name lookup anyway (no geocoding ambiguity)."""
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {'lat': lat, 'lon': lon, 'appid': api_key, 'units': 'metric'}
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return _parse_owm_response(response.json(), f"{lat:.2f},{lon:.2f}"), None
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
        'data_source': 'demo_fallback',
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
    ttl = current_app.config.get('WEATHER_CACHE_TTL_SECONDS', 600)

    def _fetch():
        if api_key and api_key != 'demo':
            w, error = fetch_openweathermap(city, api_key)
            if error:
                w = get_demo_weather(city)
                w['note'] = f'Using demo data. API error: {error}'
        else:
            w = get_demo_weather(city)
            w['note'] = 'Using demo data. Set OPENWEATHERMAP_API_KEY for real data.'
        return w

    if ttl > 0:
        # Demo data is intentionally randomized per call (see
        # get_demo_weather) -- caching it would make the demo experience
        # feel frozen/fake in an obvious way, so only cache real API
        # responses, keyed by city + whether we're in real-data mode.
        cache_key = f"weather:{city.lower()}:{'live' if api_key and api_key != 'demo' else 'demo-uncached'}"
        if api_key and api_key != 'demo':
            weather, was_cached = cache.get_or_set(cache_key, ttl, _fetch)
            weather['cache_hit'] = was_cached
        else:
            weather = _fetch()
            weather['cache_hit'] = False
    else:
        weather = _fetch()
        weather['cache_hit'] = False

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
            data_source=weather.get('data_source'),
            error_note=weather.get('note'),
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
                    weather_main = item['weather'][0]['main'] if item.get('weather') else 'Unknown'
                    forecasts.append({
                        'datetime': item['dt_txt'],
                        'temperature_c': item['main']['temp'],
                        'humidity': item['main']['humidity'],
                        'wind_speed_kmh': item['wind']['speed'] * 3.6,
                        'weather': weather_main,
                        'precipitation': _weather_text_to_precipitation(weather_main),
                        'severity': classify_severity(item['main']['temp']),
                    })
                return jsonify({'city': city, 'forecasts': forecasts, 'data_source': 'live'})
        except Exception:
            pass

    # Demo forecast. Real bug fixed here: this used to hardcode dates to
    # "2024-01-..." regardless of the actual current date, which made a
    # "plan for a future date" feature built on top of it show
    # nonsensical, obviously-wrong dates in demo mode. Now generated
    # relative to today.
    import random
    forecasts = []
    base_temp = random.uniform(-15, 20)
    now = datetime.utcnow()
    for i in range(24):
        temp = base_temp + random.uniform(-5, 5)
        forecast_time = now + timedelta(hours=3 * i)
        weather_label = 'Snow' if temp < -5 else ('Rain' if temp < 5 else 'Clear')
        forecasts.append({
            'datetime': forecast_time.strftime('%Y-%m-%d %H:%M:%S'),
            'temperature_c': round(temp, 1),
            'humidity': round(random.uniform(40, 90), 1),
            'wind_speed_kmh': round(random.uniform(5, 40), 1),
            'weather': weather_label,
            'precipitation': _weather_text_to_precipitation(weather_label),
            'severity': classify_severity(temp),
        })
    return jsonify({'city': city, 'forecasts': forecasts, 'note': 'Demo data', 'data_source': 'demo_fallback'})


def _weather_text_to_precipitation(weather_main):
    """Map OpenWeatherMap's free-text 'weather' condition to the
    none/rain/snow categories the prediction model's precipitation
    feature expects -- needed so a selected forecast slot can feed
    directly into a prediction (new: forecast-based predictions)."""
    w = (weather_main or '').lower()
    if 'snow' in w:
        return 'snow'
    if 'rain' in w or 'drizzle' in w or 'thunderstorm' in w:
        return 'rain'
    return 'none'


@weather_bp.route('/api/temperature-exposure')
@login_required
def temperature_exposure():
    """Battery Temperature Analysis: real aggregate exposure stats
    (not a fabricated internal-battery-temperature model -- see
    services/battery_intelligence.py's module docstring for why) from
    every weather lookup this app has actually logged for a city."""
    city = request.args.get('city', '').strip()
    if not city:
        return jsonify({'error': 'city is required'}), 400
    days_back = request.args.get('days_back', type=int)

    from ..services.battery_intelligence import temperature_exposure_analysis
    return jsonify(temperature_exposure_analysis(city, days_back))


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
