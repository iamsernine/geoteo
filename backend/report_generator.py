"""
Report Generator
Generates PDF reports with air quality data and visualizations
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger
import config


class ReportGenerator:
    """Generates PDF reports for air quality data"""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize report generator
        
        Args:
            output_dir: Directory for saving reports
        """
        self.output_dir = output_dir or config.EXPORTS_DIR
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        logger.info(f"Report generator initialized (output: {self.output_dir})")
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2ca02c'),
            spaceAfter=12,
            spaceBefore=12
        ))
        
        # Info style
        self.styles.add(ParagraphStyle(
            name='Info',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.grey,
            alignment=TA_RIGHT
        ))
    
    def generate_location_report(self, 
                                 location_data: Dict, 
                                 measurements_df=None,
                                 predictions_df=None,
                                 insights: Optional[List[str]] = None,
                                 weather_data: Optional[Dict] = None,
                                 forecast_data: Optional[Dict] = None,
                                 weather_analysis: Optional[Dict] = None) -> str:
        """
        Generate comprehensive GeoTEO (Geospatial + Meteo) report for a location
        
        Args:
            location_data: Processed location data
            measurements_df: DataFrame with measurements (optional)
            predictions_df: DataFrame with predictions (optional)
            insights: List of insight strings (optional)
            weather_data: Current weather data dictionary (optional)
            forecast_data: Weather forecast data dictionary (optional)
            weather_analysis: Weather-air quality correlation analysis (optional)
            
        Returns:
            Path to generated PDF file
        """
        # Generate filename
        location_name = location_data.get("name", "Unknown").replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"airwatch_report_{location_name}_{timestamp}.pdf"
        filepath = self.output_dir / filename
        
        logger.info(f"Generating report: {filepath}")
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Container for elements
        story = []
        
        # Header
        story.append(Paragraph("GeoTEO", self.styles['CustomTitle']))
        story.append(Paragraph("Geospatial + Meteorological Report", self.styles['Heading2']))
        story.append(Spacer(1, 0.2*inch))
        
        # Report info
        report_info = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        story.append(Paragraph(report_info, self.styles['Info']))
        story.append(Spacer(1, 0.3*inch))
        
        # Location Information
        story.append(Paragraph("Location Information", self.styles['CustomSubtitle']))
        
        location_info = [
            ["Location:", location_data.get("name", "Unknown")],
            ["Country:", location_data.get("country", "Unknown")],
            ["Coordinates:", f"{location_data.get('coordinates', {}).get('latitude', 'N/A')}, "
                           f"{location_data.get('coordinates', {}).get('longitude', 'N/A')}"],
            ["Monitoring Station ID:", str(location_data.get("id", "N/A"))]
        ]
        
        location_table = Table(location_info, colWidths=[2*inch, 4*inch])
        location_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        story.append(location_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Current Air Quality
        story.append(Paragraph("Current Air Quality", self.styles['CustomSubtitle']))
        
        aqi = location_data.get("max_aqi", 0)
        category = location_data.get("max_aqi_category", "Unknown")
        
        aqi_info = [
            ["Air Quality Index (AQI):", str(aqi)],
            ["Category:", category],
            ["Status:", self._get_status_icon(category)]
        ]
        
        aqi_table = Table(aqi_info, colWidths=[2*inch, 4*inch])
        aqi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        story.append(aqi_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Health Recommendations
        story.append(Paragraph("Health Recommendations", self.styles['CustomSubtitle']))
        
        health_rec = config.HEALTH_RECOMMENDATIONS.get(category, {})
        general_rec = health_rec.get("general", "No recommendations available")
        sensitive_rec = health_rec.get("sensitive", "No recommendations available")
        
        story.append(Paragraph(f"<b>General Public:</b> {general_rec}", self.styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(f"<b>Sensitive Groups:</b> {sensitive_rec}", self.styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Monitored Pollutants
        if location_data.get("sensors"):
            story.append(Paragraph("Monitored Pollutants", self.styles['CustomSubtitle']))
            
            pollutant_data = []
            pollutant_data.append(["Pollutant", "Units", "Sensor ID"])
            
            for sensor in location_data["sensors"]:
                pollutant_data.append([
                    sensor.get("display_name", "Unknown"),
                    sensor.get("units", "N/A"),
                    str(sensor.get("id", "N/A"))
                ])
            
            pollutant_table = Table(pollutant_data, colWidths=[2*inch, 1.5*inch, 2.5*inch])
            pollutant_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')])
            ]))
            
            story.append(pollutant_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Weather Information Section
        if weather_data:
            story.append(Paragraph("Current Weather Conditions", self.styles['CustomSubtitle']))
            
            weather_info = [
                ["Temperature:", f"{weather_data.get('temperature_c', 'N/A')}°C ({weather_data.get('feels_like_c', 'N/A')}°C feels like)"],
                ["Condition:", weather_data.get('condition', 'N/A')],
                ["Wind Speed:", f"{weather_data.get('wind_speed_kph', 'N/A')} km/h ({weather_data.get('wind_direction', 'N/A')})"],
                ["Humidity:", f"{weather_data.get('humidity', 'N/A')}%"],
                ["Pressure:", f"{weather_data.get('pressure_mb', 'N/A')} mb"],
                ["UV Index:", str(weather_data.get('uv_index', 'N/A'))],
                ["Visibility:", f"{weather_data.get('visibility_km', 'N/A')} km"],
                ["Cloud Cover:", f"{weather_data.get('cloud_cover', 'N/A')}%"]
            ]
            
            weather_table = Table(weather_info, colWidths=[2*inch, 4*inch])
            weather_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            
            story.append(weather_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Weather Forecast Section
        if forecast_data and forecast_data.get("forecast"):
            story.append(Paragraph("3-Day Weather Forecast", self.styles['CustomSubtitle']))
            
            forecast_info = [["Date", "Max/Min Temp", "Condition", "Wind", "Humidity", "UV"]]
            
            for day in forecast_data["forecast"]:
                forecast_info.append([
                    day.get("date", "N/A"),
                    f"{day.get('max_temp_c', '--')}°C / {day.get('min_temp_c', '--')}°C",
                    day.get("condition", "N/A"),
                    f"{day.get('max_wind_kph', '--')} km/h",
                    f"{day.get('avg_humidity', '--')}%",
                    str(day.get("uv_index", "--"))
                ])
            
            forecast_table = Table(forecast_info, colWidths=[1.2*inch, 1.2*inch, 1.2*inch, 1*inch, 0.8*inch, 0.6*inch])
            forecast_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')])
            ]))
            
            story.append(forecast_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Weather-Air Quality Correlation Analysis
        if weather_analysis:
            story.append(Paragraph("Weather-Air Quality Correlation Analysis", self.styles['CustomSubtitle']))
            
            analysis_info = [
                ["Wind Impact:", weather_analysis.get("wind_impact", "unknown").title()],
                ["Humidity Impact:", weather_analysis.get("humidity_impact", "unknown").title()],
                ["Temperature Impact:", weather_analysis.get("temperature_impact", "unknown").title()],
                ["Overall Conditions:", weather_analysis.get("overall_conditions", "unknown").title()]
            ]
            
            analysis_table = Table(analysis_info, colWidths=[2*inch, 4*inch])
            analysis_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            
            story.append(analysis_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Insights
        if insights:
            story.append(Paragraph("Key Insights & Recommendations", self.styles['CustomSubtitle']))
            
            for i, insight in enumerate(insights, 1):
                story.append(Paragraph(f"{i}. {insight}", self.styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
            
            story.append(Spacer(1, 0.3*inch))
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        footer_text = "This GeoTEO report was generated by AirWatch - Geospatial & Meteorological Analysis Dashboard"
        story.append(Paragraph(footer_text, self.styles['Info']))
        
        # Build PDF
        doc.build(story)
        
        logger.info(f"Report generated successfully: {filepath}")
        return str(filepath)
    
    def _get_status_icon(self, category: str) -> str:
        """Get status icon for category"""
        icons = {
            "Good": "✓ Excellent",
            "Moderate": "⚠ Acceptable",
            "Unhealthy for Sensitive Groups": "⚠ Caution",
            "Unhealthy": "✗ Poor",
            "Very Unhealthy": "✗ Very Poor",
            "Hazardous": "✗ Hazardous"
        }
        return icons.get(category, "? Unknown")
    
    def generate_comparison_report(self, locations_data: List[Dict]) -> str:
        """
        Generate comparison report for multiple locations
        
        Args:
            locations_data: List of processed location data
            
        Returns:
            Path to generated PDF file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"airwatch_comparison_{timestamp}.pdf"
        filepath = self.output_dir / filename
        
        logger.info(f"Generating comparison report: {filepath}")
        
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        
        # Header
        story.append(Paragraph("AirWatch", self.styles['CustomTitle']))
        story.append(Paragraph("Multi-Location Comparison Report", self.styles['Heading2']))
        story.append(Spacer(1, 0.3*inch))
        
        # Comparison table
        comparison_data = []
        comparison_data.append(["Location", "Country", "AQI", "Category"])
        
        for loc in sorted(locations_data, key=lambda x: x.get("max_aqi", 0), reverse=True):
            comparison_data.append([
                loc.get("name", "Unknown"),
                loc.get("country", "Unknown"),
                str(loc.get("max_aqi", 0)),
                loc.get("max_aqi_category", "Unknown")
            ])
        
        comparison_table = Table(comparison_data, colWidths=[2*inch, 1.5*inch, 1*inch, 2*inch])
        comparison_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')])
        ]))
        
        story.append(comparison_table)
        
        # Build PDF
        doc.build(story)
        
        logger.info(f"Comparison report generated: {filepath}")
        return str(filepath)
