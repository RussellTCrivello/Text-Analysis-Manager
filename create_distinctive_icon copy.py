"""
Premium Application Icon Generator for Text Analysis Manager
Creates a distinctive, high-resolution icon with a unique geometric symbol
Windows-optimized ICO format with proper color depth and alpha handling
"""
from PIL import Image, ImageDraw, ImageFilter
import math
import struct
import io
from pathlib import Path
from typing import Tuple, List


def create_windows_optimized_ico(images: List[Image.Image], output_path: str) -> None:
    """
    Create a Windows-optimized ICO file with proper format handling.
    
    Key optimizations:
    - Sizes <= 48px use BMP format (better Windows compatibility)
    - Sizes > 48px use PNG format (smaller file size)
    - Proper alpha channel handling (non-premultiplied)
    - Correct BITMAPINFOHEADER for BMP entries
    """
    # Sort images by size (smallest first for ICO format)
    sorted_images = sorted(images, key=lambda img: img.size[0])
    
    # Prepare ICO entries
    entries = []
    image_data_list = []
    
    for img in sorted_images:
        size = img.size[0]
        
        # Ensure RGBA format with proper alpha
        img = img.convert('RGBA')
        
        # Clean up alpha channel - ensure pure transparency where alpha is 0
        img = _clean_alpha_channel(img)
        
        if size <= 48:
            # Use BMP format for smaller sizes (better Windows rendering)
            bmp_data = _create_bmp_data(img)
            image_data_list.append(bmp_data)
            
            entries.append({
                'width': size if size < 256 else 0,
                'height': size if size < 256 else 0,
                'colors': 0,
                'reserved': 0,
                'planes': 1,
                'bpp': 32,
                'size': len(bmp_data),
                'is_png': False
            })
        else:
            # Use PNG format for larger sizes
            png_buffer = io.BytesIO()
            img.save(png_buffer, format='PNG', optimize=True)
            png_data = png_buffer.getvalue()
            image_data_list.append(png_data)
            
            entries.append({
                'width': size if size < 256 else 0,
                'height': size if size < 256 else 0,
                'colors': 0,
                'reserved': 0,
                'planes': 1,
                'bpp': 32,
                'size': len(png_data),
                'is_png': True
            })
    
    # Calculate offsets
    header_size = 6  # ICONDIR
    entry_size = 16  # ICONDIRENTRY
    data_offset = header_size + (entry_size * len(entries))
    
    current_offset = data_offset
    for entry in entries:
        entry['offset'] = current_offset
        current_offset += entry['size']
    
    # Write ICO file
    with open(output_path, 'wb') as f:
        # ICONDIR header
        f.write(struct.pack('<HHH', 0, 1, len(entries)))  # Reserved, Type (1=ICO), Count
        
        # ICONDIRENTRY for each image
        for entry in entries:
            f.write(struct.pack('<BBBBHHII',
                entry['width'],
                entry['height'],
                entry['colors'],
                entry['reserved'],
                entry['planes'],
                entry['bpp'],
                entry['size'],
                entry['offset']
            ))
        
        # Image data
        for data in image_data_list:
            f.write(data)


def _clean_alpha_channel(img: Image.Image) -> Image.Image:
    """
    Clean alpha channel to avoid muddy rendering.
    
    Key fixes:
    1. Sets RGB to 0 where alpha is 0 (prevents color bleeding)
    2. Ensures colors are NOT premultiplied (Windows expects straight alpha)
    3. Quantizes very low alpha values to prevent ghosting
    """
    import numpy as np
    
    # Convert to numpy for faster processing
    data = np.array(img, dtype=np.uint8)
    
    # Get alpha channel
    alpha = data[:, :, 3]
    
    # For fully transparent pixels (alpha=0), set RGB to 0
    # This prevents color bleeding in Windows compositing
    transparent_mask = alpha == 0
    data[transparent_mask, 0] = 0  # R
    data[transparent_mask, 1] = 0  # G
    data[transparent_mask, 2] = 0  # B
    
    # For very low alpha (1-10), either make fully transparent or boost alpha
    # This prevents "ghosting" artifacts
    low_alpha_mask = (alpha > 0) & (alpha < 10)
    data[low_alpha_mask, 3] = 0  # Make fully transparent
    data[low_alpha_mask, 0] = 0
    data[low_alpha_mask, 1] = 0
    data[low_alpha_mask, 2] = 0
    
    # For semi-transparent pixels, ensure straight (non-premultiplied) alpha
    # Windows rendering expects non-premultiplied alpha for proper display
    semi_mask = (alpha > 10) & (alpha < 255)
    if np.any(semi_mask):
        # Clamp RGB values to valid range for their alpha
        # This ensures colors don't appear washed out
        for c in range(3):
            channel = data[:, :, c].astype(np.float32)
            # No modification needed for straight alpha, just ensure valid range
            data[:, :, c] = np.clip(channel, 0, 255).astype(np.uint8)
    
    return Image.fromarray(data)


def _create_bmp_data(img: Image.Image) -> bytes:
    """
    Create BMP data for ICO entry (without file header).
    Uses BITMAPINFOHEADER format with proper alpha handling.
    """
    width, height = img.size
    
    # BITMAPINFOHEADER (40 bytes)
    header = struct.pack('<IiiHHIIiiII',
        40,                    # biSize
        width,                 # biWidth
        height * 2,            # biHeight (doubled for AND mask)
        1,                     # biPlanes
        32,                    # biBitCount (32-bit BGRA)
        0,                     # biCompression (BI_RGB)
        0,                     # biSizeImage (can be 0 for BI_RGB)
        0,                     # biXPelsPerMeter
        0,                     # biYPelsPerMeter
        0,                     # biClrUsed
        0                      # biClrImportant
    )
    
    # Pixel data (BGRA format, bottom-up)
    pixel_data = bytearray()
    pixels = img.load()
    
    for y in range(height - 1, -1, -1):  # Bottom-up
        for x in range(width):
            r, g, b, a = pixels[x, y]
            # BGRA order for Windows
            pixel_data.extend([b, g, r, a])
    
    # AND mask (1-bit per pixel, padded to 4-byte boundary)
    # For 32-bit icons, AND mask should be all 0s (fully visible)
    row_bytes = ((width + 31) // 32) * 4
    and_mask = bytes(row_bytes * height)
    
    return header + bytes(pixel_data) + and_mask


class PremiumIconGenerator:
    """Generate a premium, distinctive icon with maximum quality"""
    
    # Ultra-premium color palettes
    PALETTES = {
        'quantum': {
            'primary': (88, 86, 214),       # Deep electric blue
            'secondary': (139, 92, 246),     # Vivid purple
            'accent': (34, 211, 238),        # Bright cyan
            'gold': (251, 191, 36),          # Rich gold
            'dark': (15, 23, 42),            # Deep navy
            'white': (248, 250, 252),        # Off-white
            'glow': (167, 139, 250),         # Purple glow
        },
        'nexus': {
            'primary': (6, 182, 212),        # Cyan
            'secondary': (59, 130, 246),     # Blue
            'accent': (168, 85, 247),        # Purple accent
            'gold': (245, 158, 11),          # Amber
            'dark': (3, 7, 18),              # Almost black
            'white': (241, 245, 249),        # Slate white
            'glow': (103, 232, 249),         # Cyan glow
        },
        'titanium': {
            'primary': (100, 116, 139),      # Slate
            'secondary': (71, 85, 105),      # Dark slate
            'accent': (59, 130, 246),        # Blue accent
            'gold': (251, 191, 36),          # Gold
            'dark': (15, 23, 42),            # Navy
            'white': (248, 250, 252),        # Off-white
            'glow': (148, 163, 184),         # Light slate
        },
    }
    
    def __init__(self, palette: str = 'quantum'):
        """Initialize with a color palette"""
        if palette not in self.PALETTES:
            raise ValueError(f"Palette must be one of: {', '.join(self.PALETTES.keys())}")
        self.colors = self.PALETTES[palette]
        self.palette_name = palette
    
    def create_radial_gradient(self, size: int, color1: Tuple[int, int, int], 
                               color2: Tuple[int, int, int],
                               offset_x: float = 0, offset_y: float = 0) -> Image.Image:
        """Create a radial gradient with optional offset"""
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        center_x = size // 2 + int(offset_x * size)
        center_y = size // 2 + int(offset_y * size)
        max_dist = math.sqrt(size ** 2 + size ** 2)
        
        for y in range(size):
            for x in range(size):
                dist = math.sqrt((x - center_x) ** 2 + (y - center_y) ** 2) / max_dist
                dist = min(1, dist ** 1.2)  # Slightly curved gradient
                
                r = int(color1[0] + (color2[0] - color1[0]) * dist)
                g = int(color1[1] + (color2[1] - color1[1]) * dist)
                b = int(color1[2] + (color2[2] - color1[2]) * dist)
                
                img.putpixel((x, y), (r, g, b, 255))
        
        return img
    
    def draw_research_nexus_symbol(self, draw: ImageDraw.Draw, center_x: int, 
                                   center_y: int, size: int, colors: dict):
        """
        Draw the distinctive 'Research Nexus' symbol - a geometric design
        combining a hexagon (structure), nodes (data), and orbital rings (analysis)
        """
        scale = size / 256  # Base measurements on 256px reference
        
        # Central hexagon representing database structure
        hex_radius = int(45 * scale)
        hex_points = []
        for i in range(6):
            angle = math.radians(60 * i - 30)
            px = center_x + int(hex_radius * math.cos(angle))
            py = center_y + int(hex_radius * math.sin(angle))
            hex_points.append((px, py))
        
        # Draw hexagon with gradient effect (multiple layers)
        line_width = max(2, int(4 * scale))
        
        # Outer glow
        glow_offset = int(3 * scale)
        glow_points = []
        for i in range(6):
            angle = math.radians(60 * i - 30)
            px = center_x + int((hex_radius + glow_offset) * math.cos(angle))
            py = center_y + int((hex_radius + glow_offset) * math.sin(angle))
            glow_points.append((px, py))
        
        for i in range(6):
            next_i = (i + 1) % 6
            draw.line(
                [glow_points[i], glow_points[next_i]],
                fill=colors['glow'] + (100,),
                width=line_width + 4
            )
        
        # Main hexagon
        for i in range(6):
            next_i = (i + 1) % 6
            draw.line(
                [hex_points[i], hex_points[next_i]],
                fill=colors['primary'],
                width=line_width
            )
        
        # Inner hexagon (filled, semi-transparent)
        inner_hex_radius = int(38 * scale)
        inner_points = []
        for i in range(6):
            angle = math.radians(60 * i - 30)
            px = center_x + int(inner_hex_radius * math.cos(angle))
            py = center_y + int(inner_hex_radius * math.sin(angle))
            inner_points.append((px, py))
        
        draw.polygon(inner_points, fill=colors['primary'] + (40,))
        
        # Orbital rings (representing analysis/search)
        orbit_radius_1 = int(65 * scale)
        orbit_radius_2 = int(80 * scale)
        
        ring_width = max(1, int(2 * scale))
        
        # First orbit (partial arc)
        draw.arc(
            [center_x - orbit_radius_1, center_y - orbit_radius_1,
             center_x + orbit_radius_1, center_y + orbit_radius_1],
            start=-45, end=135,
            fill=colors['accent'],
            width=ring_width
        )
        
        # Second orbit (partial arc, opposite side)
        draw.arc(
            [center_x - orbit_radius_2, center_y - orbit_radius_2,
             center_x + orbit_radius_2, center_y + orbit_radius_2],
            start=135, end=315,
            fill=colors['secondary'],
            width=ring_width
        )
        
        # Data nodes at hexagon vertices
        node_radius = max(2, int(6 * scale))
        
        for point in hex_points:
            # Outer glow
            glow_r = node_radius + 2
            draw.ellipse(
                [point[0] - glow_r, point[1] - glow_r,
                 point[0] + glow_r, point[1] + glow_r],
                fill=colors['accent'] + (120,)
            )
            
            # Main node
            draw.ellipse(
                [point[0] - node_radius, point[1] - node_radius,
                 point[0] + node_radius, point[1] + node_radius],
                fill=colors['accent']
            )
            
            # Highlight
            highlight_r = max(1, node_radius // 2)
            highlight_offset = max(1, node_radius // 3)
            draw.ellipse(
                [point[0] - highlight_offset - highlight_r,
                 point[1] - highlight_offset - highlight_r,
                 point[0] - highlight_offset + highlight_r,
                 point[1] - highlight_offset + highlight_r],
                fill=colors['white'] + (180,)
            )
        
        # Central data core
        core_radius = max(3, int(8 * scale))
        
        # Core glow
        for r in range(core_radius + 6, core_radius - 1, -1):
            alpha = int(150 * (1 - (core_radius + 6 - r) / 7))
            draw.ellipse(
                [center_x - r, center_y - r, center_x + r, center_y + r],
                fill=colors['gold'] + (alpha,)
            )
        
        # Core circle
        draw.ellipse(
            [center_x - core_radius, center_y - core_radius,
             center_x + core_radius, center_y + core_radius],
            fill=colors['gold']
        )
        
        # Core highlight
        highlight_r = max(1, core_radius // 2)
        highlight_offset = max(1, core_radius // 3)
        draw.ellipse(
            [center_x - highlight_offset - highlight_r,
             center_y - highlight_offset - highlight_r,
             center_x - highlight_offset + highlight_r,
             center_y - highlight_offset + highlight_r],
            fill=colors['white']
        )
        
        # Connection lines from center to vertices (data flow)
        connection_width = max(1, int(1.5 * scale))
        for i in range(0, 6, 2):  # Every other vertex
            point = hex_points[i]
            # Draw line from center toward vertex (partial)
            dx = point[0] - center_x
            dy = point[1] - center_y
            length_factor = 0.6
            
            end_x = center_x + int(dx * length_factor)
            end_y = center_y + int(dy * length_factor)
            
            draw.line(
                [(center_x, center_y), (end_x, end_y)],
                fill=colors['accent'] + (150,),
                width=connection_width
            )
    
    def create_icon(self, output_path: str = "app_icon.ico", 
                   max_size: int = 512) -> str:
        """Create ultra high-resolution icon"""
        # Extended size range for maximum quality
        sizes = [16, 20, 24, 32, 40, 48, 64, 96, 128, 256, 512]
        # Filter out sizes larger than max_size
        sizes = [s for s in sizes if s <= max_size]
        
        images = []
        
        for size in sizes:
            print(f"  Rendering {size}x{size}...", end=" ")
            
            # Create base with transparent background
            img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            
            # Create sophisticated gradient background
            gradient = self.create_radial_gradient(
                size,
                self.colors['primary'],
                self.colors['dark'],
                offset_x=-0.1,
                offset_y=-0.1
            )
            
            # Create rounded rectangle mask
            padding = max(2, size // 16)
            radius = max(8, size // 6)
            mask = self.draw_rounded_rect_mask(size, padding, radius)
            
            # Apply gradient with mask
            img.paste(gradient, (0, 0), mask)
            
            # Add subtle texture overlay
            if size >= 64:
                texture = self.create_noise_texture(size)
                img = Image.alpha_composite(img, texture)
            
            # Create drawing context
            draw = ImageDraw.Draw(img, 'RGBA')
            center_x = size // 2
            center_y = size // 2
            
            # Draw the distinctive Research Nexus symbol
            self.draw_research_nexus_symbol(draw, center_x, center_y, size, self.colors)
            
            # Add depth effects for larger sizes
            if size >= 64:
                img = self.add_depth_effects(img, size, padding, radius)
            
            # Apply subtle sharpening for crisp edges
            if size >= 48:
                img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=3))
            
            images.append(img)
            print("OK")
        
        # Save as ICO file with Windows-optimized format
        base_path = Path(__file__).parent
        icon_path = base_path / output_path
        
        # Use custom Windows-optimized ICO writer
        # This ensures proper color format and alpha handling
        create_windows_optimized_ico(images, str(icon_path))
        
        print(f"\n[OK] Premium icon created: {icon_path}")
        print(f"    Palette: {self.palette_name}")
        print(f"    Max resolution: {max_size}x{max_size}")
        print(f"    Sizes included: {', '.join(map(str, sizes))}")
        
        return str(icon_path)
    
    def draw_rounded_rect_mask(self, size: int, padding: int, radius: int) -> Image.Image:
        """Create a rounded rectangle mask with anti-aliasing"""
        # Create at 4x resolution for anti-aliasing
        scale = 4
        mask = Image.new('L', (size * scale, size * scale), 0)
        draw = ImageDraw.Draw(mask)
        
        draw.rounded_rectangle(
            [padding * scale, padding * scale,
             size * scale - padding * scale, size * scale - padding * scale],
            radius=radius * scale,
            fill=255
        )
        
        # Downscale with high-quality resampling
        mask = mask.resize((size, size), Image.Resampling.LANCZOS)
        return mask
    
    def create_noise_texture(self, size: int) -> Image.Image:
        """Create subtle noise texture for depth"""
        import random
        
        texture = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        pixels = texture.load()
        
        for y in range(size):
            for x in range(size):
                if random.random() < 0.03:  # Sparse noise
                    alpha = random.randint(5, 15)
                    pixels[x, y] = (255, 255, 255, alpha)
        
        # Blur slightly for softer effect
        texture = texture.filter(ImageFilter.GaussianBlur(radius=0.5))
        return texture
    
    def add_depth_effects(self, img: Image.Image, size: int, 
                         padding: int, radius: int) -> Image.Image:
        """Add sophisticated depth effects"""
        overlay = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay, 'RGBA')
        
        # Subtle inner shadow at top
        shadow_height = size // 10
        for i in range(shadow_height):
            alpha = int(25 * (1 - i / shadow_height) ** 2)
            y = padding + i
            draw.line(
                [(padding + radius // 2, y), (size - padding - radius // 2, y)],
                fill=(0, 0, 0, alpha)
            )
        
        # Subtle highlight at bottom
        highlight_height = size // 12
        for i in range(highlight_height):
            alpha = int(20 * (1 - i / highlight_height) ** 2)
            y = size - padding - 1 - i
            draw.line(
                [(padding + radius // 2, y), (size - padding - radius // 2, y)],
                fill=(255, 255, 255, alpha)
            )
        
        # Edge highlight (left side)
        edge_width = max(1, size // 80)
        for i in range(edge_width):
            alpha = int(30 * (1 - i / edge_width))
            draw.line(
                [(padding + i, padding + radius), 
                 (padding + i, size - padding - radius)],
                fill=(255, 255, 255, alpha)
            )
        
        return Image.alpha_composite(img, overlay)


    def create_uninstall_icon(self, output_path: str = "uninstall_icon.ico",
                             max_size: int = 512) -> str:
        """Create uninstall icon with warning/removal theme"""
        sizes = [16, 20, 24, 32, 40, 48, 64, 96, 128, 256, 512]
        sizes = [s for s in sizes if s <= max_size]
        
        images = []
        
        # Use warning colors
        warning_colors = {
            'primary': (239, 68, 68),        # Red
            'secondary': (220, 38, 38),      # Dark red
            'accent': (251, 191, 36),        # Amber/yellow
            'gold': (245, 158, 11),          # Orange
            'dark': (127, 29, 29),           # Dark red/brown
            'white': (254, 242, 242),        # Light red tint
            'glow': (252, 165, 165),         # Light red glow
        }
        
        for size in sizes:
            print(f"  Rendering uninstall {size}x{size}...", end=" ")
            
            img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            
            # Red gradient background
            gradient = self.create_radial_gradient(
                size,
                warning_colors['primary'],
                warning_colors['dark'],
                offset_x=-0.1,
                offset_y=-0.1
            )
            
            padding = max(2, size // 16)
            radius = max(8, size // 6)
            mask = self.draw_rounded_rect_mask(size, padding, radius)
            
            img.paste(gradient, (0, 0), mask)
            
            draw = ImageDraw.Draw(img, 'RGBA')
            center_x = size // 2
            center_y = size // 2
            
            # Draw X symbol or minus sign for removal
            scale = size / 256
            symbol_size = int(80 * scale)
            line_width = max(3, int(12 * scale))
            
            # Draw X
            offset = symbol_size // 2
            
            # Glow effect
            glow_width = line_width + 6
            draw.line(
                [(center_x - offset, center_y - offset),
                 (center_x + offset, center_y + offset)],
                fill=warning_colors['glow'] + (120,),
                width=glow_width
            )
            draw.line(
                [(center_x + offset, center_y - offset),
                 (center_x - offset, center_y + offset)],
                fill=warning_colors['glow'] + (120,),
                width=glow_width
            )
            
            # Main X
            draw.line(
                [(center_x - offset, center_y - offset),
                 (center_x + offset, center_y + offset)],
                fill=warning_colors['white'],
                width=line_width
            )
            draw.line(
                [(center_x + offset, center_y - offset),
                 (center_x - offset, center_y + offset)],
                fill=warning_colors['white'],
                width=line_width
            )
            
            # Add warning border
            border_width = max(2, int(3 * scale))
            draw.rounded_rectangle(
                [padding, padding, size - padding, size - padding],
                radius=radius,
                outline=warning_colors['accent'] + (200,),
                width=border_width
            )
            
            if size >= 64:
                img = self.add_depth_effects(img, size, padding, radius)
            
            if size >= 48:
                img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=3))
            
            images.append(img)
            print("OK")
        
        base_path = Path(__file__).parent
        icon_path = base_path / output_path
        
        # Use custom Windows-optimized ICO writer
        create_windows_optimized_ico(images, str(icon_path))
        
        print(f"\n[OK] Uninstall icon created: {icon_path}")
        print(f"    Theme: Warning/Removal (Red with X symbol)")
        print(f"    Max resolution: {max_size}x{max_size}")
        
        return str(icon_path)


def main():
    """Generate premium icons"""
    print("=" * 70)
    print("  PREMIUM ICON GENERATOR - Text Analysis Manager")
    print("=" * 70)
    print()
    
    print("Distinctive Symbol: 'Research Nexus'")
    print("  - Hexagonal structure = Database organization")
    print("  - Orbital rings = Analysis & search capabilities")
    print("  - Data nodes = Research connections")
    print("  - Central core = Knowledge hub")
    print()
    
    print("Available palettes:")
    for name, colors in PremiumIconGenerator.PALETTES.items():
        print(f"  - {name}: {colors['primary']} + {colors['accent']}")
    print()
    
    print("Generating icons at maximum quality...")
    print("-" * 70)
    
    # Create main icon with quantum palette
    generator = PremiumIconGenerator(palette='quantum')
    generator.create_icon('app_icon.ico', max_size=512)
    
    print()
    print("Creating palette variants...")
    print("-" * 70)
    
    # Create variants
    for palette in ['nexus', 'titanium']:
        variant_gen = PremiumIconGenerator(palette=palette)
        variant_gen.create_icon(f'app_icon_{palette}.ico', max_size=512)
    
    print()
    print("Creating uninstall icon...")
    print("-" * 70)
    
    # Create uninstall icon
    generator.create_uninstall_icon('uninstall_icon.ico', max_size=512)
    
    print()
    print("-" * 70)
    print("[OK] ALL ICONS GENERATED SUCCESSFULLY!")
    print()
    print("Files created:")
    print("  - app_icon.ico          - Quantum palette (electric blue/purple)")
    print("  - app_icon_nexus.ico    - Nexus palette (cyan/blue)")
    print("  - app_icon_titanium.ico - Titanium palette (slate/blue)")
    print("  - uninstall_icon.ico    - Red warning theme with X symbol")
    print()
    print("Each icon includes sizes: 16, 20, 24, 32, 40, 48, 64, 96, 128, 256, 512px")
    print("=" * 70)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n[X] Error: {e}")
        import traceback
        traceback.print_exc()