"""ADK function tools for SAA"""
from saa.tools.document_tools import (
    extract_text_from_pdf,
    extract_text_from_txt,
    get_document_metadata,
)
from saa.tools.text_tools import (
    clean_text,
    segment_text,
    filter_unwanted_content,
)
from saa.tools.voice_tools import (
    detect_characters,
    assign_voice_profile,
    analyze_text_gender,
)
from saa.tools.tts_tools import (
    synthesize_with_replicate,
    synthesize_with_local,
    synthesize_audio,
    cleanup_tts_resources,
)
from saa.tools.audio_tools import (
    merge_audio_chunks,
    normalize_audio,
    export_audio_format,
    get_audio_info,
)

__all__ = [
    # Document tools
    "extract_text_from_pdf",
    "extract_text_from_txt",
    "get_document_metadata",
    # Text tools
    "clean_text",
    "segment_text",
    "filter_unwanted_content",
    # Voice tools
    "detect_characters",
    "assign_voice_profile",
    "analyze_text_gender",
    # TTS tools
    "synthesize_with_replicate",
    "synthesize_with_local",
    "synthesize_audio",
    "cleanup_tts_resources",
    # Audio tools
    "merge_audio_chunks",
    "normalize_audio",
    "export_audio_format",
    "get_audio_info",
]
