import { AnalysisResult, AnemiaClass } from "../types";
import { generateUUID } from "../utils/uuid";

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Upload and analyze nail bed image using the backend API
 */
export const analyzeNailImage = async (base64Image: string): Promise<AnalysisResult> => {
    try {
        // Convert base64 to blob
        const base64Data = base64Image.split(',')[1];
        const byteCharacters = atob(base64Data);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: 'image/jpeg' });

        // Create form data
        const formData = new FormData();
        formData.append('file', blob, 'nail_image.jpg');

        // Call backend API
        const response = await fetch(`${API_BASE_URL}/api/v1/scan`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const errorData = await response.json();

            // Handle validation errors (including hand detection)
            if (response.status === 400) {
                throw new Error(errorData.detail || 'Validation failed');
            }

            throw new Error(errorData.detail || 'Analysis failed');
        }

        const data = await response.json();

        // Map backend response to frontend AnalysisResult
        return mapBackendToFrontend(data, base64Image);

    } catch (error) {
        console.error('Backend API error:', error);

        // Re-throw validation errors (hand detection, etc.)
        if (error instanceof Error && error.message.includes('hand')) {
            throw error;
        }

        // For other errors, throw generic message
        throw new Error(error instanceof Error ? error.message : 'Failed to analyze image');
    }
};

/**
 * Map backend API response to frontend AnalysisResult format
 */
function mapBackendToFrontend(backendData: any, imageUrl: string): AnalysisResult {
    const prediction = backendData.prediction;

    // Map anemia class
    let anemiaClass: AnemiaClass;
    const anemiaLabel = prediction.anemia_class?.toLowerCase() || 'normal';

    if (anemiaLabel.includes('severe')) {
        anemiaClass = AnemiaClass.SEVERE;
    } else if (anemiaLabel.includes('moderate')) {
        anemiaClass = AnemiaClass.MODERATE;
    } else if (anemiaLabel.includes('mild')) {
        anemiaClass = AnemiaClass.MILD;
    } else {
        anemiaClass = AnemiaClass.NORMAL;
    }

    // Extract top features from explainability
    const topFeatures = backendData.explainability?.top_contributing_features || [];
    const mappedFeatures = topFeatures.slice(0, 3).map((feature: any) => ({
        name: feature.feature_name || feature.name || 'Unknown',
        direction: determineDirection(feature.contribution || 0),
        impact: feature.explanation || `Contribution: ${(feature.contribution || 0).toFixed(3)}`
    }));

    // Calculate confidence from uncertainty (inverse relationship)
    const uncertainty = prediction.uncertainty || 0.1;
    const confidence = Math.max(0.5, Math.min(0.99, 1 - uncertainty));

    return {
        id: backendData.scan_id || generateUUID(),
        timestamp: Date.now(),
        hb_estimate_g_dl: parseFloat((prediction.hb_g_per_dl || 12.0).toFixed(1)),
        hb_ci_95: prediction.hb_ci_95 || [
            parseFloat((prediction.hb_g_per_dl - 0.9).toFixed(1)),
            parseFloat((prediction.hb_g_per_dl + 0.9).toFixed(1))
        ],
        anemia_class: anemiaClass,
        confidence: parseFloat(confidence.toFixed(2)),
        tone_group: backendData.preprocessing?.tone_cluster || 3,
        quality_flags: {
            sharpness_ok: backendData.quality?.sharpness_ok ?? true,
            brightness_ok: backendData.quality?.brightness_ok ?? true,
            glare_detected: backendData.quality?.glare_detected ?? false,
        },
        explanations: {
            top_contributing_features: mappedFeatures.length > 0 ? mappedFeatures : [
                { name: 'R_G_ratio', direction: 'normal', impact: 'Color analysis' },
                { name: 'vascular_density', direction: 'normal', impact: 'Blood vessel analysis' },
                { name: 'texture', direction: 'normal', impact: 'Nail bed texture' }
            ]
        },
        imageUrl
    };
}

/**
 * Determine feature direction from contribution value
 */
function determineDirection(contribution: number): 'low' | 'high' | 'normal' {
    if (contribution < -0.1) return 'low';
    if (contribution > 0.1) return 'high';
    return 'normal';
}

/**
 * Check backend health
 */
export const checkBackendHealth = async (): Promise<boolean> => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/health`);
        return response.ok;
    } catch {
        return false;
    }
};
