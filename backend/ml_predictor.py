"""
ML Predictor
Machine learning models for air quality prediction and forecasting
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger


class AirQualityPredictor:
    """Machine learning predictor for air quality forecasting"""
    
    def __init__(self):
        """Initialize ML predictor"""
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        logger.info("ML Predictor initialized")
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare features for ML model
        
        Args:
            df: DataFrame with measurements
            
        Returns:
            Tuple of (features DataFrame, target Series)
        """
        if df.empty or "datetime" not in df.columns or "value" not in df.columns:
            logger.warning("Insufficient data for feature preparation")
            return pd.DataFrame(), pd.Series()
        
        # Create time-based features
        df = df.copy()
        df["hour"] = df["datetime"].dt.hour
        df["day_of_week"] = df["datetime"].dt.dayofweek
        df["month"] = df["datetime"].dt.month
        df["day_of_year"] = df["datetime"].dt.dayofyear
        
        # Create lag features
        for lag in [1, 2, 3, 6, 12, 24]:
            df[f"lag_{lag}"] = df["value"].shift(lag)
        
        # Create rolling features
        for window in [3, 6, 12, 24]:
            df[f"rolling_mean_{window}"] = df["value"].rolling(window=window).mean()
            df[f"rolling_std_{window}"] = df["value"].rolling(window=window).std()
        
        # Drop rows with NaN values
        df = df.dropna()
        
        # Select features
        feature_cols = [
            "hour", "day_of_week", "month", "day_of_year",
            "lag_1", "lag_2", "lag_3", "lag_6", "lag_12", "lag_24",
            "rolling_mean_3", "rolling_mean_6", "rolling_mean_12", "rolling_mean_24",
            "rolling_std_3", "rolling_std_6", "rolling_std_12", "rolling_std_24"
        ]
        
        X = df[feature_cols]
        y = df["value"]
        
        return X, y
    
    def train(self, df: pd.DataFrame, model_type: str = "random_forest") -> Dict:
        """
        Train ML model on historical data
        
        Args:
            df: DataFrame with historical measurements
            model_type: Type of model ('random_forest' or 'gradient_boosting')
            
        Returns:
            Dictionary with training metrics
        """
        logger.info(f"Training {model_type} model")
        
        # Prepare features
        X, y = self.prepare_features(df)
        
        if X.empty or y.empty:
            logger.error("Cannot train model: insufficient data")
            return {"error": "Insufficient data for training"}
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        if model_type == "random_forest":
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
        else:  # gradient_boosting
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)
        
        self.is_trained = True
        
        metrics = {
            "model_type": model_type,
            "train_score": float(train_score),
            "test_score": float(test_score),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "features": list(X.columns)
        }
        
        logger.info(f"Model trained: R² = {test_score:.3f}")
        return metrics
    
    def predict_next_hours(self, df: pd.DataFrame, hours: int = 24) -> pd.DataFrame:
        """
        Predict air quality for next N hours
        
        Args:
            df: DataFrame with recent measurements
            hours: Number of hours to predict
            
        Returns:
            DataFrame with predictions
        """
        if not self.is_trained:
            logger.warning("Model not trained, training on provided data")
            self.train(df)
        
        if df.empty or "datetime" not in df.columns:
            logger.error("Cannot make predictions: insufficient data")
            return pd.DataFrame()
        
        # Prepare recent data
        recent_data = df.tail(48).copy()  # Use last 48 hours
        
        predictions = []
        current_time = recent_data["datetime"].max()
        
        for i in range(1, hours + 1):
            # Create features for next hour
            next_time = current_time + timedelta(hours=i)
            
            features = {
                "hour": next_time.hour,
                "day_of_week": next_time.dayofweek,
                "month": next_time.month,
                "day_of_year": next_time.dayofyear
            }
            
            # Add lag features from recent data
            recent_values = recent_data["value"].tail(24).values
            for lag in [1, 2, 3, 6, 12, 24]:
                if lag <= len(recent_values):
                    features[f"lag_{lag}"] = recent_values[-lag]
                else:
                    features[f"lag_{lag}"] = recent_values[0]
            
            # Add rolling features
            for window in [3, 6, 12, 24]:
                if window <= len(recent_values):
                    features[f"rolling_mean_{window}"] = np.mean(recent_values[-window:])
                    features[f"rolling_std_{window}"] = np.std(recent_values[-window:])
                else:
                    features[f"rolling_mean_{window}"] = np.mean(recent_values)
                    features[f"rolling_std_{window}"] = np.std(recent_values)
            
            # Make prediction
            X = pd.DataFrame([features])
            X_scaled = self.scaler.transform(X)
            prediction = self.model.predict(X_scaled)[0]
            
            predictions.append({
                "datetime": next_time,
                "predicted_value": max(0, prediction),  # Ensure non-negative
                "hour_ahead": i
            })
            
            # Add prediction to recent data for next iteration
            new_row = pd.DataFrame({
                "datetime": [next_time],
                "value": [prediction]
            })
            recent_data = pd.concat([recent_data, new_row], ignore_index=True)
        
        return pd.DataFrame(predictions)
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance from trained model
        
        Returns:
            Dictionary mapping feature names to importance scores
        """
        if not self.is_trained or self.model is None:
            logger.warning("Model not trained")
            return {}
        
        if hasattr(self.model, "feature_importances_"):
            importance = self.model.feature_importances_
            feature_names = [
                "hour", "day_of_week", "month", "day_of_year",
                "lag_1", "lag_2", "lag_3", "lag_6", "lag_12", "lag_24",
                "rolling_mean_3", "rolling_mean_6", "rolling_mean_12", "rolling_mean_24",
                "rolling_std_3", "rolling_std_6", "rolling_std_12", "rolling_std_24"
            ]
            
            return dict(zip(feature_names, importance.tolist()))
        
        return {}
    
    def generate_forecast_summary(self, predictions_df: pd.DataFrame) -> Dict:
        """
        Generate summary of forecast
        
        Args:
            predictions_df: DataFrame with predictions
            
        Returns:
            Dictionary with forecast summary
        """
        if predictions_df.empty:
            return {}
        
        summary = {
            "avg_predicted": float(predictions_df["predicted_value"].mean()),
            "max_predicted": float(predictions_df["predicted_value"].max()),
            "min_predicted": float(predictions_df["predicted_value"].min()),
            "trend": "stable"
        }
        
        # Determine trend
        first_half = predictions_df.head(len(predictions_df)//2)["predicted_value"].mean()
        second_half = predictions_df.tail(len(predictions_df)//2)["predicted_value"].mean()
        
        if second_half > first_half * 1.1:
            summary["trend"] = "increasing"
        elif second_half < first_half * 0.9:
            summary["trend"] = "decreasing"
        
        return summary
