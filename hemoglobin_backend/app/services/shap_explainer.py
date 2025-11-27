"""
SHAP-based feature importance explainer.
Explains which features contribute most to hemoglobin predictions.
"""
import numpy as np
import shap
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import io
import base64
from typing import Dict, List, Tuple
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# Feature names for the 18 extracted features
FEATURE_NAMES = [
    'L* (Lightness)',
    'a* (Red-Green)',
    'b* (Blue-Yellow)',
    'Mean Red',
    'Mean Green',
    'Mean Blue',
    'R/G Ratio',
    'R/B Ratio',
    'GLCM Contrast',
    'GLCM Homogeneity',
    'GLCM Energy',
    'LBP Uniformity',
    'FFT High Freq',
    'Vessel Density',
    'Vessel Thickness',
    'Orientation Entropy',
    'L* Std Dev',
    'a*/L* Ratio'
]


class SHAPExplainer:
    """
    SHAP-based explainer for feature importance.
    Works with the mock prediction model to explain feature contributions.
    """
    
    def __init__(self):
        """Initialize SHAP explainer."""
        self.feature_names = FEATURE_NAMES
        logger.info("SHAP Explainer initialized")
    
    def calculate_feature_importance(self, features: Dict) -> Dict:
        """
        Calculate feature importance using a simplified approach.
        
        For the mock prediction model, we can calculate importance based on
        the actual formula weights used in predict_mock_from_features().
        
        Args:
            features: Extracted features dict
            
        Returns:
            Dict with feature importance analysis
        """
        try:
            # Extract feature values
            color = features['color']
            texture = features['texture']
            vascular = features['vascular']
            
            # Create feature array matching the order in FEATURE_NAMES
            feature_values = np.array([
                color['mean_L'],
                color['mean_a'],
                color['mean_b'],
                color['mean_R'],
                color['mean_G'],
                color['mean_B'],
                color['ratio_R_G'],
                color['ratio_R_B'],
                texture['glcm_contrast'],
                texture['glcm_homogeneity'],
                texture['glcm_energy'],
                texture['lbp_uniformity'],
                texture['fft_highfreq_power'],
                vascular['vessel_density'],
                vascular['mean_thickness'],
                vascular['orientation_entropy'],
                color['std_L'],
                color['ratio_a_L']
            ])
            
            # Calculate importance based on mock prediction formula
            # These weights reflect the actual contribution in predict_mock_from_features()
            importance_scores = np.zeros(18)
            
            # L* (index 0) - most important (used in L_factor calculation)
            L_normalized = (color['mean_L'] - 60) / 20.0
            L_contribution = abs(-L_normalized * 2.0)
            importance_scores[0] = L_contribution
            
            # R/G ratio (index 6) - second most important
            rg_normalized = (color['ratio_R_G'] - 1.05) / 0.15
            rg_contribution = abs(rg_normalized * 1.5)
            importance_scores[6] = rg_contribution
            
            # Vessel density (index 13) - third most important
            vessel_normalized = (vascular['vessel_density'] - 0.15) / 0.1
            vessel_contribution = abs(vessel_normalized * 0.8)
            importance_scores[13] = vessel_contribution
            
            # Mean Red (index 3) - fourth most important
            red_normalized = (color['mean_R'] - 150) / 50.0
            red_contribution = abs(red_normalized * 0.5)
            importance_scores[3] = red_contribution
            
            # LBP Uniformity (index 11) - affects uncertainty/confidence
            texture_contribution = abs(texture.get('lbp_uniformity', 0.5) - 0.5) * 0.4
            importance_scores[11] = texture_contribution
            
            # Normalize importance scores to sum to 1
            total_importance = np.sum(importance_scores)
            if total_importance > 0:
                importance_scores = importance_scores / total_importance
            
            # Create feature importance list
            feature_importance = []
            for i, (name, value, importance) in enumerate(zip(self.feature_names, feature_values, importance_scores)):
                if importance > 0.01:  # Only include features with >1% importance
                    feature_importance.append({
                        'name': name,
                        'value': float(value),
                        'importance': float(importance),
                        'contribution': float(importance * 100)  # As percentage
                    })
            
            # Sort by importance (descending)
            feature_importance.sort(key=lambda x: x['importance'], reverse=True)
            
            # Generate interpretation
            top_feature = feature_importance[0] if feature_importance else None
            interpretation = self._generate_interpretation(feature_importance)
            
            result = {
                'top_features': feature_importance[:5],  # Top 5 features
                'all_features': feature_importance,
                'interpretation': interpretation,
                'method': 'formula_based'  # Indicates this is based on the mock formula
            }
            
            logger.info(f"Feature importance calculated: top feature = {top_feature['name'] if top_feature else 'none'}")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating feature importance: {e}")
            return {
                'top_features': [],
                'all_features': [],
                'interpretation': f'Feature importance calculation failed: {str(e)}',
                'method': 'error'
            }
    
    def _generate_interpretation(self, feature_importance: List[Dict]) -> str:
        """Generate human-readable interpretation of feature importance."""
        if not feature_importance:
            return "No significant features identified."
        
        top_3 = feature_importance[:3]
        
        interpretation_parts = []
        interpretation_parts.append(f"The prediction was primarily influenced by {len(feature_importance)} features:")
        
        for i, feat in enumerate(top_3, 1):
            interpretation_parts.append(
                f"{i}. **{feat['name']}** ({feat['contribution']:.1f}% contribution, value: {feat['value']:.2f})"
            )
        
        # Add clinical context
        if feature_importance[0]['name'] == 'L* (Lightness)':
            interpretation_parts.append("\nL* lightness is the primary indicator - darker nail beds typically indicate higher hemoglobin levels.")
        
        if any(f['name'] == 'R/G Ratio' for f in top_3):
            interpretation_parts.append("The red/green color ratio helps assess blood oxygenation in the nail bed.")
        
        if any(f['name'] == 'Vessel Density' for f in top_3):
            interpretation_parts.append("Blood vessel density in the nail bed provides additional hemoglobin information.")
        
        return "\n".join(interpretation_parts)
    
    def generate_visualization(self, feature_importance: List[Dict]) -> str:
        """
        Generate a bar chart visualization of feature importance.
        
        Args:
            feature_importance: List of feature importance dicts
            
        Returns:
            Base64 encoded PNG image
        """
        try:
            if not feature_importance:
                return ""
            
            # Take top 8 features for visualization
            top_features = feature_importance[:8]
            
            # Create figure
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Extract data
            names = [f['name'] for f in top_features]
            importances = [f['contribution'] for f in top_features]
            
            # Create horizontal bar chart
            y_pos = np.arange(len(names))
            colors = plt.cm.RdYlGn_r(np.linspace(0.3, 0.7, len(names)))
            
            bars = ax.barh(y_pos, importances, color=colors)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(names)
            ax.invert_yaxis()  # Highest importance at top
            ax.set_xlabel('Contribution (%)', fontsize=12)
            ax.set_title('Feature Importance for Hemoglobin Prediction', fontsize=14, fontweight='bold')
            ax.set_xlim(0, max(importances) * 1.1)
            
            # Add value labels on bars
            for i, (bar, imp) in enumerate(zip(bars, importances)):
                ax.text(imp + 0.5, i, f'{imp:.1f}%', va='center', fontsize=10)
            
            plt.tight_layout()
            
            # Convert to base64
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig)
            
            logger.info("Feature importance visualization generated")
            return img_base64
            
        except Exception as e:
            logger.error(f"Error generating visualization: {e}")
            return ""


# Global explainer instance
_shap_explainer = None

def get_shap_explainer() -> SHAPExplainer:
    """Get global SHAP explainer instance."""
    global _shap_explainer
    if _shap_explainer is None:
        _shap_explainer = SHAPExplainer()
    return _shap_explainer
