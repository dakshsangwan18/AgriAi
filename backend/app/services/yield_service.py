import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import pandas as pd
from typing import Dict

class YieldService:
    # Crop data with typical yield ranges (quintals per hectare)
    CROP_DATA = {
        "wheat": {"min_yield": 25, "max_yield": 50, "optimal_temp": 22, "optimal_rainfall": 600},
        "rice": {"min_yield": 30, "max_yield": 60, "optimal_temp": 25, "optimal_rainfall": 1200},
        "cotton": {"min_yield": 15, "max_yield": 35, "optimal_temp": 28, "optimal_rainfall": 700},
        "sugarcane": {"min_yield": 600, "max_yield": 1000, "optimal_temp": 28, "optimal_rainfall": 1500},
        "maize": {"min_yield": 30, "max_yield": 70, "optimal_temp": 24, "optimal_rainfall": 600},
        "soybean": {"min_yield": 15, "max_yield": 30, "optimal_temp": 26, "optimal_rainfall": 500},
        "potato": {"min_yield": 200, "max_yield": 400, "optimal_temp": 18, "optimal_rainfall": 500},
        "tomato": {"min_yield": 300, "max_yield": 600, "optimal_temp": 24, "optimal_rainfall": 600},
    }
    
    SOIL_TYPES = ["loamy", "clay", "sandy", "black", "red", "alluvial"]
    CROP_ALIASES = {
        "corn": "maize",
        "soyabean": "soybean",
    }
    
    def __init__(self):
      self.label_encoders = {}
      self.model = self._train_model()
      
    
    def _train_model(self):
        # Generate synthetic training data
        np.random.seed(42)
        n_samples = 1000
        
        crops = list(self.CROP_DATA.keys())
        
        training_data = []
        for _ in range(n_samples):
            crop = np.random.choice(crops)
            crop_info = self.CROP_DATA[crop]
            
            # Generate features
            area = np.random.uniform(0.5, 10)  # hectares
            rainfall = np.random.uniform(300, 2000)  # mm
            temperature = np.random.uniform(15, 35)  # celsius
            soil_ph = np.random.uniform(5.5, 8.5)
            nitrogen = np.random.uniform(20, 100)  # kg/ha
            phosphorus = np.random.uniform(20, 80)  # kg/ha
            potassium = np.random.uniform(20, 80)  # kg/ha
            
            # Calculate yield based on conditions
            base_yield = (crop_info["min_yield"] + crop_info["max_yield"]) / 2
            
            # Adjust for environmental factors
            temp_factor = 1 - abs(temperature - crop_info["optimal_temp"]) / 20
            rain_factor = 1 - abs(rainfall - crop_info["optimal_rainfall"]) / 1000
            ph_factor = 1 - abs(soil_ph - 7.0) / 2
            nutrient_factor = (nitrogen + phosphorus + potassium) / 240
            
            yield_per_ha = base_yield * temp_factor * rain_factor * ph_factor * nutrient_factor
            yield_per_ha = max(crop_info["min_yield"], min(crop_info["max_yield"], yield_per_ha))
            
            total_yield = yield_per_ha * area
            
            training_data.append({
                'crop': crop,
                'area': area,
                'rainfall': rainfall,
                'temperature': temperature,
                'soil_ph': soil_ph,
                'nitrogen': nitrogen,
                'phosphorus': phosphorus,
                'potassium': potassium,
                'yield': total_yield
            })
        
        df = pd.DataFrame(training_data)
        
        # Encode categorical variables
        self.label_encoders['crop'] = LabelEncoder()
        df['crop_encoded'] = self.label_encoders['crop'].fit_transform(df['crop'])
        
        # Features and target
        X = df[['crop_encoded', 'area', 'rainfall', 'temperature', 'soil_ph', 
                'nitrogen', 'phosphorus', 'potassium']]
        y = df['yield']
        
        # Train model
        model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
        model.fit(X, y)
        
        return model
    
    def predict_yield(self, crop: str, area: float, rainfall: float, temperature: float,
                     soil_ph: float, nitrogen: float, phosphorus: float, potassium: float) -> Dict:
        try:
            crop_key = self.CROP_ALIASES.get(crop.lower(), crop.lower())
            if crop_key not in self.CROP_DATA:
                return {"error": f"Crop '{crop}' not supported. Supported crops: {', '.join(self.CROP_DATA.keys())}"}
            
            crop_info = self.CROP_DATA[crop_key]
            
            # Encode crop
            crop_encoded = self.label_encoders['crop'].transform([crop_key])[0]
            
            # Prepare features
            features = np.array([[crop_encoded, area, rainfall, temperature, soil_ph,
                                nitrogen, phosphorus, potassium]])
            
            # Predict
            predicted_yield = self.model.predict(features)[0]
            yield_per_hectare = predicted_yield / area
            
            # Calculate confidence and recommendations
            recommendations = self._generate_recommendations(
                crop_key, temperature, rainfall, soil_ph, nitrogen, phosphorus, potassium
            )
            
            # Calculate optimal vs actual
            optimal_conditions = self._check_optimal_conditions(
                crop_key, temperature, rainfall, soil_ph
            )
            
            return {
                "crop": crop_key,
                "area_hectares": round(area, 2),
                "predicted_total_yield": round(predicted_yield, 2),
                "predicted_yield_per_hectare": round(yield_per_hectare, 2),
                "unit": "quintals",
                "expected_range": {
                    "min": round(crop_info["min_yield"] * area, 2),
                    "max": round(crop_info["max_yield"] * area, 2)
                },
                "optimal_conditions": optimal_conditions,
                "recommendations": recommendations,
                "input_parameters": {
                    "rainfall_mm": rainfall,
                    "temperature_celsius": temperature,
                    "soil_ph": soil_ph,
                    "nitrogen_kg_per_ha": nitrogen,
                    "phosphorus_kg_per_ha": phosphorus,
                    "potassium_kg_per_ha": potassium
                }
            }
        
        except Exception as e:
            return {"error": str(e)}
    
    def _check_optimal_conditions(self, crop: str, temperature: float, 
                                  rainfall: float, soil_ph: float) -> Dict:
        crop_info = self.CROP_DATA[crop]
        
        temp_diff = abs(temperature - crop_info["optimal_temp"])
        rain_diff = abs(rainfall - crop_info["optimal_rainfall"])
        ph_diff = abs(soil_ph - 7.0)
        
        conditions = {
            "temperature": "optimal" if temp_diff < 3 else "suboptimal" if temp_diff < 6 else "poor",
            "rainfall": "optimal" if rain_diff < 200 else "suboptimal" if rain_diff < 500 else "poor",
            "soil_ph": "optimal" if ph_diff < 0.5 else "suboptimal" if ph_diff < 1.5 else "poor",
            "overall_score": 0
        }
        
        # Calculate overall score (0-100)
        temp_score = max(0, 100 - (temp_diff * 5))
        rain_score = max(0, 100 - (rain_diff / 10))
        ph_score = max(0, 100 - (ph_diff * 20))
        
        conditions["overall_score"] = round((temp_score + rain_score + ph_score) / 3, 1)
        
        return conditions
    
    def _generate_recommendations(self, crop: str, temperature: float, rainfall: float,
                                 soil_ph: float, nitrogen: float, phosphorus: float, 
                                 potassium: float) -> list:
        recommendations = []
        crop_info = self.CROP_DATA[crop]
        
        # Temperature recommendations
        if temperature < crop_info["optimal_temp"] - 5:
            recommendations.append({
                "type": "temperature",
                "priority": "high",
                "message": f"Temperature is too low. Consider delaying planting or use protective covers."
            })
        elif temperature > crop_info["optimal_temp"] + 5:
            recommendations.append({
                "type": "temperature",
                "priority": "high",
                "message": f"Temperature is too high. Ensure adequate irrigation and consider shade nets."
            })
        
        # Rainfall recommendations
        if rainfall < crop_info["optimal_rainfall"] - 300:
            recommendations.append({
                "type": "irrigation",
                "priority": "high",
                "message": f"Rainfall is insufficient. Plan for supplementary irrigation."
            })
        elif rainfall > crop_info["optimal_rainfall"] + 500:
            recommendations.append({
                "type": "drainage",
                "priority": "medium",
                "message": f"Excessive rainfall expected. Ensure proper drainage to prevent waterlogging."
            })
        
        # Soil pH recommendations
        if soil_ph < 6.0:
            recommendations.append({
                "type": "soil",
                "priority": "medium",
                "message": f"Soil is acidic (pH {soil_ph}). Consider adding lime to raise pH."
            })
        elif soil_ph > 8.0:
            recommendations.append({
                "type": "soil",
                "priority": "medium",
                "message": f"Soil is alkaline (pH {soil_ph}). Consider adding sulfur or organic matter."
            })
        
        # Nutrient recommendations
        if nitrogen < 40:
            recommendations.append({
                "type": "fertilizer",
                "priority": "high",
                "message": f"Nitrogen level is low. Apply urea or nitrogen-rich fertilizers."
            })
        
        if phosphorus < 30:
            recommendations.append({
                "type": "fertilizer",
                "priority": "medium",
                "message": f"Phosphorus level is low. Apply DAP or phosphate fertilizers."
            })
        
        if potassium < 30:
            recommendations.append({
                "type": "fertilizer",
                "priority": "medium",
                "message": f"Potassium level is low. Apply MOP (Muriate of Potash)."
            })
        
        # If no issues, add positive recommendation
        if not recommendations:
            recommendations.append({
                "type": "general",
                "priority": "low",
                "message": f"Conditions are optimal for {crop} cultivation. Continue with standard practices."
            })
        
        return recommendations
    
    @staticmethod
    def get_supported_crops():
        return list(YieldService.CROP_DATA.keys())
