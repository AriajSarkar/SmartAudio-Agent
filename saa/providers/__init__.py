"""TTS providers for SAA - Lazy loading to avoid slow scipy imports"""

# Lazy loading to avoid scipy import hang on Windows
__all__ = ["LocalTTSProvider", "ReplicateTTSProvider"]


def __getattr__(name):
    """Lazy load providers to avoid slow scipy imports on Windows"""
    if name == "LocalTTSProvider":
        from saa.providers.local_provider import LocalTTSProvider
        return LocalTTSProvider
    elif name == "ReplicateTTSProvider":
        from saa.providers.replicate_provider import ReplicateTTSProvider
        return ReplicateTTSProvider
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
