# Troubleshooting Guide

## Common Issues

### "ModuleNotFoundError: No module named 'TTS'"
This usually happens if the Coqui TTS dependency wasn't installed correctly.
**Solution:**
```powershell
pip install TTS==0.22.0
```

### "CUDA out of memory"
Your GPU ran out of VRAM during synthesis.
**Solutions:**
- Reduce `MAX_SEGMENT_LENGTH` in `.env` (try 200).
- Switch to cloud TTS by setting `TTS_PROVIDER=replicate`.

### "FFmpeg not found"
FFmpeg is required for audio merging and MP3 export.
**Solution:**
Install FFmpeg:
```powershell
winget install Gyan.FFmpeg
```
Or download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.

### "Replicate API authentication failed"
**Solution:**
Check your `REPLICATE_API_TOKEN` in `.env`. Ensure it has no extra spaces.

### "Google API Key Invalid"
**Solution:**
Ensure `GOOGLE_API_KEY` is set in `.env` and has access to Gemini models.

## Debugging
You can enable verbose logging by setting `LOG_LEVEL=DEBUG` in `.env`.
Logs are saved to `logs/pipeline.log`.
