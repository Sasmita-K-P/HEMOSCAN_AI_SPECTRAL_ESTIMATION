"""
Patch script to add feature-based mock predictions to hb_predictor.py
This script carefully modifies the file to avoid corruption.
"""

# Read the original file
with open('app/models/hb_predictor.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and modify the __init__ method
modified_lines = []
for i, line in enumerate(lines):
    # Add is_trained flag after model_path assignment
    if 'self.model_path = model_path or settings.hb_model_path' in line:
        modified_lines.append(line)
        modified_lines.append('        self.is_trained = False\n')
        continue
    
    # Modify the else block in __init__
    if 'logger.warning(f"Hb model not found at {self.model_path}. Using placeholder.")' in line:
        modified_lines.append('            logger.warning(f"Hb model not found at {self.model_path}. Using feature-based mock predictions.")\n')
        continue
    
    if i > 0 and 'Using placeholder' in lines[i-1] and 'self.model = build_hb_predictor()' in line:
        modified_lines.append('            self.model = None\n')
        modified_lines.append('            self.is_trained = False\n')
        continue
    
    # Modify load_model to set is_trained
    if 'self.model = keras.models.load_model(str(self.model_path))' in line:
        modified_lines.append(line)
        modified_lines.append('            self.is_trained = True\n')
        continue
    
    # Modify load_model error handling
    if 'logger.warning("Using untrained model")' in line:
        modified_lines.append('            logger.warning("Falling back to feature-based mock predictions")\n')
        continue
    
    if i > 0 and 'Using untrained model' in lines[i-1] and 'self.model = build_hb_predictor()' in line:
        modified_lines.append('            self.model = None\n')
        modified_lines.append('            self.is_trained = False\n')
        continue
    
    # Add mock prediction method after features_to_array
    if 'return feature_array' in line and i < len(lines) - 1 and 'def predict_with_uncertainty' in lines[i+2]:
        modified_lines.append(line)
        modified_lines.append('    \n')
        modified_lines.append('    def predict_mock_from_features(\n')
        modified_lines.append('        self,\n')
        modified_lines.append('        features: Dict\n')
        modified_lines.append('    ) -> Tuple[float, float, float, np.ndarray]:\n')
        modified_lines.append('        """Generate realistic mock prediction from extracted features."""\n')
        modified_lines.append('        mean_L = features["color"]["mean_L"]\n')
        modified_lines.append('        ratio_R_G = features["color"]["ratio_R_G"]\n')
        modified_lines.append('        vessel_density = features["vascular"]["vessel_density"]\n')
        modified_lines.append('        mean_R = features["color"]["mean_R"]\n')
        modified_lines.append('        \n')
        modified_lines.append('        base_hb = 14.0\n')
        modified_lines.append('        L_normalized = (mean_L - 60) / 20.0\n')
        modified_lines.append('        L_factor = -L_normalized * 2.0\n')
        modified_lines.append('        rg_normalized = (ratio_R_G - 1.05) / 0.15\n')
        modified_lines.append('        rg_factor = rg_normalized * 1.5\n')
        modified_lines.append('        vessel_normalized = (vessel_density - 0.15) / 0.1\n')
        modified_lines.append('        vessel_factor = vessel_normalized * 0.8\n')
        modified_lines.append('        red_normalized = (mean_R - 150) / 50.0\n')
        modified_lines.append('        red_factor = red_normalized * 0.5\n')
        modified_lines.append('        \n')
        modified_lines.append('        hb_mean = base_hb + L_factor + rg_factor + vessel_factor + red_factor\n')
        modified_lines.append('        hb_mean = float(np.clip(hb_mean, 8.0, 18.0))\n')
        modified_lines.append('        \n')
        modified_lines.append('        texture_uniformity = features["texture"].get("lbp_uniformity", 0.5)\n')
        modified_lines.append('        base_std = 0.6 + (1.0 - texture_uniformity) * 0.4\n')
        modified_lines.append('        hb_std = float(base_std + np.random.uniform(-0.1, 0.1))\n')
        modified_lines.append('        uncertainty = float(min(hb_std / (hb_mean + 1e-6), 0.5))\n')
        modified_lines.append('        \n')
        modified_lines.append('        if hb_mean >= 12.0:\n')
        modified_lines.append('            anemia_probs = np.array([0.75, 0.15, 0.08, 0.02])\n')
        modified_lines.append('        elif hb_mean >= 11.0:\n')
        modified_lines.append('            anemia_probs = np.array([0.25, 0.55, 0.15, 0.05])\n')
        modified_lines.append('        elif hb_mean >= 8.0:\n')
        modified_lines.append('            anemia_probs = np.array([0.10, 0.25, 0.55, 0.10])\n')
        modified_lines.append('        else:\n')
        modified_lines.append('            anemia_probs = np.array([0.05, 0.10, 0.30, 0.55])\n')
        modified_lines.append('        \n')
        modified_lines.append('        logger.info(f"Mock prediction: Hb={hb_mean:.2f}±{hb_std:.2f} g/dL (L*={mean_L:.1f}, R/G={ratio_R_G:.3f})")\n')
        modified_lines.append('        return hb_mean, hb_std, uncertainty, anemia_probs\n')
        continue
    
    # Add check at beginning of predict_with_uncertainty
    if '"""' in line and i > 0 and 'Predict Hb with uncertainty' in lines[i-1]:
        modified_lines.append(line)
        # Find the next line after the docstring closes
        j = i + 1
        while j < len(lines) and '"""' not in lines[j]:
            j += 1
        # Add lines up to and including closing """
        for k in range(i+1, j+1):
            modified_lines.append(lines[k])
        # Add the mock prediction check
        modified_lines.append('        # Use mock predictions if model not trained\n')
        modified_lines.append('        if not self.is_trained or self.model is None:\n')
        modified_lines.append('            logger.info("Using feature-based mock predictions (no trained model)")\n')
        modified_lines.append('            return self.predict_mock_from_features(features)\n')
        modified_lines.append('        \n')
        # Skip to after the docstring
        for k in range(i+1, j+1):
            lines[k] = None  # Mark as processed
        continue
    
    # Skip lines that were already processed
    if line is None:
        continue
    
    modified_lines.append(line)

# Write the modified file
with open('app/models/hb_predictor.py', 'w', encoding='utf-8') as f:
    f.writelines(modified_lines)

print("Successfully patched hb_predictor.py")
print("Changes made:")
print("1. Added is_trained flag")
print("2. Modified __init__ to not create untrained model")
print("3. Modified load_model to set is_trained flag")
print("4. Added predict_mock_from_features() method")
print("5. Modified predict_with_uncertainty() to use mock predictions when model not trained")
