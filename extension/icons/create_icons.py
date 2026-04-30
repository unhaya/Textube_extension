"""Create Textube icons from source image with rounded corners

Usage:
    python create_icons.py [source_image_path]
    # 引数省略時はスクリプトと同じディレクトリの source.png を読む
"""
import os
import sys
from PIL import Image, ImageDraw

def add_rounded_corners(img, radius):
    """Add rounded corners to an image"""
    # Create a mask for rounded corners
    mask = Image.new('L', img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, img.size[0], img.size[1]], radius=radius, fill=255)

    # Apply the mask
    result = Image.new('RGBA', img.size, (0, 0, 0, 0))
    result.paste(img, mask=mask)
    return result

def create_icon(source_img, size):
    """Resize source image and add rounded corners"""
    # Resize with high quality
    resized = source_img.resize((size, size), Image.Resampling.LANCZOS)

    # Convert to RGBA if needed
    if resized.mode != 'RGBA':
        resized = resized.convert('RGBA')

    # Add rounded corners (radius = 20% of size)
    radius = max(size // 5, 2)
    return add_rounded_corners(resized, radius)

script_dir = os.path.dirname(os.path.abspath(__file__))

# 第1引数があればそれを、無ければ同階層の source.png を使用
if len(sys.argv) > 1:
    source_path = sys.argv[1]
else:
    source_path = os.path.join(script_dir, 'source.png')

# Load source image
try:
    source = Image.open(source_path)
    print(f"Loaded source: {source_path}")
except Exception as e:
    print(f"Error loading source: {e}")
    exit(1)

# Create icons
sizes = [16, 48, 128]

for size in sizes:
    img = create_icon(source, size)
    path = os.path.join(script_dir, f'icon{size}.png')
    img.save(path)
    print(f'Created {path}')

print('Done!')
