"""
Premium Application Icon Generator for Text Analysis Manager
Creates distinctive, high-resolution icons optimized for Windows display
Windows-optimized ICO format with proper color depth and alpha handling
"""
from PIL import Image, ImageDraw, ImageFilter
import math
import struct
import io
from pathlib import Path
from typing import Tuple, List

# Check for NumPy (optional but recommended for best quality)
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


def create_windows_optimized_ico(images: List[Image.Image], output_path: str) -> None:
    """
    Create a Windows-optimized ICO file with proper format handling.
    
    Key optimizations:
    - BMP format for small icons (up to 48px) - better legacy Windows compatibility
    - PNG format for large icons (>48px) - better quality + smaller file size
    - Proper alpha channel handling (non-premultiplied)
    - Clean alpha edges to prevent artifacts
    - BGRA pixel order for Windows native rendering
    - Bottom-up scanlines (BMP standard)
    - Proper AND mask for transparency
    """
    # Sort images by size (smallest first) for proper ICO structure
    sorted_images = sorted(images, key=lambda img: img.size[0])
    
    entries = []
    image_data_list = []
    
    # Threshold: use BMP for small sizes, PNG for large
    BMP_THRESHOLD = 48
    
    for img in sorted_images:
        size = img.size[0]
        
        # Ensure RGBA format with proper alpha
        img = img.convert('RGBA')
        
        # Clean up alpha channel - ensure pure transparency
        img = _clean_alpha_channel(img)
        
        if size <= BMP_THRESHOLD:
            # Use BMP format for small icons (better Windows legacy support)
            image_data = _create_bmp_data(img)
            is_png = False
        else:
            # Use PNG format for large icons (better quality, smaller size)
            png_buffer = io.BytesIO()
            img.save(png_buffer, format='PNG', optimize=True)
            image_data = png_buffer.getvalue()
            is_png = True
        
        image_data_list.append(image_data)
        
        entries.append({
            'width': size if size < 256 else 0,  # 0 means 256 in ICO format
            'height': size if size < 256 else 0,
            'colors': 0,  # 0 for 32-bit images
            'reserved': 0,
            'planes': 1,
            'bpp': 32,
            'size': len(image_data),
            'is_png': is_png
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
        # ICONDIR header: reserved (0), type (1=icon), count
        f.write(struct.pack('<HHH', 0, 1, len(entries)))
        
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
        
        # Image data (BMP or PNG)
        for data in image_data_list:
            f.write(data)


def _clean_alpha_channel(img: Image.Image) -> Image.Image:
    """
    Clean alpha channel to avoid muddy rendering.
    Uses NumPy if available for faster processing, otherwise uses PIL.
    """
    if HAS_NUMPY:
        return _clean_alpha_numpy(img)
    else:
        return _clean_alpha_pil(img)


def _clean_alpha_numpy(img: Image.Image) -> Image.Image:
    """NumPy-based alpha channel cleaning (faster)"""
    import numpy as np
    
    data = np.array(img, dtype=np.uint8)
    alpha = data[:, :, 3]
    
    # For fully transparent pixels, set RGB to 0 (prevents color bleeding)
    transparent_mask = alpha == 0
    data[transparent_mask, :3] = 0
    
    # For very low alpha (1-10), make fully transparent (prevents ghosting)
    low_alpha_mask = (alpha > 0) & (alpha < 10)
    data[low_alpha_mask, :] = 0
    
    return Image.fromarray(data)


def _clean_alpha_pil(img: Image.Image) -> Image.Image:
    """PIL-based alpha channel cleaning (slower but no dependencies)"""
    pixels = img.load()
    width, height = img.size
    
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            
            # Fully transparent: set RGB to 0
            if a == 0:
                pixels[x, y] = (0, 0, 0, 0)
            # Very low alpha: make fully transparent
            elif 0 < a < 10:
                pixels[x, y] = (0, 0, 0, 0)
    
    return img


def _create_bmp_data(img: Image.Image) -> bytes:
    """
    Create BMP data for ICO entry (without file header).
    Uses BITMAPINFOHEADER format with proper alpha handling.
    
    Windows-specific optimizations:
    - BGRA pixel order (Windows native)
    - Bottom-up scanlines (BMP standard)
    - Proper AND mask for transparency
    - Non-premultiplied alpha
    """
    if HAS_NUMPY:
        return _create_bmp_data_numpy(img)
    else:
        return _create_bmp_data_pil(img)


def _create_bmp_data_numpy(img: Image.Image) -> bytes:
    """NumPy-accelerated BMP data creation (much faster for large images)"""
    import numpy as np
    
    width, height = img.size
    
    # BITMAPINFOHEADER (40 bytes)
    header = struct.pack('<IiiHHIIiiII',
        40,                    # biSize
        width,                 # biWidth
        height * 2,            # biHeight (doubled for XOR + AND masks)
        1,                     # biPlanes
        32,                    # biBitCount (32-bit BGRA)
        0,                     # biCompression (BI_RGB = uncompressed)
        0,                     # biSizeImage (can be 0 for BI_RGB)
        0,                     # biXPelsPerMeter
        0,                     # biYPelsPerMeter
        0,                     # biClrUsed
        0                      # biClrImportant
    )
    
    # Convert to numpy array
    data = np.array(img, dtype=np.uint8)
    
    # Flip vertically (BMP is bottom-up)
    data = np.flipud(data)
    
    # Convert RGBA to BGRA (swap R and B channels)
    pixel_data = np.empty_like(data)
    pixel_data[:, :, 0] = data[:, :, 2]  # B <- R
    pixel_data[:, :, 1] = data[:, :, 1]  # G <- G
    pixel_data[:, :, 2] = data[:, :, 0]  # R <- B
    pixel_data[:, :, 3] = data[:, :, 3]  # A <- A
    
    # AND mask: 1-bit mask, 1 = transparent, 0 = opaque
    # For 32-bit icons with alpha, AND mask is typically all zeros
    # but we set transparent pixels to 1 for maximum compatibility
    row_bytes = ((width + 31) // 32) * 4  # Rows padded to 4-byte boundary
    and_mask = bytearray(row_bytes * height)
    
    # Build AND mask from alpha channel (flipped data)
    alpha = data[:, :, 3]
    for y in range(height):
        for x in range(width):
            if alpha[y, x] < 128:  # Mostly transparent
                byte_idx = y * row_bytes + (x // 8)
                bit_idx = 7 - (x % 8)
                and_mask[byte_idx] |= (1 << bit_idx)
    
    return header + pixel_data.tobytes() + bytes(and_mask)


def _create_bmp_data_pil(img: Image.Image) -> bytes:
    """Pure PIL BMP data creation (no NumPy dependency)"""
    width, height = img.size
    
    # BITMAPINFOHEADER (40 bytes)
    header = struct.pack('<IiiHHIIiiII',
        40,                    # biSize
        width,                 # biWidth
        height * 2,            # biHeight (doubled for XOR + AND masks)
        1,                     # biPlanes
        32,                    # biBitCount (32-bit BGRA)
        0,                     # biCompression (BI_RGB = uncompressed)
        0,                     # biSizeImage (can be 0 for BI_RGB)
        0,                     # biXPelsPerMeter
        0,                     # biYPelsPerMeter
        0,                     # biClrUsed
        0                      # biClrImportant
    )
    
    # Pixel data (BGRA format, bottom-up)
    pixel_data = bytearray(width * height * 4)
    pixels = img.load()
    
    idx = 0
    for y in range(height - 1, -1, -1):  # Bottom-up
        for x in range(width):
            r, g, b, a = pixels[x, y]
            # BGRA order for Windows
            pixel_data[idx] = b
            pixel_data[idx + 1] = g
            pixel_data[idx + 2] = r
            pixel_data[idx + 3] = a
            idx += 4
    
    # AND mask: 1-bit mask, rows padded to 4-byte boundary
    row_bytes = ((width + 31) // 32) * 4
    and_mask = bytearray(row_bytes * height)
    
    # Build AND mask from alpha channel
    for y in range(height - 1, -1, -1):  # Bottom-up (same order as pixel data)
        mask_y = height - 1 - y
        for x in range(width):
            _, _, _, a = pixels[x, y]
            if a < 128:  # Mostly transparent
                byte_idx = mask_y * row_bytes + (x // 8)
                bit_idx = 7 - (x % 8)
                and_mask[byte_idx] |= (1 << bit_idx)
    
    return header + bytes(pixel_data) + bytes(and_mask)


class PremiumIconGenerator:
    """Generate premium, distinctive icons with maximum quality"""
    
    PALETTES = {
        'quantum': {
            'primary': (88, 86, 214),
            'secondary': (139, 92, 246),
            'accent': (34, 211, 238),
            'gold': (251, 191, 36),
            'dark': (15, 23, 42),
            'white': (248, 250, 252),
            'glow': (167, 139, 250),
        },
        'nexus': {
            'primary': (6, 182, 212),
            'secondary': (59, 130, 246),
            'accent': (168, 85, 247),
            'gold': (245, 158, 11),
            'dark': (3, 7, 18),
            'white': (241, 245, 249),
            'glow': (103, 232, 249),
        },
        'titanium': {
            'primary': (100, 116, 139),
            'secondary': (71, 85, 105),
            'accent': (59, 130, 246),
            'gold': (251, 191, 36),
            'dark': (15, 23, 42),
            'white': (248, 250, 252),
            'glow': (148, 163, 184),
        },
    }
    
    def __init__(self, palette: str = 'quantum'):
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
                dist = min(1, dist ** 1.2)
                
                r = int(color1[0] + (color2[0] - color1[0]) * dist)
                g = int(color1[1] + (color2[1] - color1[1]) * dist)
                b = int(color1[2] + (color2[2] - color1[2]) * dist)
                
                img.putpixel((x, y), (r, g, b, 255))
        
        return img
    
    def draw_research_nexus_symbol(self, draw: ImageDraw.Draw, center_x: int, 
                                   center_y: int, size: int, colors: dict,
                                   use_glows: bool = True):
        """Draw the distinctive 'Research Nexus' symbol
        
        Args:
            use_glows: If False, skip semi-transparent glow effects (cleaner for small sizes)
        """
        scale = size / 256
        
        # Central hexagon
        hex_radius = int(45 * scale)
        hex_points = []
        for i in range(6):
            angle = math.radians(60 * i - 30)
            px = center_x + int(hex_radius * math.cos(angle))
            py = center_y + int(hex_radius * math.sin(angle))
            hex_points.append((px, py))
        
        line_width = max(2, int(4 * scale))
        
        # Outer glow (only if enabled)
        if use_glows:
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
        
        # Inner hexagon fill (solid for small sizes, semi-transparent for large)
        inner_hex_radius = int(38 * scale)
        inner_points = []
        for i in range(6):
            angle = math.radians(60 * i - 30)
            px = center_x + int(inner_hex_radius * math.cos(angle))
            py = center_y + int(inner_hex_radius * math.sin(angle))
            inner_points.append((px, py))
        
        if use_glows:
            draw.polygon(inner_points, fill=colors['primary'] + (40,))
        else:
            # Use darker solid fill for small sizes
            dark_fill = tuple(max(0, c - 30) for c in colors['primary'])
            draw.polygon(inner_points, fill=dark_fill + (255,))
        
        # Orbital rings
        orbit_radius_1 = int(65 * scale)
        orbit_radius_2 = int(80 * scale)
        ring_width = max(1, int(2 * scale))
        
        draw.arc(
            [center_x - orbit_radius_1, center_y - orbit_radius_1,
             center_x + orbit_radius_1, center_y + orbit_radius_1],
            start=-45, end=135,
            fill=colors['accent'],
            width=ring_width
        )
        
        draw.arc(
            [center_x - orbit_radius_2, center_y - orbit_radius_2,
             center_x + orbit_radius_2, center_y + orbit_radius_2],
            start=135, end=315,
            fill=colors['secondary'],
            width=ring_width
        )
        
        # Data nodes
        node_radius = max(2, int(6 * scale))
        
        for point in hex_points:
            # Glow (only if enabled)
            if use_glows:
                glow_r = node_radius + 2
                draw.ellipse(
                    [point[0] - glow_r, point[1] - glow_r,
                     point[0] + glow_r, point[1] + glow_r],
                    fill=colors['accent'] + (120,)
                )
            
            # Main node (solid)
            draw.ellipse(
                [point[0] - node_radius, point[1] - node_radius,
                 point[0] + node_radius, point[1] + node_radius],
                fill=colors['accent']
            )
            
            # Highlight (solid white for visibility)
            if use_glows:
                highlight_r = max(1, node_radius // 2)
                highlight_offset = max(1, node_radius // 3)
                draw.ellipse(
                    [point[0] - highlight_offset - highlight_r,
                     point[1] - highlight_offset - highlight_r,
                     point[0] - highlight_offset + highlight_r,
                     point[1] - highlight_offset + highlight_r],
                    fill=colors['white']
                )
        
        # Central core
        core_radius = max(3, int(8 * scale))
        
        # Core glow (only if enabled)
        if use_glows:
            for r in range(core_radius + 6, core_radius - 1, -1):
                alpha = int(150 * (1 - (core_radius + 6 - r) / 7))
                draw.ellipse(
                    [center_x - r, center_y - r, center_x + r, center_y + r],
                    fill=colors['gold'] + (alpha,)
                )
        
        # Core (solid)
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
        
        # Connection lines
        connection_width = max(1, int(1.5 * scale))
        for i in range(0, 6, 2):
            point = hex_points[i]
            dx = point[0] - center_x
            dy = point[1] - center_y
            length_factor = 0.6
            
            end_x = center_x + int(dx * length_factor)
            end_y = center_y + int(dy * length_factor)
            
            # Use solid color for connection lines (semi-transparency can cause artifacts)
            line_color = colors['accent'] if use_glows else colors['secondary']
            draw.line(
                [(center_x, center_y), (end_x, end_y)],
                fill=line_color,
                width=connection_width
            )
    
    def create_icon(self, output_path: str = "app_icon.ico", 
                   max_size: int = 512) -> str:
        """Create ultra high-resolution Windows-optimized icon"""
        sizes = [16, 20, 24, 32, 40, 48, 64, 96, 128, 256, 512]
        sizes = [s for s in sizes if s <= max_size]
        
        images = []
        
        for size in sizes:
            print(f"  Rendering {size}x{size}...", end=" ")
            
            # Use supersampling for cleaner anti-aliasing
            # Render at 4x resolution, then scale down
            supersample = 4 if size <= 128 else 2
            render_size = size * supersample
            
            img = Image.new('RGBA', (render_size, render_size), (0, 0, 0, 0))
            
            gradient = self.create_radial_gradient(
                render_size,
                self.colors['primary'],
                self.colors['dark'],
                offset_x=-0.1,
                offset_y=-0.1
            )
            
            padding = max(2, render_size // 16)
            radius = max(8, render_size // 6)
            mask = self.draw_rounded_rect_mask(render_size, padding, radius)
            
            img.paste(gradient, (0, 0), mask)
            
            if render_size >= 256:
                texture = self.create_noise_texture(render_size)
                img = Image.alpha_composite(img, texture)
            
            draw = ImageDraw.Draw(img, 'RGBA')
            center_x = render_size // 2
            center_y = render_size // 2
            
            # Draw symbol with solid colors (no semi-transparent glows for small sizes)
            use_glows = size >= 48
            self.draw_research_nexus_symbol(draw, center_x, center_y, render_size, self.colors, use_glows)
            
            if render_size >= 256:
                img = self.add_depth_effects(img, render_size, padding, radius)
            
            # Scale down with high-quality resampling
            if supersample > 1:
                img = img.resize((size, size), Image.Resampling.LANCZOS)
            
            # Light sharpening for crisp edges
            if size >= 32:
                img = img.filter(ImageFilter.UnsharpMask(radius=0.5, percent=80, threshold=2))
            
            images.append(img)
            print("OK")
        
        base_path = Path(__file__).parent
        icon_path = base_path / output_path
        
        create_windows_optimized_ico(images, str(icon_path))
        
        print(f"\n[OK] Premium icon created: {icon_path}")
        print(f"    Palette: {self.palette_name}")
        print(f"    Max resolution: {max_size}x{max_size}")
        print(f"    Sizes: {', '.join(map(str, sizes))}")
        if HAS_NUMPY:
            print(f"    Alpha optimization: NumPy (fast)")
        else:
            print(f"    Alpha optimization: PIL (install numpy for faster processing)")
        
        return str(icon_path)
    
    def draw_rounded_rect_mask(self, size: int, padding: int, radius: int) -> Image.Image:
        """Create anti-aliased rounded rectangle mask"""
        scale = 4
        mask = Image.new('L', (size * scale, size * scale), 0)
        draw = ImageDraw.Draw(mask)
        
        draw.rounded_rectangle(
            [padding * scale, padding * scale,
             size * scale - padding * scale, size * scale - padding * scale],
            radius=radius * scale,
            fill=255
        )
        
        mask = mask.resize((size, size), Image.Resampling.LANCZOS)
        return mask
    
    def create_noise_texture(self, size: int) -> Image.Image:
        """Create subtle noise texture for depth"""
        import random
        
        texture = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        pixels = texture.load()
        
        for y in range(size):
            for x in range(size):
                if random.random() < 0.03:
                    alpha = random.randint(5, 15)
                    pixels[x, y] = (255, 255, 255, alpha)
        
        texture = texture.filter(ImageFilter.GaussianBlur(radius=0.5))
        return texture
    
    def add_depth_effects(self, img: Image.Image, size: int, 
                         padding: int, radius: int) -> Image.Image:
        """Add sophisticated depth effects"""
        overlay = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay, 'RGBA')
        
        shadow_height = size // 10
        for i in range(shadow_height):
            alpha = int(25 * (1 - i / shadow_height) ** 2)
            y = padding + i
            draw.line(
                [(padding + radius // 2, y), (size - padding - radius // 2, y)],
                fill=(0, 0, 0, alpha)
            )
        
        highlight_height = size // 12
        for i in range(highlight_height):
            alpha = int(20 * (1 - i / highlight_height) ** 2)
            y = size - padding - 1 - i
            draw.line(
                [(padding + radius // 2, y), (size - padding - radius // 2, y)],
                fill=(255, 255, 255, alpha)
            )
        
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
        
        warning_colors = {
            'primary': (239, 68, 68),
            'secondary': (220, 38, 38),
            'accent': (251, 191, 36),
            'gold': (245, 158, 11),
            'dark': (127, 29, 29),
            'white': (254, 242, 242),
            'glow': (252, 165, 165),
        }
        
        for size in sizes:
            print(f"  Rendering uninstall {size}x{size}...", end=" ")
            
            # Use supersampling for cleaner anti-aliasing
            supersample = 4 if size <= 128 else 2
            render_size = size * supersample
            
            img = Image.new('RGBA', (render_size, render_size), (0, 0, 0, 0))
            
            gradient = self.create_radial_gradient(
                render_size,
                warning_colors['primary'],
                warning_colors['dark'],
                offset_x=-0.1,
                offset_y=-0.1
            )
            
            padding = max(2, render_size // 16)
            radius = max(8, render_size // 6)
            mask = self.draw_rounded_rect_mask(render_size, padding, radius)
            
            img.paste(gradient, (0, 0), mask)
            
            draw = ImageDraw.Draw(img, 'RGBA')
            center_x = render_size // 2
            center_y = render_size // 2
            
            scale = render_size / 256
            symbol_size = int(80 * scale)
            line_width = max(3, int(12 * scale))
            x_offset = symbol_size // 2
            
            use_glows = size >= 48
            
            # Glow (only for larger sizes)
            if use_glows:
                glow_width = line_width + 6
                draw.line(
                    [(center_x - x_offset, center_y - x_offset),
                     (center_x + x_offset, center_y + x_offset)],
                    fill=warning_colors['glow'] + (120,),
                    width=glow_width
                )
                draw.line(
                    [(center_x + x_offset, center_y - x_offset),
                     (center_x - x_offset, center_y + x_offset)],
                    fill=warning_colors['glow'] + (120,),
                    width=glow_width
                )
            
            # Main X (solid white)
            draw.line(
                [(center_x - x_offset, center_y - x_offset),
                 (center_x + x_offset, center_y + x_offset)],
                fill=warning_colors['white'],
                width=line_width
            )
            draw.line(
                [(center_x + x_offset, center_y - x_offset),
                 (center_x - x_offset, center_y + x_offset)],
                fill=warning_colors['white'],
                width=line_width
            )
            
            # Border (solid color)
            border_width = max(2, int(3 * scale))
            draw.rounded_rectangle(
                [padding, padding, render_size - padding, render_size - padding],
                radius=radius,
                outline=warning_colors['accent'],
                width=border_width
            )
            
            if render_size >= 256:
                img = self.add_depth_effects(img, render_size, padding, radius)
            
            # Scale down with high-quality resampling
            if supersample > 1:
                img = img.resize((size, size), Image.Resampling.LANCZOS)
            
            # Light sharpening
            if size >= 32:
                img = img.filter(ImageFilter.UnsharpMask(radius=0.5, percent=80, threshold=2))
            
            images.append(img)
            print("OK")
        
        base_path = Path(__file__).parent
        icon_path = base_path / output_path
        
        create_windows_optimized_ico(images, str(icon_path))
        
        print(f"\n[OK] Uninstall icon created: {icon_path}")
        print(f"    Theme: Warning/Removal")
        print(f"    Max resolution: {max_size}x{max_size}")
        
        return str(icon_path)


def main():
    """Generate premium Windows-optimized icons"""
    print("=" * 70)
    print("  PREMIUM ICON GENERATOR - Text Analysis Manager")
    print("  Windows-Optimized Format with Clean Alpha Channels")
    print("=" * 70)
    print()
    
    print("Distinctive Symbol: 'Research Nexus'")
    print("  - Hexagonal structure = Database organization")
    print("  - Orbital rings = Analysis & search")
    print("  - Data nodes = Research connections")
    print("  - Central core = Knowledge hub")
    print()
    
    print("Generating icons...")
    print("-" * 70)
    
    generator = PremiumIconGenerator(palette='quantum')
    generator.create_icon('app_icon.ico', max_size=512)
    
    print()
    print("Creating palette variants...")
    print("-" * 70)
    
    for palette in ['nexus', 'titanium']:
        variant_gen = PremiumIconGenerator(palette=palette)
        variant_gen.create_icon(f'app_icon_{palette}.ico', max_size=512)
    
    print()
    print("Creating uninstall icon...")
    print("-" * 70)
    
    generator.create_uninstall_icon('uninstall_icon.ico', max_size=512)
    
    print()
    print("-" * 70)
    print("[OK] ALL ICONS GENERATED!")
    print()
    print("Files created:")
    print("  - app_icon.ico          - Quantum (blue/purple)")
    print("  - app_icon_nexus.ico    - Nexus (cyan/blue)")
    print("  - app_icon_titanium.ico - Titanium (slate)")
    print("  - uninstall_icon.ico    - Red warning X")
    print()
    print("Features:")
    print("  - Sizes: 16, 20, 24, 32, 40, 48, 64, 96, 128, 256, 512px")
    print("  - Format: BMP (<=48px) + PNG (>48px) for optimal rendering")
    print("  - Alpha: Cleaned & quantized to prevent color bleeding/ghosting")
    print("  - BMP: BGRA pixel order, bottom-up scanlines, proper AND mask")
    print("  - Quality: 4x supersampled anti-aliasing, sharpened edges")
    if HAS_NUMPY:
        print("  - Processing: NumPy-accelerated (fast)")
    else:
        print("  - Processing: Pure PIL (install numpy for 10x speed boost)")
    print("=" * 70)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()