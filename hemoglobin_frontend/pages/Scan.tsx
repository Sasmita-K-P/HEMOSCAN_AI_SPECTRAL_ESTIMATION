import React, { useState, useRef, useEffect } from 'react';
import { Camera, X, AlertCircle, CheckCircle2, Upload, Loader2 } from 'lucide-react';
import { AnalysisResult } from '../types';
import { analyzeNailImage } from '../services/apiService';

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

    useEffect(() => {
        return () => {
            if (videoRef.current && videoRef.current.srcObject) {
                const stream = videoRef.current.srcObject as MediaStream;
                stream.getTracks().forEach(track => track.stop());
            }
        };
    }, []);

    const startCamera = async () => {
        console.log('Starting camera...');
        setError(null);

        try {
            console.log('Requesting camera access...');
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: 'user',
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                }
            });

            console.log('Camera access granted, stream:', stream);

            setIsCameraActive(true);
            console.log('Camera state set to active');

            setTimeout(() => {
                if (videoRef.current) {
                    console.log('Setting video source...');
                    videoRef.current.srcObject = stream;

                    videoRef.current.play()
                        .then(() => console.log('Video playing successfully'))
                        .catch(err => {
                            console.error('Play error:', err);
                            setError('Failed to start video playback');
                        });
                } else {
                    console.error('Video ref is still null after state update');
                    setError('Camera element not ready');
                    setIsCameraActive(false);
                    stream.getTracks().forEach(track => track.stop());
                }
            }, 200);

        } catch (err) {
            console.error('Camera error:', err);
            const errorMsg = err instanceof Error ? err.message : 'Unknown error';
            setError(`Camera failed: ${errorMsg}`);
            setIsCameraActive(false);
        }
    };

    const stopCamera = () => {
        if (videoRef.current && videoRef.current.srcObject) {
            const stream = videoRef.current.srcObject as MediaStream;
            stream.getTracks().forEach(track => track.stop());
            videoRef.current.srcObject = null;
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
            const errorMessage = err instanceof Error ? err.message : 'Analysis failed';
            setError(errorMessage);
            console.error('Analysis error:', err);
        } finally {
            setIsProcessing(false);
        }
    };

    const handleRetake = () => {
        setCapturedImage(null);
        setError(null);
    };

    console.log('Render - isCameraActive:', isCameraActive, 'capturedImage:', !!capturedImage);

    return (
        <div className="min-h-screen bg-slate-50 pb-20">
            {!isCameraActive && (
                <div className="sticky top-0 bg-white border-b border-slate-200 p-4 flex items-center justify-between z-10">
                    <h2 className="font-bold text-slate-800">Scan Nail Bed</h2>
                    <button onClick={onCancel} className="p-1 rounded-full hover:bg-slate-100">
                        <X className="w-6 h-6 text-slate-700" />
                    </button>
                </div>
            )}

            <div className={isCameraActive ? "" : "p-4 space-y-6"}>
                {!isCameraActive && !capturedImage && (
                    <div className="bg-blue-50 border border-blue-100 p-4 rounded-xl flex gap-3">
                        <AlertCircle className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
                        <div>
                            <h3 className="text-sm font-bold text-blue-800 mb-1">Capture Guidelines</h3>
                            <ul className="text-xs text-blue-700 space-y-1">
                                <li>• Use natural lighting</li>
                                <li>• Keep nail bed in focus</li>
                                <li>• Avoid glare and shadows</li>
                                <li>• Press gently on nail</li>
                            </ul>
                        </div>
                    </div>
                )}

                {!capturedImage ? (
                    <div className="space-y-4">
                        {isCameraActive ? (
                            <div className="relative bg-black overflow-hidden h-screen -mx-4 -mt-0">
                                <video
                                    ref={videoRef}
                                    autoPlay
                                    playsInline
                                    muted
                                    className="w-full h-full object-cover"
                                />

                                <div className="absolute inset-0 flex items-center justify-center">
                                    <div className="relative w-80 h-96 border-2 border-white/30 rounded-3xl">
                                        <div className="absolute top-0 left-0 w-8 h-8 border-t-4 border-l-4 border-teal-400 rounded-tl-3xl"></div>
                                        <div className="absolute top-0 right-0 w-8 h-8 border-t-4 border-r-4 border-teal-400 rounded-tr-3xl"></div>
                                        <div className="absolute bottom-0 left-0 w-8 h-8 border-b-4 border-l-4 border-teal-400 rounded-bl-3xl"></div>
                                        <div className="absolute bottom-0 right-0 w-8 h-8 border-b-4 border-r-4 border-teal-400 rounded-br-3xl"></div>

                                        <div className="absolute inset-0 flex items-center justify-center gap-3 px-8">
                                            <div className="w-16 h-48 border-2 border-dashed border-white/40 rounded-full"></div>
                                            <div className="w-16 h-52 border-2 border-dashed border-white/40 rounded-full"></div>
                                            <div className="w-16 h-48 border-2 border-dashed border-white/40 rounded-full"></div>
                                        </div>

                                        <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-teal-400/50"></div>
                                    </div>
                                </div>

                                <button
                                    onClick={stopCamera}
                                    className="absolute top-6 left-6 w-12 h-12 bg-black/50 rounded-full flex items-center justify-center backdrop-blur-sm"
                                >
                                    <X className="w-6 h-6 text-white" />
                                </button>

                                <div className="absolute bottom-32 left-0 right-0 flex justify-center">
                                    <div className="bg-black/70 backdrop-blur-sm px-6 py-3 rounded-full flex items-center gap-2">
                                        <div className="w-6 h-6 border-2 border-teal-400 rounded flex items-center justify-center">
                                            <div className="w-2 h-2 bg-teal-400 rounded-full"></div>
                                        </div>
                                        <span className="text-white text-sm font-medium">Align fingertips in boxes</span>
                                    </div>
                                </div>

                                <div className="absolute bottom-0 left-0 right-0 bg-black/90 backdrop-blur-sm py-8">
                                    <div className="flex items-center justify-center gap-12">
                                        <button
                                            onClick={() => fileInputRef.current?.click()}
                                            className="flex flex-col items-center gap-2"
                                        >
                                            <div className="w-14 h-14 bg-gray-700 rounded-full flex items-center justify-center">
                                                <Upload className="w-6 h-6 text-white" />
                                            </div>
                                            <span className="text-white text-xs">Upload</span>
                                        </button>

                                        <button
                                            onClick={capturePhoto}
                                            className="w-20 h-20 bg-white rounded-full border-4 border-teal-400 flex items-center justify-center active:scale-95 transition-transform shadow-lg shadow-teal-400/50"
                                        >
                                            <div className="w-16 h-16 bg-teal-400 rounded-full"></div>
                                        </button>

                                        <button
                                            onClick={stopCamera}
                                            className="flex flex-col items-center gap-2"
                                        >
                                            <div className="w-14 h-14 bg-gray-700 rounded-full flex items-center justify-center">
                                                <Camera className="w-6 h-6 text-white" />
                                            </div>
                                            <span className="text-white text-xs">Flip</span>
                                        </button>
                                    </div>
                                </div>

                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept="image/*"
                                    onChange={handleFileUpload}
                                    className="hidden"
                                />
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
                        <div className="relative bg-black rounded-2xl overflow-hidden aspect-[3/4]">
                            <img src={capturedImage} alt="Captured nail" className="w-full h-full object-cover" />
                            <div className="absolute top-4 right-4 bg-green-500 text-white px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1">
                                <CheckCircle2 className="w-3 h-3" />
                                Captured
                            </div>
                        </div>

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

                {error && !isCameraActive && (
                    <div className="bg-red-50 border border-red-200 p-4 rounded-xl flex gap-3">
                        <AlertCircle className="w-5 h-5 text-red-600 shrink-0" />
                        <p className="text-sm text-red-700">{error}</p>
                    </div>
                )}

                {!isCameraActive && !capturedImage && (
                    <div className="bg-white rounded-2xl p-5 border border-slate-100">
                        <h3 className="font-bold text-slate-800 text-sm mb-3">Quality Checklist</h3>
                        <div className="space-y-2">
                            {[
                                'Nail bed is clearly visible',
                                'Good lighting without glare',
                                'Image is sharp and in focus',
                                'Nail is pressed gently'
                            ].map((item, idx) => (
                                <div key={idx} className="flex items-center gap-2 text-xs text-slate-600">
                                    <div className="w-4 h-4 rounded-full border-2 border-slate-300"></div>
                                    {item}
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Scan;
