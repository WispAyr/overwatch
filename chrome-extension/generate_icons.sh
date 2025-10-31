#!/bin/bash

# Generate PNG icons from SVG using ImageMagick or rsvg-convert
# Install with: brew install imagemagick librsvg

cd "$(dirname "$0")/icons"

if command -v rsvg-convert &> /dev/null; then
    echo "Using rsvg-convert to generate icons..."
    rsvg-convert -w 16 -h 16 icon.svg -o icon16.png
    rsvg-convert -w 48 -h 48 icon.svg -o icon48.png
    rsvg-convert -w 128 -h 128 icon.svg -o icon128.png
    echo "✅ Icons generated successfully!"
elif command -v convert &> /dev/null; then
    echo "Using ImageMagick to generate icons..."
    convert -background none -resize 16x16 icon.svg icon16.png
    convert -background none -resize 48x48 icon.svg icon48.png
    convert -background none -resize 128x128 icon.svg icon128.png
    echo "✅ Icons generated successfully!"
else
    echo "❌ Error: Neither rsvg-convert nor ImageMagick found"
    echo "Install with: brew install librsvg  OR  brew install imagemagick"
    echo ""
    echo "Alternatively, create PNG icons manually:"
    echo "  - icon16.png (16x16)"
    echo "  - icon48.png (48x48)"
    echo "  - icon128.png (128x128)"
    exit 1
fi

ls -lh *.png

