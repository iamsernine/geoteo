# 🌍 AirWatch - Global Air Quality Monitoring Dashboard

**Real-time air quality monitoring and visualization platform with ML predictions**

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Dash](https://img.shields.io/badge/dash-2.18.0-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Screenshots](#screenshots)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Architecture](#architecture)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

**AirWatch** is a comprehensive air quality monitoring dashboard that provides real-time global air quality data visualization, analysis, and predictions. Built for the **Plateforme d'Analyse et de Visualisation de Données Géospatiales** academic project, it combines modern web technologies with machine learning to deliver actionable insights about air pollution worldwide.

### Key Highlights

- 🌐 **Global Coverage**: Monitor air quality from 100+ countries
- 📊 **Real-time Data**: Live updates from OpenAQ API
- 🗺️ **Interactive Maps**: 3D heatmaps, markers, and density visualizations
- 🤖 **ML Predictions**: 24-hour air quality forecasts
- 📈 **Advanced Analytics**: Trends, comparisons, and insights
- 📄 **PDF Reports**: Exportable professional reports
- 🌓 **Dark Mode**: Modern, eye-friendly interface
- 📱 **Responsive**: Works on desktop, tablet, and mobile

---

## ✨ Features

### Data Visualization

- **3 Map Types**:
  - 🗺️ **Markers**: Individual monitoring stations with AQI colors
  - 🔥 **Heatmap**: Density-based pollution visualization
  - 📍 **Density**: Smooth pollution gradients

- **Interactive Filters**:
  - Country selection
  - Quick access to major cities
  - Pollutant type selection (PM2.5, PM10, NO₂, O₃, SO₂, CO)

### Analytics & Insights

- **Real-time Statistics**:
  - Total monitoring stations
  - Countries covered
  - Average AQI
  - Last update timestamp

- **Multi-tab Analysis**:
  - 📊 **Overview**: Top polluted locations
  - 🏙️ **City Comparison**: Side-by-side comparisons
  - 📈 **Trends**: Historical patterns and predictions
  - 💡 **Insights**: AI-powered recommendations

### Machine Learning

- **Air Quality Predictions**:
  - 24-hour forecasts using Random Forest/Gradient Boosting
  - Feature importance analysis
  - Trend detection (increasing/decreasing/stable)

- **Health Recommendations**:
  - AQI-based health alerts
  - Specific advice for sensitive groups
  - Color-coded risk levels

### Export & Reporting

- **PDF Reports**:
  - Location-specific reports
  - Multi-location comparisons
  - Professional formatting with charts
  - Health recommendations included

---

## 🖼️ Screenshots

### Main Dashboard
![Dashboard](docs/screenshots/dashboard.png)

### Interactive Map
![Map](docs/screenshots/map.png)

### Analytics
![Analytics](docs/screenshots/analytics.png)

---

## 🚀 Installation

### Prerequisites

- Python 3.11 or higher
- Poetry (Python package manager)
- OpenAQ API key (free from [explore.openaq.org](https://explore.openaq.org))

### Quick Start

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/airwatch.git
cd airwatch
```

2. **Install Poetry** (if not already installed)

```bash
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"
```

3. **Install dependencies**

```bash
poetry install
```

4. **Configure environment**

```bash
cp .env.example .env
# Edit .env and add your OpenAQ API key
```

5. **Run the application**

```bash
poetry run python app.py
```

6. **Open in browser**

Navigate to `http://localhost:8050`

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# OpenAQ API Key (Required)
OPENAQ_API_KEY=your_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8050

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_SECRET_KEY=your-secret-key

# Cache Configuration
CACHE_TYPE=disk
CACHE_TIMEOUT=300

# Logging
LOG_LEVEL=INFO

# Data Refresh Interval (seconds)
DATA_REFRESH_INTERVAL=300
```

### Getting an OpenAQ API Key

1. Visit [explore.openaq.org](https://explore.openaq.org)
2. Sign up for a free account
3. Navigate to Settings
4. Copy your API key
5. Add it to your `.env` file

---

## 📖 Usage

### Running the Dashboard

```bash
# Development mode
poetry run python app.py

# Production mode (with Gunicorn)
poetry run gunicorn app:server -b 0.0.0.0:8050
```

### Accessing Features

1. **View Global Map**: Main page shows all monitoring stations
2. **Filter by Country**: Use dropdown to focus on specific country
3. **Quick City Access**: Select from major cities for instant zoom
4. **Change Map Type**: Toggle between Heatmap, Markers, and Density
5. **View Analytics**: Click on tabs for different analysis views
6. **Export Reports**: Use export button to generate PDF reports

### API Usage

The backend provides a Python API for programmatic access:

```python
from backend.api_client import OpenAQClient
from backend.data_processor import DataProcessor

# Initialize clients
api = OpenAQClient(api_key="your_key")
processor = DataProcessor()

# Get locations
locations = api.get_locations(country="FR", limit=10)

# Process data
for loc in locations:
    processed = processor.process_location_data(loc)
    aqi, category, color = processor.calculate_aqi("pm25", 35.5)
    print(f"{processed['name']}: AQI={aqi} ({category})")
```

---

## 🏗️ Architecture

### Project Structure

```
airwatch/
├── app.py                      # Main Dash application
├── config.py                   # Configuration management
├── pyproject.toml             # Poetry dependencies
├── .env.example               # Environment template
├── backend/                   # Backend modules
│   ├── __init__.py
│   ├── api_client.py         # OpenAQ API client
│   ├── cache_manager.py      # Caching system
│   ├── data_processor.py     # Data processing & AQI
│   ├── ml_predictor.py       # ML predictions
│   └── report_generator.py   # PDF generation
├── frontend/                  # Frontend components (future)
├── utils/                     # Utilities
│   ├── __init__.py
│   └── logger_setup.py       # Logging configuration
├── assets/                    # Static assets
│   └── custom.css            # Custom styles
├── data/                      # Data storage
│   └── cache/                # Cache directory
├── logs/                      # Application logs
├── exports/                   # Generated reports
└── docs/                      # Documentation

```

### Technology Stack

- **Frontend**: Dash, Plotly, Bootstrap 5
- **Backend**: Flask, Python 3.11
- **Data Processing**: Pandas, NumPy, SciPy
- **Machine Learning**: Scikit-learn
- **Visualization**: Plotly, Folium
- **Caching**: DiskCache
- **Logging**: Loguru
- **PDF Generation**: ReportLab
- **Package Management**: Poetry

### Data Flow

```
OpenAQ API → API Client → Cache Manager → Data Processor → Dash Frontend
                                              ↓
                                         ML Predictor
                                              ↓
                                      Report Generator
```

---

## 📡 API Documentation

### OpenAQ API Client

```python
client = OpenAQClient(api_key="your_key")

# Get locations
locations = client.get_locations(
    limit=100,
    country="FR",
    coordinates=(48.8566, 2.3522),
    radius=50000
)

# Get location details
location = client.get_location_by_id(8118)

# Get latest measurements
latest = client.get_latest_measurements(8118)

# Search by name
results = client.search_locations_by_name("Paris")
```

### Data Processor

```python
processor = DataProcessor()

# Calculate AQI
aqi, category, color = processor.calculate_aqi("pm25", 35.5)

# Get health recommendations
rec = processor.get_health_recommendation(category)

# Process location data
processed = processor.process_location_data(location_dict)

# Generate insights
insights = processor.generate_insights(location_data, measurements_df)
```

### ML Predictor

```python
predictor = AirQualityPredictor()

# Train model
metrics = predictor.train(historical_df, model_type="random_forest")

# Predict next 24 hours
predictions = predictor.predict_next_hours(recent_df, hours=24)

# Get feature importance
importance = predictor.get_feature_importance()
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Add docstrings to all functions
- Write unit tests for new features
- Update documentation as needed

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **OpenAQ** for providing free air quality data API
- **Plotly & Dash** for amazing visualization tools
- **Scikit-learn** for machine learning capabilities
- Academic project supervisor and peers

---

## 📧 Contact

For questions, suggestions, or issues:

- **GitHub Issues**: [github.com/yourusername/airwatch/issues](https://github.com/yourusername/airwatch/issues)
- **Email**: your.email@example.com

---

## 🌟 Star History

If you find this project useful, please consider giving it a star! ⭐

---

**Built with ❤️ for cleaner air and better health**
