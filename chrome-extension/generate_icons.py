#!/usr/bin/env python3
"""
Generate placeholder PNG icons for the Chrome extension.
Requires: pip install pillow
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, filename):
    """Create a simple icon with a bug emoji/symbol"""
    # Create image with dark background
    img = Image.new('RGB', (size, size), color='#0a0e14')
    draw = ImageDraw.Draw(img)
    
    # Draw cyan circle background
    margin = size // 8
    draw.ellipse([margin, margin, size-margin, size-margin], fill='#22d3ee')
    
    # Draw bug shape
    center_x, center_y = size // 2, size // 2
    
    # Body (two circles)
    body_radius = size // 6
    draw.ellipse([center_x - body_radius, center_y - body_radius//2, 
                  center_x + body_radius, center_y + body_radius//2 + body_radius], 
                 fill='#0a0e14')
    draw.ellipse([center_x - body_radius//1.5, center_y - body_radius*1.5, 
                  center_x + body_radius//1.5, center_y - body_radius//2], 
                 fill='#0a0e14')
    
    # Save
    img.save(filename)
    print(f"✅ Created {filename} ({size}x{size})")

def main():
    # Change to icons directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icons_dir = os.path.join(script_dir, 'icons')
    os.makedirs(icons_dir, exist_ok=True)
    
    os.chdir(icons_dir)
    
    # Generate icons
    create_icon(16, 'icon16.png')
    create_icon(48, 'icon48.png')
    create_icon(128, 'icon128.png')
    
    print("\n✅ All icons generated successfully!")
    print("\nGenerated files:")
    for f in ['icon16.png', 'icon48.png', 'icon128.png']:
        size = os.path.getsize(f)
        print(f"  {f}: {size} bytes")

if __name__ == '__main__':
    try:
        main()
    except ImportError:
        print("❌ Error: Pillow not installed")
        print("Install with: pip install pillow")
        print("\nOr use the shell script with: brew install librsvg")
        exit(1)

