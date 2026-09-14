# Fonts Directory

This directory contains fonts used for better printing and display in the application.

## Automatic Download

Run the download script to automatically fetch recommended fonts:

```bash
python fonts/download_fonts.py
```

## Manual Installation

If automatic download fails, you can manually download fonts from:

### Recommended Fonts

1. **Noto Sans** (English/General) - https://fonts.google.com/noto/specimen/Noto+Sans
2. **Noto Sans Arabic** (Arabic support) - https://fonts.google.com/noto/specimen/Noto+Sans+Arabic
3. **Amiri** (Arabic calligraphy) - https://fonts.google.com/specimen/Amiri
4. **Roboto** (Clean UI font) - https://fonts.google.com/specimen/Roboto

### Installation

1. Download the font files (.ttf or .otf)
2. Place them in this `fonts/` directory
3. Restart the application

## Supported Formats

- TrueType Font (.ttf)
- OpenType Font (.otf)

## Usage in Application

The application automatically loads fonts from this directory at startup. Fonts are used for:

- Report generation and printing
- PDF export
- Better RTL (Arabic) text rendering
- Professional document output

## System Fonts

The application will also use system fonts if available:

### Windows
- Segoe UI (default)
- Arial
- Times New Roman
- Tahoma (Arabic support)

### macOS
- SF Pro
- Helvetica
- Times
- Geeza Pro (Arabic support)

### Linux
- DejaVu Sans
- Liberation Sans
- Noto fonts (if installed)
