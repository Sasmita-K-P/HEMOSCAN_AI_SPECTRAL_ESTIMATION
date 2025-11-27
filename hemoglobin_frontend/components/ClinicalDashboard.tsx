import React, { useState } from 'react';
import {
    ArrowLeft, Share2, Printer, User, Calendar,
    Activity, FileText, AlertCircle, CheckCircle,
    Info, Droplets
} from 'lucide-react';
import { AnalysisResult, AnemiaClass } from '../types';

interface ClinicalDashboardProps {
    result: AnalysisResult;
    onBack: () => void;
}

const ClinicalDashboard: React.FC<ClinicalDashboardProps> = ({ result, onBack }) => {
    // Mock patient state (in a real app, this would come from context or props)
    const [patient] = useState({
        id: "PT-" + Math.random().toString(36).substr(2, 6).toUpperCase(),
        name: "Anonymous Patient",
        age: 34,
        gender: "Female",
        dob: "1989-05-12"
    });

    const getStatusColor = (cls: AnemiaClass) => {
        switch (cls) {
            case AnemiaClass.NORMAL: return 'text-emerald-700 bg-emerald-50 border-emerald-200';
            case AnemiaClass.MILD: return 'text-amber-700 bg-amber-50 border-amber-200';
            case AnemiaClass.MODERATE: return 'text-orange-700 bg-orange-50 border-orange-200';
            case AnemiaClass.SEVERE: return 'text-red-700 bg-red-50 border-red-200';
            default: return 'text-slate-700 bg-slate-50 border-slate-200';
        }
    };

    const handlePrint = () => {
        window.print();
    };

    // Helper to ensure base64 strings have the correct prefix
    const getBase64Image = (base64String?: string) => {
        if (!base64String) return undefined;
        if (base64String.startsWith('data:')) return base64String;
        return `data:image/png;base64,${base64String}`;
    };

    return (
        <div className="min-h-screen bg-gray-50/50 pb-12 print:bg-white print:pb-0 font-sans text-slate-900">
            {/* Header / Navigation */}
            <div className="bg-white border-b border-slate-200 sticky top-0 z-30 print:hidden shadow-sm backdrop-blur-md bg-white/90">
                <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center h-16">
                        <div className="flex items-center gap-4">
                            <button
                                onClick={onBack}
                                className="p-2 -ml-2 rounded-full hover:bg-slate-100 text-slate-500 hover:text-slate-700 transition-colors"
                                aria-label="Go back"
                            >
                                <ArrowLeft className="w-5 h-5" />
                            </button>
                            <div className="h-6 w-px bg-slate-200 mx-1"></div>
                            <div className="flex items-center gap-2">
                                <Activity className="w-5 h-5 text-teal-600" />
                                <h1 className="text-lg font-bold text-slate-800 tracking-tight">
                                    Clinical Report
                                </h1>
                            </div>
                        </div>
                        <div className="flex items-center gap-3">
                            <button
                                onClick={handlePrint}
                                className="flex items-center gap-2 px-3 py-1.5 bg-white border border-slate-200 rounded-md text-slate-600 hover:bg-slate-50 hover:border-slate-300 font-medium transition-all text-sm shadow-sm"
                            >
                                <Printer className="w-4 h-4" />
                                <span className="hidden sm:inline">Print</span>
                            </button>
                            <button className="flex items-center gap-2 px-3 py-1.5 bg-teal-600 text-white rounded-md hover:bg-teal-700 font-medium transition-all text-sm shadow-sm hover:shadow">
                                <Share2 className="w-4 h-4" />
                                <span className="hidden sm:inline">Share</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8 print:p-0 print:max-w-none space-y-8">

                {/* 1. Patient & Scan Header */}
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 print:shadow-none print:border-none print:mb-4">
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                        <div>
                            <h2 className="text-2xl font-bold text-slate-900 mb-2">{patient.name}</h2>
                            <div className="flex flex-wrap items-center gap-4 text-sm text-slate-500">
                                <span className="flex items-center gap-1.5 bg-slate-50 px-2.5 py-1 rounded-md border border-slate-100">
                                    <User className="w-3.5 h-3.5 text-slate-400" />
                                    <span className="font-mono text-slate-600">{patient.id}</span>
                                </span>
                                <span className="flex items-center gap-1.5">
                                    <Calendar className="w-3.5 h-3.5 text-slate-400" />
                                    {patient.dob} ({patient.age}y)
                                </span>
                                <span className="px-2 py-0.5 bg-slate-100 rounded text-xs font-semibold text-slate-600 uppercase tracking-wider">{patient.gender}</span>
                            </div>
                        </div>
                        <div className="text-left md:text-right">
                            <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold mb-1">Scan Date & Time</p>
                            <p className="font-medium text-slate-900 text-lg">
                                {new Date(result.timestamp).toLocaleDateString()}
                                <span className="text-slate-300 mx-2">·</span>
                                {new Date(result.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </p>
                            <p className="text-xs font-mono text-slate-400 mt-1">ID: {result.id.substring(0, 8)}</p>
                        </div>
                    </div>
                </div>

                {/* 2. Primary Result Card */}
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden print:border print:shadow-none relative">
                    <div className={`absolute top-0 left-0 w-full h-1.5 ${getStatusColor(result.anemia_class).split(' ')[1].replace('bg-', 'bg-')}`}></div>
                    <div className="p-8 text-center">
                        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-6">Estimated Hemoglobin Level</h3>

                        <div className="flex items-baseline justify-center gap-3 mb-8">
                            <span className="text-8xl font-bold text-slate-900 tracking-tighter">{result.hb_estimate_g_dl}</span>
                            <span className="text-2xl text-slate-500 font-medium">g/dL</span>
                        </div>

                        <div className={`inline-flex items-center px-6 py-3 rounded-full border ${getStatusColor(result.anemia_class)} mb-8`}>
                            <Activity className="w-5 h-5 mr-3" />
                            <span className="font-bold text-lg">{result.anemia_class} Anemia</span>
                        </div>

                        <div className="grid grid-cols-2 gap-8 max-w-md mx-auto border-t border-slate-100 pt-8">
                            <div>
                                <p className="text-xs text-slate-400 uppercase font-semibold mb-1">Model Confidence</p>
                                <p className="text-2xl font-semibold text-slate-700">{Math.round(result.confidence * 100)}%</p>
                            </div>
                            <div className="border-l border-slate-100">
                                <p className="text-xs text-slate-400 uppercase font-semibold mb-1">95% Confidence Interval</p>
                                <p className="text-2xl font-semibold text-slate-700">
                                    {typeof result.hb_ci_95[0] === 'number' ? result.hb_ci_95[0].toFixed(1) : result.hb_ci_95[0]} - {typeof result.hb_ci_95[1] === 'number' ? result.hb_ci_95[1].toFixed(1) : result.hb_ci_95[1]}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* 3. Clinical Interpretation */}
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 print:break-inside-avoid">
                    <h3 className="font-bold text-slate-800 flex items-center gap-2 mb-6 text-lg">
                        <FileText className="w-5 h-5 text-teal-600" />
                        Clinical Interpretation
                    </h3>
                    <div className="space-y-4">
                        <div className="p-5 bg-slate-50 rounded-xl border border-slate-100">
                            <p className="font-semibold text-slate-700 mb-2 text-xs uppercase tracking-wide">WHO Classification Criteria</p>
                            <p className="text-slate-700 leading-relaxed text-base">
                                For {patient.gender.toLowerCase()} adults, hemoglobin levels below {patient.gender === 'Male' ? '13.0' : '12.0'} g/dL indicate anemia.
                                This result is classified as <strong className="text-slate-900 bg-white px-2 py-0.5 rounded border border-slate-200 mx-1">{result.anemia_class}</strong>.
                            </p>
                        </div>

                        <div>
                            <p className="font-semibold text-slate-700 mb-3 text-xs uppercase tracking-wide">Recommendation</p>
                            {result.anemia_class === AnemiaClass.NORMAL ? (
                                <div className="flex gap-4 items-start p-4 rounded-xl bg-green-50 border border-green-100">
                                    <CheckCircle className="w-6 h-6 text-green-600 shrink-0 mt-0.5" />
                                    <div>
                                        <p className="font-medium text-green-900">Normal Hemoglobin Levels</p>
                                        <p className="text-green-800 mt-1">Levels are within the normal physiological range. Maintain a balanced diet rich in iron and vitamin C to sustain healthy levels.</p>
                                    </div>
                                </div>
                            ) : (
                                <div className="flex gap-4 items-start p-4 rounded-xl bg-amber-50 border border-amber-100">
                                    <AlertCircle className="w-6 h-6 text-amber-600 shrink-0 mt-0.5" />
                                    <div>
                                        <p className="font-medium text-amber-900">Follow-up Recommended</p>
                                        <p className="text-amber-800 mt-1">
                                            Screening suggests potential anemia. <strong>A confirmatory CBC (Complete Blood Count) test is recommended</strong> to validate these findings. Please consult a healthcare provider for a formal diagnosis.
                                        </p>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* 4. Visual Analysis Pipeline */}
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 print:break-inside-avoid">
                    <h3 className="font-bold text-slate-800 flex items-center gap-2 mb-6 text-lg">
                        <Activity className="w-5 h-5 text-teal-600" />
                        Visual Analysis Pipeline
                    </h3>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                        {/* 1. Original */}
                        <div className="space-y-3 group">
                            <div className="aspect-square rounded-xl overflow-hidden bg-slate-100 border border-slate-200 relative shadow-sm group-hover:shadow-md transition-all">
                                <img
                                    src={getBase64Image(result.preprocessing?.original_image_base64) || result.imageUrl}
                                    alt="Original"
                                    className="w-full h-full object-cover"
                                />
                                <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                                <span className="absolute bottom-2 left-2 bg-black/70 text-white text-[10px] font-bold px-2 py-1 rounded backdrop-blur-md">RAW</span>
                            </div>
                            <p className="text-xs font-medium text-slate-500 text-center uppercase tracking-wide">Raw Capture</p>
                        </div>

                        {/* 2. Preprocessed */}
                        <div className="space-y-3 group">
                            <div className="aspect-square rounded-xl overflow-hidden bg-slate-100 border border-slate-200 relative shadow-sm group-hover:shadow-md transition-all">
                                <img
                                    src={getBase64Image(result.preprocessing?.preprocessed_image_base64) || result.imageUrl}
                                    alt="Preprocessed"
                                    className="w-full h-full object-cover"
                                />
                                <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                                <span className="absolute bottom-2 left-2 bg-teal-600/90 text-white text-[10px] font-bold px-2 py-1 rounded backdrop-blur-md">ENHANCED</span>
                            </div>
                            <p className="text-xs font-medium text-slate-500 text-center uppercase tracking-wide">Glare & Tone Corrected</p>
                        </div>

                        {/* 3. ROI Analysis */}
                        <div className="space-y-3 group">
                            <div className="aspect-square rounded-xl overflow-hidden bg-slate-900 border border-slate-200 relative shadow-sm group-hover:shadow-md transition-all">
                                {result.explainability?.gradcam_nail_overlay ? (
                                    <img
                                        src={getBase64Image(result.explainability.gradcam_nail_overlay)}
                                        alt="GradCAM"
                                        className="w-full h-full object-cover opacity-90 group-hover:opacity-100 transition-opacity"
                                    />
                                ) : (
                                    <div className="w-full h-full flex items-center justify-center text-slate-500 text-xs">No Visualization</div>
                                )}
                                <span className="absolute bottom-2 left-2 bg-indigo-600/90 text-white text-[10px] font-bold px-2 py-1 rounded backdrop-blur-md">GRAD-CAM</span>
                            </div>
                            <p className="text-xs font-medium text-slate-500 text-center uppercase tracking-wide">Heatmap Analysis</p>
                        </div>
                    </div>

                    <div className="mt-6 p-4 bg-slate-50 text-slate-600 text-sm rounded-xl border border-slate-100 flex gap-3 items-start">
                        <Info className="w-5 h-5 shrink-0 text-slate-400 mt-0.5" />
                        <p className="leading-relaxed">
                            <strong className="text-slate-900">GradCAM Interpretation:</strong> Red regions indicate areas of high vascular density and blood volume that most strongly influenced the hemoglobin prediction. Blue regions had less impact.
                        </p>
                    </div>
                </div>

                {/* 5. Feature Contribution Analysis (SHAP) */}
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 print:break-inside-avoid">
                    <h3 className="font-bold text-slate-800 flex items-center gap-2 mb-6 text-lg">
                        <Droplets className="w-5 h-5 text-teal-600" />
                        Feature Contribution Analysis (SHAP)
                    </h3>

                    <div className="flex flex-col gap-8">
                        <div>
                            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Top Contributing Features</h4>
                            <div className="space-y-4">
                                {result.explainability?.top_features?.slice(0, 5).map((feature, idx) => (
                                    <div key={idx} className="group">
                                        <div className="flex justify-between text-sm mb-2">
                                            <span className="font-medium text-slate-700 group-hover:text-teal-700 transition-colors">{feature.name}</span>
                                            <span className="font-mono font-medium text-slate-600">{feature.contribution.toFixed(1)}%</span>
                                        </div>
                                        <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                                            <div
                                                className={`h-full rounded-full ${idx === 0 ? 'bg-teal-600' : 'bg-teal-400'} transition-all duration-500 ease-out`}
                                                style={{ width: `${Math.min(feature.contribution, 100)}%` }}
                                            ></div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="bg-slate-50 rounded-xl p-6 border border-slate-100">
                            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Analysis Summary</h4>
                            <p className="text-sm text-slate-600 leading-relaxed mb-6">
                                {result.explainability?.interpretation || "The model analyzed spectral features including color intensity, vascular patterns, and texture to estimate hemoglobin levels."}
                            </p>

                            {result.explainability?.feature_importance_plot ? (
                                <div className="bg-white p-2 rounded-lg border border-slate-200 shadow-sm">
                                    <img
                                        src={getBase64Image(result.explainability.feature_importance_plot)}
                                        alt="SHAP Plot"
                                        className="w-full rounded"
                                    />
                                </div>
                            ) : (
                                <div className="text-center py-8 bg-white rounded-lg border border-dashed border-slate-300">
                                    <p className="text-xs text-slate-400">Visualization not available</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* 6. Quality Metrics */}
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 print:break-inside-avoid">
                    <h3 className="font-bold text-slate-800 flex items-center gap-2 mb-6 text-lg">
                        <Info className="w-5 h-5 text-teal-600" />
                        Scan Quality Metrics
                    </h3>
                    <div className="space-y-4">
                        <div className="flex items-center justify-between p-4 rounded-xl bg-slate-50 border border-slate-100">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-white rounded-lg border border-slate-200 text-slate-500">
                                    <Activity className="w-4 h-4" />
                                </div>
                                <span className="font-medium text-slate-700">Image Sharpness</span>
                            </div>
                            {result.quality_flags.sharpness_ok ?
                                <span className="text-sm font-bold text-emerald-700 bg-emerald-100 px-3 py-1 rounded-full">Pass</span> :
                                <span className="text-sm font-bold text-red-700 bg-red-100 px-3 py-1 rounded-full">Fail</span>
                            }
                        </div>

                        <div className="flex items-center justify-between p-4 rounded-xl bg-slate-50 border border-slate-100">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-white rounded-lg border border-slate-200 text-slate-500">
                                    <Info className="w-4 h-4" />
                                </div>
                                <span className="font-medium text-slate-700">Lighting Condition</span>
                            </div>
                            {result.quality_flags.brightness_ok ?
                                <span className="text-sm font-bold text-emerald-700 bg-emerald-100 px-3 py-1 rounded-full">Optimal</span> :
                                <span className="text-sm font-bold text-amber-700 bg-amber-100 px-3 py-1 rounded-full">Suboptimal</span>
                            }
                        </div>

                        <div className="flex items-center justify-between p-4 rounded-xl bg-slate-50 border border-slate-100">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-white rounded-lg border border-slate-200 text-slate-500">
                                    <AlertCircle className="w-4 h-4" />
                                </div>
                                <span className="font-medium text-slate-700">Glare Detection</span>
                            </div>
                            {result.quality_flags.glare_detected ?
                                <span className="text-sm font-bold text-amber-700 bg-amber-100 px-3 py-1 rounded-full">Corrected</span> :
                                <span className="text-sm font-bold text-emerald-700 bg-emerald-100 px-3 py-1 rounded-full">Clean</span>
                            }
                        </div>

                        <div className="flex items-center justify-between p-4 rounded-xl bg-slate-50 border border-slate-100">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-white rounded-lg border border-slate-200 text-slate-500">
                                    <User className="w-4 h-4" />
                                </div>
                                <span className="font-medium text-slate-700">Skin Tone Classification</span>
                            </div>
                            <span className="text-sm font-bold text-slate-700 bg-white border border-slate-200 px-3 py-1 rounded-full">Type {result.tone_group}</span>
                        </div>
                    </div>
                </div>

                {/* Footer Disclaimer */}
                <div className="mt-12 text-center border-t border-slate-200 pt-8 print:mt-4 print:pt-4 pb-8">
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">HemoScan AI Analysis System</p>
                    <p className="text-xs text-slate-500 max-w-2xl mx-auto leading-relaxed">
                        This report is generated by an AI screening tool and is not a confirmed medical diagnosis.
                        Results should be verified with standard laboratory tests (CBC).
                        The system uses spectral analysis and deep learning to estimate hemoglobin levels from nail bed images.
                    </p>
                </div>

            </main>
        </div>
    );
};

export default ClinicalDashboard;
