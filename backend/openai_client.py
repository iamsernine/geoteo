"""
OpenAI Client
Handles AI-powered analytics and insights generation
"""

from openai import OpenAI
from typing import Dict, List, Optional, Any
from loguru import logger
import config
import json


class OpenAIClient:
    """Client for OpenAI API to generate smart analytics"""
    
    def __init__(self, api_key: Optional[str] = None, db: Optional[Any] = None):
        """
        Initialize OpenAI client
        
        Args:
            api_key: OpenAI API key (optional, uses config or database if not provided)
            db: Database instance to check for stored API keys
        """
        # Priority: provided > config (.env) > database
        self.api_key = api_key
        if not self.api_key:
            # First try config (which reads from .env)
            self.api_key = getattr(config, 'OPENAI_API_KEY', '')
        if not self.api_key and db:
            # Then try database
            try:
                self.api_key = db.get_api_key("openai")
            except Exception as e:
                logger.debug(f"Could not get OpenAI API key from database: {e}")
        
        # Clean up API key - remove whitespace and quotes
        if self.api_key:
            self.api_key = self.api_key.strip().strip('"').strip("'")
        
        self.model = getattr(config, 'OPENAI_MODEL', 'gpt-4o-mini')
        
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            # Log first and last 4 chars for debugging (without exposing full key)
            key_preview = f"{self.api_key[:4]}...{self.api_key[-4:]}" if len(self.api_key) > 8 else "***"
            logger.info(f"OpenAI client initialized with API key from {'config' if getattr(config, 'OPENAI_API_KEY', '') else 'database'}: {key_preview}")
        else:
            self.client = None
            logger.warning("OpenAI API key not configured. Add OPENAI_API_KEY to your .env file or configure it in Settings.")
    
    def _is_configured(self) -> bool:
        """Check if OpenAI is configured"""
        return bool(self.api_key)
    
    def generate_analytics_insights(self, air_quality_data: List[Dict], weather_data: Optional[Dict] = None) -> Dict:
        """
        Generate AI-powered insights from air quality and weather data
        
        Args:
            air_quality_data: List of location data with air quality metrics
            weather_data: Optional weather data dictionary
            
        Returns:
            Dictionary with AI-generated insights
        """
        if not self._is_configured():
            return {
                "error": "OpenAI API key not configured",
                "insights": [],
                "recommendations": [],
                "summary": "Please configure OPENAI_API_KEY in your .env file"
            }
        
        try:
            # Prepare data summary for AI
            data_summary = self._prepare_data_summary(air_quality_data, weather_data)
            
            # Create prompt for AI
            prompt = self._create_analytics_prompt(data_summary)
            
            # Call OpenAI API
            if not self.client:
                raise ValueError("OpenAI client not initialized")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert environmental data analyst specializing in air quality and meteorological analysis. Provide clear, actionable insights based on the data provided."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Parse response
            ai_response = response.choices[0].message.content
            
            # Clean up markdown code blocks if present (```json ... ``` or ``` ... ```)
            cleaned_response = ai_response.strip()
            if cleaned_response.startswith("```"):
                # Remove code block markers
                lines = cleaned_response.split("\n")
                # Remove first line if it's ```json or ```
                if lines[0].startswith("```"):
                    lines = lines[1:]
                # Remove last line if it's ```
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                cleaned_response = "\n".join(lines).strip()
            
            # Try to parse as JSON if possible, otherwise return as text
            try:
                insights = json.loads(cleaned_response)
            except json.JSONDecodeError:
                # If not JSON, structure it
                insights = {
                    "summary": ai_response,
                    "key_findings": self._extract_findings(ai_response),
                    "recommendations": self._extract_recommendations(ai_response)
                }
            
            return {
                "insights": insights,
                "raw_response": ai_response,
                "model_used": self.model
            }
            
        except Exception as e:
            logger.error(f"Error generating AI insights: {e}")
            return {
                "error": str(e),
                "insights": [],
                "recommendations": [],
                "summary": "Error generating insights. Please check your OpenAI API key and try again."
            }
    
    def _prepare_data_summary(self, air_quality_data: List[Dict], weather_data: Optional[Dict]) -> Dict:
        """Prepare a summary of the data for AI analysis"""
        if not air_quality_data:
            return {}
        
        # Calculate statistics
        aqi_values = [loc.get("max_aqi", 0) for loc in air_quality_data if isinstance(loc.get("max_aqi"), (int, float))]
        
        summary = {
            "total_locations": len(air_quality_data),
            "average_aqi": sum(aqi_values) / len(aqi_values) if aqi_values else 0,
            "max_aqi": max(aqi_values) if aqi_values else 0,
            "min_aqi": min(aqi_values) if aqi_values else 0,
            "high_pollution_count": len([aqi for aqi in aqi_values if aqi > 150]),
            "good_air_quality_count": len([aqi for aqi in aqi_values if aqi <= 50]),
            "top_polluted": sorted(air_quality_data, key=lambda x: x.get("max_aqi", 0), reverse=True)[:5],
            "countries": list(set([loc.get("country", "Unknown") for loc in air_quality_data]))
        }
        
        if weather_data:
            summary["weather"] = {
                "temperature": weather_data.get("temperature_c"),
                "humidity": weather_data.get("humidity"),
                "wind_speed": weather_data.get("wind_speed_kph"),
                "condition": weather_data.get("condition")
            }
        
        return summary
    
    def _create_analytics_prompt(self, data_summary: Dict) -> str:
        """Create a prompt for AI analysis"""
        prompt = f"""
Analyze the following air quality and meteorological data and provide:

1. **Key Findings**: Identify the most important patterns, trends, and anomalies
2. **Risk Assessment**: Evaluate health risks and environmental concerns
3. **Geographic Insights**: Note any regional patterns or country-specific issues
4. **Weather Correlation**: If weather data is available, analyze how weather conditions affect air quality
5. **Actionable Recommendations**: Provide specific, practical recommendations for:
   - Public health advisories
   - Environmental policy suggestions
   - Individual protective measures
   - Data collection improvements

Data Summary:
- Total Locations Monitored: {data_summary.get('total_locations', 0)}
- Average AQI: {data_summary.get('average_aqi', 0):.1f}
- Maximum AQI: {data_summary.get('max_aqi', 0)}
- Minimum AQI: {data_summary.get('min_aqi', 0)}
- High Pollution Locations (AQI > 150): {data_summary.get('high_pollution_count', 0)}
- Good Air Quality Locations (AQI ≤ 50): {data_summary.get('good_air_quality_count', 0)}
- Countries: {', '.join(data_summary.get('countries', []))}
- Top 5 Most Polluted Locations: {', '.join([loc.get('name', 'Unknown') for loc in data_summary.get('top_polluted', [])])}

Please provide a comprehensive analysis in JSON format with the following structure:
{{
    "summary": "Brief overall assessment",
    "key_findings": ["finding1", "finding2", "finding3"],
    "risk_assessment": "Assessment of health and environmental risks",
    "geographic_insights": "Regional patterns and observations",
    "weather_correlation": "How weather affects air quality (if applicable)",
    "recommendations": ["recommendation1", "recommendation2", "recommendation3"]
}}
"""
        return prompt
    
    def _extract_findings(self, text: str) -> List[str]:
        """Extract key findings from text response"""
        # Simple extraction - look for bullet points or numbered items
        findings = []
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                findings.append(line[1:].strip())
            elif any(line.startswith(f'{i}.') for i in range(1, 10)):
                findings.append(line[3:].strip())
        return findings[:5] if findings else ["Analysis completed"]
    
    def _extract_recommendations(self, text: str) -> List[str]:
        """Extract recommendations from text response"""
        # Look for recommendation section
        recommendations = []
        in_recommendations = False
        lines = text.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if 'recommendation' in line_lower or 'suggestion' in line_lower:
                in_recommendations = True
                continue
            if in_recommendations and line.strip():
                if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                    recommendations.append(line[1:].strip())
                elif any(line.startswith(f'{i}.') for i in range(1, 10)):
                    recommendations.append(line[3:].strip())
        
        return recommendations[:5] if recommendations else ["Continue monitoring air quality data"]
    
    def generate_city_comparison(self, cities_data: List[Dict]) -> Dict:
        """
        Generate AI-powered comparison between cities
        
        Args:
            cities_data: List of city data dictionaries
            
        Returns:
            Dictionary with comparison analysis
        """
        if not self._is_configured():
            return {"error": "OpenAI API key not configured"}
        
        try:
            prompt = f"""
Compare the following cities' air quality data and provide insights:

Cities Data:
{json.dumps(cities_data, indent=2)}

Provide a comparison analysis including:
1. Which cities have the best/worst air quality
2. Geographic patterns
3. Potential causes of differences
4. Recommendations for each city

Format as JSON with:
{{
    "comparison_summary": "Overall comparison",
    "best_city": "City name with best air quality",
    "worst_city": "City name with worst air quality",
    "insights": ["insight1", "insight2"],
    "recommendations": {{"city1": "rec1", "city2": "rec2"}}
}}
"""
            
            if not self.client:
                raise ValueError("OpenAI client not initialized")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert environmental analyst comparing air quality across different cities."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            ai_response = response.choices[0].message.content
            
            try:
                return json.loads(ai_response)
            except json.JSONDecodeError:
                return {"analysis": ai_response, "raw": True}
                
        except Exception as e:
            logger.error(f"Error generating city comparison: {e}")
            return {"error": str(e)}

