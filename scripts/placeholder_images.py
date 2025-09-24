#!/usr/bin/env python3
import re
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Create a simple placeholder image (1x1 transparent PNG)
PLACEHOLDER_DATA = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'

def create_placeholder():
    """Create a 1x1 transparent PNG placeholder"""
    placeholder_path = ROOT / "assets" / "placeholder.png"
    placeholder_path.parent.mkdir(parents=True, exist_ok=True)
    placeholder_path.write_bytes(PLACEHOLDER_DATA)
    return str(placeholder_path.relative_to(ROOT))

def replace_external_images():
    """Replace all external image URLs with local placeholder"""
    placeholder_path = "/" + create_placeholder()
    
    # Pattern to match img tags with external URLs
    img_pattern = re.compile(r'<img([^>]*?)src="([^"]*?)"([^>]*?)>', re.IGNORECASE)
    
    for html_file in ROOT.rglob("*.html"):
        content = html_file.read_text(encoding='utf-8', errors='ignore')
        original_content = content
        
        def replace_img(match):
            attrs_before = match.group(1)
            src = match.group(2)
            attrs_after = match.group(3)
            
            # Check if it's an external URL
            if src.startswith('http://') or src.startswith('https://'):
                return f'<img{attrs_before}src="{placeholder_path}"{attrs_after}>'
            return match.group(0)
        
        content = img_pattern.sub(replace_img, content)
        
        if content != original_content:
            html_file.write_text(content, encoding='utf-8')
            print(f"Updated: {html_file.relative_to(ROOT)}")

if __name__ == "__main__":
    replace_external_images()
    print("All external images replaced with placeholder")
