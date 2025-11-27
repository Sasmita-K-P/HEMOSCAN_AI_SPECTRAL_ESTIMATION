import React from 'react';
import { ArrowLeft, Share2, Info, Activity, Droplets } from 'lucide-react';
import { AnalysisResult, AnemiaClass } from '../types';

interface ResultDetailProps {
    result: AnalysisResult;
    onBack: () => void;
}

const ResultDetail: React.FC<ResultDetailProps> = ({ result, onBack }) => {

    const getStatusColor = (cls: AnemiaClass) => {
        switch (cls) {
            case AnemiaClass.NORMAL: return 'text-green-600 bg-green-50 border-green-200';
            case AnemiaClass.MILD: return 'text-yellow-600 bg-yellow-50 border-yellow-200';
            case AnemiaClass.MODERATE: return 'text-orange-600 bg-orange-50 border-orange-200';
            case AnemiaClass.SEVERE: return 'text-red-600 bg-red-50 border-red-200';
            default: return 'text-slate-600 bg-slate-50 border-slate-200';
        }
    };

    return (
        <div className="pb-8">
            {/* Navbar override within page */}
            <div className="sticky top-0 bg-white border-b border-slate-200 p-4 flex items-center justify-between z-10">
                <button onClick={onBack} className="p-1 rounded-full hover:bg-slate-100">
                    <ArrowLeft className="w-6 h-6 text-slate-700" />
                </button>
                <h2 className="font-bold text-slate-800">Result Detail</h2>
                <button className="p-1 rounded-full hover:bg-slate-100">
                    <Share2 className="w-5 h-5 text-slate-500" />
                </button>
            </div>

            <div className="p-4 space-y-6">

                {/* Main Metric Card */}
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100 text-center relative overflow-hidden">
                    <div className={`absolute top-0 left-0 w-full h-1.5 ${getStatusColor(result.anemia_class).split(' ')[1].replace('bg-', 'bg-')}`}></div>
                    <p className="text-slate-500 text-sm font-medium uppercase tracking-wide mb-1">Estimated Hemoglobin</p>
                    <div className="flex items-center justify-center gap-2 mb-2">
                        <span className="text-5xl font-bold text-slate-900">{result.hb_estimate_g_dl}</span>
                        <span className="text-lg text-slate-400 font-medium mt-4">g/dL</span>
                    </div>

                    <div className={`inline-flex items-center px-4 py-1.5 rounded-full border ${getStatusColor(result.anemia_class)}`}>
                        <span className="font-bold text-sm">{result.anemia_class} Anemia</span>
                    </div>

                    <div className="mt-4 grid grid-cols-2 gap-4 border-t border-slate-100 pt-4">
                        <div className="text-center">
                            <p className="text-[10px] text-slate-400 uppercase">Confidence</p>
                            <p className="font-semibold text-slate-700">{Math.round(result.confidence * 100)}%</p>
                        </div>
                        <div className="text-center border-l border-slate-100">
                            <p className="text-[10px] text-slate-400 uppercase">95% CI</p>
                            <p className="font-semibold text-slate-700">{result.hb_ci_95[0]} - {result.hb_ci_95[1]}</p>
                        </div>
                    </div>
                </div>

                {/* Image Processing Pipeline */}
                <div className="space-y-3">
                    <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2">
                        <Activity className="w-4 h-4 text-teal-600" />
                        Image Processing Pipeline
                    </h3>

                    {/* Before Calibration */}
                    <div className="space-y-1">
                        <p className="text-xs font-semibold text-slate-600">1. Original Image (Before Calibration)</p>
                        <div className="relative rounded-lg overflow-hidden aspect-[4/3] bg-slate-100 border border-slate-200">
                            <img
                                src={result.preprocessing?.original_image_base64 || result.imageUrl}
                                alt="Original Before Calibration"
                                className="w-full h-full object-cover"
                            />
                        </div>
                    </div>

                    {/* After Calibration */}
                    <div className="space-y-1">
                        <p className="text-xs font-semibold text-slate-600">2. After Calibration (Glare Removal & Tone Correction)</p>
                        <div className="relative rounded-lg overflow-hidden aspect-[4/3] bg-slate-100 border border-slate-200">
                            <img
                                src={result.preprocessing?.preprocessed_image_base64 || result.imageUrl}
                                alt="After Calibration"
                                className="w-full h-full object-cover"
                            />
                        </div>
                    </div>

                    {/* ROI with GradCAM */}
                    <div className="space-y-1">
                        <p className="text-xs font-semibold text-slate-600">3. ROI Nail Bed with Heatmap Analysis</p>
                        <div className="relative rounded-lg overflow-hidden aspect-[4/3] bg-slate-900 border border-slate-200">
                            {/* Display GradCAM heatmap on ROI if available, otherwise show ROI only */}
                            {result.explainability?.gradcam_nail_overlay ? (
                                <img
                                    src={result.explainability.gradcam_nail_overlay}
                                    alt="ROI with GradCAM Heatmap"
                                    className="w-full h-full object-cover"
                                />
                            ) : result.segmentation?.roi_image_base64 ? (
                                <img
                                    src={result.segmentation.roi_image_base64}
                                    alt="ROI Nail Bed Only"
                                    className="w-full h-full object-cover"
                                />
                            ) : (
                                <>
                                    <img src={result.imageUrl} alt="Analyzed Nail" className="w-full h-full object-cover opacity-80" />
                                    <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-red-500/20 to-yellow-400/10 mix-blend-overlay"></div>
                                </>
                            )}

                            <div className="absolute bottom-2 right-2 bg-black/60 backdrop-blur-md px-2 py-1 rounded text-[10px] text-white">
                                Tone Group: {result.tone_group} (Calibrated)
                            </div>
                        </div>
                        <p className="text-xs text-slate-500 leading-relaxed">
                            Red areas indicate high vascular contribution for hemoglobin estimation.
                        </p>
                    </div>
                </div>

                {/* Contributing Features */}
                <div className="space-y-3">
                    <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2">
                        <Droplets className="w-4 h-4 text-teal-600" />
                        Why this result?
                    </h3>
                    <div className="bg-white rounded-xl p-4 border border-slate-100 shadow-sm">
                        <div className="flex flex-wrap gap-2">
                            {result.explanations.top_contributing_features.map((feature, idx) => (
                                <div key={idx} className="flex items-center gap-2 bg-slate-50 px-3 py-2 rounded-lg border border-slate-100 w-full">
                                    <div className={`w-2 h-2 rounded-full ${feature.direction === 'low' ? 'bg-orange-400' :
                                        feature.direction === 'high' ? 'bg-blue-400' : 'bg-green-400'
                                        }`}></div>
                                    <div>
                                        <p className="text-xs font-bold text-slate-700 capitalize">{feature.name.replace(/_/g, ' ')}</p>
                                        <p className="text-[10px] text-slate-500">{feature.impact}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Disclaimer */}
                <div className="bg-blue-50 border border-blue-100 p-4 rounded-xl flex gap-3">
                    <Info className="w-5 h-5 text-blue-600 shrink-0" />
                    <p className="text-xs text-blue-800 leading-relaxed">
                        <strong>Screening Tool Only:</strong> This is not a confirmed medical diagnosis. Please consult a doctor and perform a laboratory Complete Blood Count (CBC) test for verification.
                    </p>
                </div>

            </div>
        </div>
    );
};

export default ResultDetail;
