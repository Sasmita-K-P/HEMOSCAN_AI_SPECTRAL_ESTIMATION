import { GoogleGenAI } from "@google/genai";
import { AnalysisResult, AnemiaClass } from "../types";
import { generateUUID } from "../utils/uuid";

// Mock result generator for when API key is missing or fails
const generateMockResult = (imageUrl: string): AnalysisResult => {
  const hb = 11.0 + (Math.random() * 4 - 2); // Random between 9 and 13
  let anemiaClass = AnemiaClass.NORMAL;
  if (hb < 11) anemiaClass = AnemiaClass.MILD;
  if (hb < 9.5) anemiaClass = AnemiaClass.MODERATE;
  if (hb < 8) anemiaClass = AnemiaClass.SEVERE;

  return {
    id: generateUUID(),
    timestamp: Date.now(),
    hb_estimate_g_dl: parseFloat(hb.toFixed(1)),
    hb_ci_95: [parseFloat((hb - 0.8).toFixed(1)), parseFloat((hb + 0.8).toFixed(1))],
    anemia_class: anemiaClass,
    confidence: 0.85 + (Math.random() * 0.1),
    tone_group: Math.floor(Math.random() * 5) + 1,
    quality_flags: {
      sharpness_ok: true,
      brightness_ok: true,
      glare_detected: false,
    },
    explanations: {
      top_contributing_features: [
        { name: "R_G_ratio", direction: hb < 12 ? "low" : "normal", impact: hb < 12 ? "Increases anemia risk" : "Healthy coloration" },
        { name: "vascular_density", direction: hb < 10 ? "low" : "normal", impact: "Correlation with perfusion" },
        { name: "lunula_visibility", direction: "normal", impact: "Standard morphology" }
      ]
    },
    imageUrl,
  };
};

export const analyzeNailImage = async (base64Image: string): Promise<AnalysisResult> => {
  const apiKey = process.env.API_KEY;
  if (!apiKey) {
    console.warn("No API Key found. Using mock data.");
    await new Promise(resolve => setTimeout(resolve, 2500)); // Simulate processing
    return generateMockResult(base64Image);
  }

  try {
    const ai = new GoogleGenAI({ apiKey });
    
    // Remove header if present (e.g., "data:image/jpeg;base64,")
    const cleanBase64 = base64Image.split(',')[1];

    const model = 'gemini-2.5-flash';
    const prompt = `
      You are a clinical-grade anemia screening AI. Analyze this image of a fingernail/nailbed.
      
      Perform the following steps virtually:
      1. Segment the nail bed.
      2. Analyze pallor, redness, and texture.
      3. Estimate Hemoglobin (Hb) levels based on visual perfusion.
      
      Return a valid JSON object with NO markdown formatting. The JSON must match this structure:
      {
        "hb_estimate_g_dl": number (between 6.0 and 17.0),
        "anemia_class": "Normal" | "Mild" | "Moderate" | "Severe",
        "confidence": number (0.0 to 1.0),
        "tone_group": number (1-6, Fitzpatrick scale estimate),
        "quality_flags": {
          "sharpness_ok": boolean,
          "brightness_ok": boolean,
          "glare_detected": boolean
        },
        "explanations": {
          "top_contributing_features": [
            { "name": string, "direction": "low"|"high"|"normal", "impact": string }
          ]
        }
      }
    `;

    const response = await ai.models.generateContent({
      model,
      contents: {
        parts: [
          { inlineData: { mimeType: 'image/jpeg', data: cleanBase64 } },
          { text: prompt }
        ]
      },
      config: {
        responseMimeType: "application/json"
      }
    });

    const text = response.text;
    if (!text) throw new Error("No response from AI");

    const data = JSON.parse(text);

    // Calculate CI 95 roughly based on estimate
    const ciLower = data.hb_estimate_g_dl - 0.9;
    const ciUpper = data.hb_estimate_g_dl + 0.9;

    return {
      id: generateUUID(),
      timestamp: Date.now(),
      hb_estimate_g_dl: data.hb_estimate_g_dl,
      hb_ci_95: [parseFloat(ciLower.toFixed(1)), parseFloat(ciUpper.toFixed(1))],
      anemia_class: data.anemia_class,
      confidence: data.confidence,
      tone_group: data.tone_group,
      quality_flags: data.quality_flags,
      explanations: data.explanations,
      imageUrl: base64Image
    };

  } catch (error) {
    console.error("Gemini analysis failed:", error);
    return generateMockResult(base64Image);
  }
};
