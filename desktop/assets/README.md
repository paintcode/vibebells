# Vibebells Application Icons

This directory contains the application icons for all platforms.

## Icon Design

The Vibebells icon features:
- **Golden handbell** with black handle on maroon background
- **Sound wave graphics** showing vibration/ringing
- **Professional design** suitable for desktop and web applications

## Source File

- **handbell-icon-full-cropped.png** - Optimally cropped source image
  - This is the source image for all generated icons

## Generated Files

- **icon.ico** - Windows icon (multi-resolution: 16-256px)
- **icon.png** - Linux icon (512x512)
- **icon.iconset/** - macOS icon set (requires `iconutil` to create .icns)
- **icon-256.png** - Medium size for documentation
- **icon-128.png** - Small size for README

## Web Icons (Generated to ../frontend/public/)

- **favicon.ico** - Browser favicon (16, 32, 48px)
- **logo192.png** - PWA icon (192x192)
- **logo512.png** - PWA icon (512x512)

## Regenerating Icons

To regenerate all platform icons from handbell-icon-full-cropped.png:

```bash
cd desktop
npm run generate-icons
```

### macOS ICNS Generation

On macOS, convert the iconset to .icns:

```bash
iconutil -c icns assets/icon.iconset
```

## Icon Specifications

### Windows (.ico)
- Sizes: 16, 24, 32, 48, 64, 128, 256px
- Used in: Title bar, taskbar, installer

### macOS (.icns)  
- Sizes: 16-1024px including @2x Retina versions
- Used in: Dock, Finder, installer

### Linux (.png)
- Size: 512x512px
- Used in: Application launcher, system menus

