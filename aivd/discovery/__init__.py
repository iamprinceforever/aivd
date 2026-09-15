"""Active Behavioral Discovery (AIVD 3.5).

Finds WHERE to look and amplifies WEAK signals into 3.4 investigations.
Does not replace Explorer, Investigation, Verifier, Memory, or Reward.
"""
from aivd.discovery.cartography import BehavioralMapView, RegionStats
from aivd.discovery.weak_signal import SignalStrength, classify_signal, WeakSignalDetector
from aivd.discovery.discovery_controller import (
    DiscoveryController,
    DiscoveryMode,
    DiscoveryLevel,
)
from aivd.discovery.metrics import summarize_discovery

__all__ = [
    "BehavioralMapView",
    "RegionStats",
    "SignalStrength",
    "classify_signal",
    "WeakSignalDetector",
    "DiscoveryController",
    "DiscoveryMode",
    "DiscoveryLevel",
    "summarize_discovery",
]
