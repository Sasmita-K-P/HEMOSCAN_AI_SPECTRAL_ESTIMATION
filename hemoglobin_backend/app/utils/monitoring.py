"""
Prometheus metrics and drift detection for monitoring.
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from typing import Dict, Any
import numpy as np
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


# Metrics
scan_requests_total = Counter(
    'scan_requests_total',
    'Total number of scan requests',
    ['status']
)

scan_duration_seconds = Histogram(
    'scan_duration_seconds',
    'Time spent processing scans',
    ['stage']
)

qc_failures_total = Counter(
    'qc_failures_total',
    'Total number of QC failures',
    ['reason']
)

prediction_uncertainty = Histogram(
    'prediction_uncertainty',
    'Distribution of prediction uncertainties'
)

model_version_info = Gauge(
    'model_version_info',
    'Model version information',
    ['model_type', 'version']
)

feature_drift_score = Gauge(
    'feature_drift_score',
    'Feature distribution drift score',
    ['feature_name']
)


class DriftDetector:
    """
    Monitor feature distributions for dataset drift.
    Uses simple statistical tests against training distribution.
    """
    
    def __init__(self):
        self.baseline_stats: Dict[str, Dict[str, float]] = {}
        self.recent_samples: Dict[str, list] = {}
        self.window_size = 100
    
    def set_baseline(self, feature_name: str, mean: float, std: float):
        """
        Set baseline statistics for a feature.
        
        Args:
            feature_name: Name of the feature
            mean: Training set mean
            std: Training set standard deviation
        """
        self.baseline_stats[feature_name] = {'mean': mean, 'std': std}
        self.recent_samples[feature_name] = []
        logger.info(f"Set baseline for {feature_name}: mean={mean:.3f}, std={std:.3f}")
    
    def update(self, features: Dict[str, float]):
        """
        Update with new feature values and compute drift.
        
        Args:
            features: Dictionary of feature values
        """
        for name, value in features.items():
            if name not in self.baseline_stats:
                continue
            
            # Add to rolling window
            self.recent_samples[name].append(value)
            if len(self.recent_samples[name]) > self.window_size:
                self.recent_samples[name].pop(0)
            
            # Compute drift score (normalized difference in means)
            if len(self.recent_samples[name]) >= 30:  # Minimum samples
                recent_mean = np.mean(self.recent_samples[name])
                baseline_mean = self.baseline_stats[name]['mean']
                baseline_std = self.baseline_stats[name]['std']
                
                drift = abs(recent_mean - baseline_mean) / (baseline_std + 1e-6)
                feature_drift_score.labels(feature_name=name).set(drift)
                
                if drift > 2.0:  # Alert threshold
                    logger.warning(
                        f"Significant drift detected in {name}: "
                        f"baseline={baseline_mean:.3f}, recent={recent_mean:.3f}, "
                        f"drift_score={drift:.3f}"
                    )


# Global drift detector
drift_detector = DriftDetector()


def get_metrics():
    """Return Prometheus metrics in text format."""
    return generate_latest()
