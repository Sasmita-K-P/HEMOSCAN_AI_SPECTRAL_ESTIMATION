import React, { useState, useRef } from 'react';
import { Camera, X, AlertCircle, CheckCircle2, Upload, Loader2 } from 'lucide-react';
import { AnalysisResult } from '../types';
import { analyzeNailImage } from '../services/geminiService';

interface ScanProps {
    onResult: (result: AnalysisResult) => void;
    onCancel: () => void;
}

const Scan: React.FC<ScanProps> = ({ onResult, onCancel }) => {
    const [capturedImage, setCapturedImage] = useState<string | null>(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const videoRef = useRef<HTMLVideoElement>(null);
    const [isCameraActive, setIsCameraActive] = useState(false);

    const startCamera = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'environment' }
            });
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
                setIsCameraActive(true);
            }
        } catch (err) {
            setError('Camera access denied. Please use file upload instead.');
            console.error('Camera error:', err);
        }
    };

    const stopCamera = () => {
        if (videoRef.current && videoRef.current.srcObject) {
            const stream = videoRef.current.srcObject as MediaStream;
            stream.getTracks().forEach(track => track.stop());
            setIsCameraActive(false);
        }
    };

    const capturePhoto = () => {
        if (!videoRef.current) return;

        const canvas = document.createElement('canvas');
        canvas.width = videoRef.current.videoWidth;
        canvas.height = videoRef.current.videoHeight;
        const ctx = canvas.getContext('2d');

        if (ctx) {
            ctx.drawImage(videoRef.current, 0, 0);
            const imageData = canvas.toDataURL('image/jpeg', 0.9);
            setCapturedImage(imageData);
            stopCamera();
        }
    };

    const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        if (!file.type.startsWith('image/')) {
            setError('Please upload a valid image file');
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            const result = e.target?.result as string;
            setCapturedImage(result);
        };
        reader.readAsDataURL(file);
    };

    const handleAnalyze = async () => {
        if (!capturedImage) return;

        setIsProcessing(true);
        setError(null);

        try {
            const result = await analyzeNailImage(capturedImage);
            onResult(result);
        } catch (err) {
            setError('Analysis failed. Please try again.');
            console.error('Analysis error:', err);
        } finally {
            setIsProcessing(false);
        }
    };

    const handleRetake = () => {
        setCapturedImage(null);
        setError(null);
    };

    return (
        <div className="min-h-screen bg-slate-50 pb-20">
            {/* Header */}
            <div className="sticky top-0 bg-white border-b border-slate-200 p-4 flex items-center justify-between z-10">
                <h2 className="font-bold text-slate-800">Scan Nail Bed</h2>
                <button onClick={onCancel} className="p-1 rounded-full hover:bg-slate-100">
                    <X className="w-6 h-6 text-slate-700" />
                </button>
            </div>

            <div className="p-4 space-y-6">
                {/* Instructions */}
                <div className="bg-blue-50 border border-blue-100 p-4 rounded-xl flex gap-3">
                    <AlertCircle className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
                    <div>
                        <h3 className="text-sm font-bold text-blue-800 mb-1">Capture Guidelines</h3>
                        <ul className="text-xs text-blue-700 space-y-1">
                            <li>• Use natural lighting (avoid direct sunlight)</li>
                            <li>• Keep the nail bed in focus</li>
                            <li>• Avoid glare and shadows</li>
                            <li>• Press gently on the nail for best results</li>
                        </ul>
                    </div>
                </div>

                {/* Camera/Image Section */}
                {!capturedImage ? (
                    <div className="space-y-4">
                        {/* Camera View */}
                        {isCameraActive ? (
                            <div className="relative bg-black rounded-2xl overflow-hidden aspect-[3/4]">
                                <video
                                    ref={videoRef}
                                    autoPlay
                                    playsInline
                                    className="w-full h-full object-cover"
                                />
                                <div className="absolute inset-0 border-4 border-white/20 rounded-2xl pointer-events-none">
                                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-48 h-48 border-2 border-teal-400 rounded-full"></div>
                                </div>
                                <button
                                    onClick={capturePhoto}
                                    className="absolute bottom-6 left-1/2 -translate-x-1/2 w-16 h-16 bg-white rounded-full shadow-lg flex items-center justify-center active:scale-95 transition-transform"
                                >
                                    <div className="w-14 h-14 bg-teal-600 rounded-full"></div>
                                </button>
                            </div>
                        ) : (
                            <div className="bg-white rounded-2xl p-8 border border-slate-200 text-center space-y-4">
                                <div className="w-20 h-20 bg-slate-100 rounded-full mx-auto flex items-center justify-center">
                                    <Camera className="w-10 h-10 text-slate-400" />
                                </div>
                                <div>
                                    <h3 className="font-bold text-slate-800 mb-1">Ready to Scan</h3>
                                    <p className="text-sm text-slate-500">Choose how to capture your nail image</p>
                                </div>
                                <div className="space-y-3 pt-2">
                                    <button
                                        onClick={startCamera}
                                        className="w-full bg-teal-600 text-white py-3 rounded-xl font-bold hover:bg-teal-700 transition-colors flex items-center justify-center gap-2"
                                    >
                                        <Camera className="w-5 h-5" />
                                        Open Camera
                                    </button>
                                    <button
                                        onClick={() => fileInputRef.current?.click()}
                                        className="w-full bg-white border-2 border-slate-200 text-slate-700 py-3 rounded-xl font-bold hover:bg-slate-50 transition-colors flex items-center justify-center gap-2"
                                    >
                                        <Upload className="w-5 h-5" />
                                        Upload Image
                                    </button>
                                    <input
                                        ref={fileInputRef}
                                        type="file"
                                        accept="image/*"
                                        onChange={handleFileUpload}
                                        className="hidden"
                                    />
                                </div>
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="space-y-4">
                        {/* Preview */}
                        <div className="relative bg-black rounded-2xl overflow-hidden aspect-[3/4]">
                            <img src={capturedImage} alt="Captured nail" className="w-full h-full object-cover" />
                            <div className="absolute top-4 right-4 bg-green-500 text-white px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1">
                                <CheckCircle2 className="w-3 h-3" />
                                Captured
                            </div>
                        </div>

                        {/* Actions */}
                        <div className="space-y-3">
                            <button
                                onClick={handleAnalyze}
                                disabled={isProcessing}
                                className="w-full bg-teal-600 text-white py-4 rounded-xl font-bold hover:bg-teal-700 transition-colors disabled:bg-slate-300 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                            >
                                {isProcessing ? (
                                    <>
                                        <Loader2 className="w-5 h-5 animate-spin" />
                                        Analyzing...
                                    </>
                                ) : (
                                    'Analyze Image'
                                )}
                            </button>
                            <button
                                onClick={handleRetake}
                                disabled={isProcessing}
                                className="w-full bg-white border-2 border-slate-200 text-slate-700 py-3 rounded-xl font-bold hover:bg-slate-50 transition-colors disabled:opacity-50"
                            >
                                Retake Photo
                            </button>
                        </div>
                    </div>
                )}

                {/* Error Message */}
                {error && (
                    <div className="bg-red-50 border border-red-200 p-4 rounded-xl flex gap-3">
                        <AlertCircle className="w-5 h-5 text-red-600 shrink-0" />
                        <p className="text-sm text-red-700">{error}</p>
                    </div>
                )}

                {/* Quality Checklist */}
                <div className="bg-white rounded-2xl p-5 border border-slate-100">
                    <h3 className="font-bold text-slate-800 text-sm mb-3">Quality Checklist</h3>
                    <div className="space-y-2">
                        {[
                            'Nail bed is clearly visible',
                            'Good lighting without glare',
                            'Image is sharp and in focus',
                            'Nail is pressed gently (not too hard)'
                        ].map((item, idx) => (
                            <div key={idx} className="flex items-center gap-2 text-xs text-slate-600">
                                <div className="w-4 h-4 rounded-full border-2 border-slate-300"></div>
                                {item}
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Scan;
