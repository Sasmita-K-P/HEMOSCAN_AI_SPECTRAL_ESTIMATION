
export enum AnemiaClass {
  NORMAL = 'Normal',
  MILD = 'Mild',
  MODERATE = 'Moderate',
  SEVERE = 'Severe'
}

export interface ExplanationFeature {
  name: string;
  direction: 'low' | 'high' | 'normal';
  impact: string;
}

export interface QualityFlags {
  sharpness_ok: boolean;
  brightness_ok: boolean;
  glare_detected: boolean;
}

export interface AnalysisResult {
  id: string;
  timestamp: number;
  hb_estimate_g_dl: number;
  hb_ci_95: [number, number];
  anemia_class: AnemiaClass;
  confidence: number;
  tone_group: number;
  quality_flags: QualityFlags;
  explanations: {
    top_contributing_features: ExplanationFeature[];
  };
  explainability?: {
    gradcam_nail_overlay?: string;
    top_features?: Array<{
      name: string;
      value: number;
      importance: number;
      contribution: number;
    }>;
    feature_importance_plot?: string;
    interpretation?: string;
    method?: string;
  };
  preprocessing?: {
    tone_cluster?: number;
    original_image_base64?: string;
    preprocessed_image_base64?: string;
  };
  segmentation?: {
    roi_image_base64?: string;
  };
  imageUrl: string; // Data URL
}

export interface User {
  id: string;
  email: string;
  password?: string; // Note: In a real backend, this would be hashed.
  age: number;
  gender: 'Male' | 'Female' | 'Other';
  termsAccepted: boolean;
  createdAt: number;
  shareData?: boolean;
}

export type ViewState = 'HOME' | 'SCAN' | 'HISTORY' | 'RESULT' | 'PROFILE';
