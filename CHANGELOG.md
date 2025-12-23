# Changelog

## [2.1.0] - 2024-12-23

### 🎯 Quality Selection Feature

#### Added
- **Quality Selection UI**
  - Users can now choose video quality before download
  - Visual quality selector with grid layout
  - Shows available resolutions (1080p, 720p, 480p, 360p, etc.)
  - Displays estimated filesize for each quality
  - "Best Quality" auto option available

- **New API Endpoint: `/api/formats`**
  - Fetches available video formats/qualities
  - Returns quality options with filesize info
  - Filters and sorts by resolution
  - Groups by unique resolutions

- **Enhanced Download Endpoint**
  - Now accepts `quality` parameter
  - Format selection based on chosen quality
  - Backward compatible (defaults to 'best')

#### Changed
- UI workflow: URL → Check Video → Choose Quality → Download
- Button text: "Download" → "Cek Video"
- Added quality selector panel (hidden by default)
- Improved user feedback during quality check

#### UI/UX Improvements
- Grid layout for quality options
- Visual selection feedback
- Hover effects on quality cards
- Cancel button to reset selection
- Better loading states
- Filesize display in MB

#### Technical Details
- Quality detection from yt-dlp formats
- Client-side quality selection
- Server-side format filtering
- Responsive grid layout (auto-fit)

---

## [2.0.0] - 2024-12-23

### 🎉 Major Update - Anti-403 Enhanced

#### Added
- **Enhanced 403 Bypass System**
  - Multiple player clients (Android, Web) untuk bypass YouTube blocks
  - Auto-retry mechanism dengan exponential backoff (3x retries)
  - Improved HTTP headers dengan Firefox User-Agent terbaru
  - Fragment retry untuk menangani partial download failures
  
- **Better Error Handling**
  - Pesan error yang lebih informatif dan actionable
  - Specific handling untuk 403 errors dengan solusi
  - Auto-cleanup temporary files on error
  
- **New Features**
  - `update_ytdlp.py` script untuk easy update
  - Enhanced video info API dengan uploader dan view count
  - Better file detection (scan tmpdir untuk find merged MP4)
  - Version info di UI
  
- **Documentation**
  - Comprehensive README.md dengan troubleshooting guide
  - Deploy script untuk shared hosting
  - .gitignore file
  - Changelog untuk tracking updates

#### Changed
- Updated `requirements.txt` dengan minimum versions
- Enhanced `app.py` dengan new ydl options
- Improved UI messages dan error feedback
- Better format selection prioritizing H.264 + AAC

#### Fixed
- 403 Forbidden errors dari YouTube
- File not found after merge issues
- Incomplete error messages
- Missing temporary directory cleanup

#### Technical Details
- yt-dlp: >= 2024.12.13 (latest)
- Flask: >= 3.0.0
- Added extractor_args untuk YouTube player_client selection
- Socket timeout: 30s
- Retry strategy: 3 attempts with 2^n second delays

### Migration Guide
1. Update dependencies: `pip install -r requirements.txt`
2. Update yt-dlp: `python update_ytdlp.py`
3. Restart application
4. Test with any YouTube URL

### Breaking Changes
None - Fully backward compatible

---

## [1.0.0] - Initial Release

### Added
- Basic YouTube download functionality
- Flask web interface
- ffmpeg integration
- Video info API
- Basic error handling
