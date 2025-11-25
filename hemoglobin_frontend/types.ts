
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
