import os
import math
import random
import numpy as np
from PIL import Image, ImageOps, ImageFilter, ImageEnhance

# Set seeds for reproducibility
random.seed(42)
np.random.seed(42)

def generate_banner(is_dark=True):
    theme_name = "dark" if is_dark else "light"
    
    # 1. Colors
    if is_dark:
        bg_col = "#0A101F"
        card_bg = "#070D18"
        border_col = "#1E293B"
        chrome_col = "#22D3EE"
        chrome_dim = "#0E7490"
        accent_col = "#10B981"
        portrait_col = "#A78BFA"
        lbl_col = "#94A3B8"
        val_col = "#F8FAFC"
        dots_lead_col = "#1E293B"
        pill_bg = "#1E1B4B"
        pill_stroke = "#6366F1"
        pill_txt = "#A78BFA"
        frame_box_stroke = "#1E293B"
        frame_header_bg = "#0F172A"
    else:
        bg_col = "#F8FAFC"
        card_bg = "#FFFFFF"
        border_col = "#CBD5E1"
        chrome_col = "#0891B2"
        chrome_dim = "#0284C7"
        accent_col = "#059669"
        portrait_col = "#7C3AED"
        lbl_col = "#64748B"
        val_col = "#0F172A"
        dots_lead_col = "#E2E8F0"
        pill_bg = "#EEF2FF"
        pill_stroke = "#818CF8"
        pill_txt = "#4F46E5"
        frame_box_stroke = "#CBD5E1"
        frame_header_bg = "#F1F5F9"

    # 2. Image Processing
    img = Image.open('portrait.jpg').convert('RGB')
    w, h = img.size
    target_w, target_h = 300, 340
    target_aspect = target_w / float(target_h)
    
    crop_w = w
    crop_h = int(w / target_aspect)
    if crop_h > h:
        crop_h = h
        crop_w = int(h * target_aspect)
        
    left = (w - crop_w) // 2
    top = 0
    cropped = img.crop((left, top, left + crop_w, top + crop_h))
    resized = cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)
    
    auto = ImageOps.autocontrast(resized, cutoff=1)
    sharp = auto.filter(ImageFilter.UnsharpMask(radius=3, percent=140))
    contrast_img = ImageEnhance.Contrast(sharp).enhance(1.3)
    
    gray = np.array(contrast_img.convert('L'), dtype=np.float32)
    
    # Masking
    mask = gray > 18
    mask_img = Image.fromarray((mask * 255).astype(np.uint8))
    mask_img = mask_img.filter(ImageFilter.MaxFilter(size=5)).filter(ImageFilter.MinFilter(size=5))
    clean_mask = np.array(mask_img) > 128
    
    # Dithering
    if is_dark:
        f_arr = gray.copy()
    else:
        f_arr = np.zeros_like(gray)
        f_arr[clean_mask] = 255.0 - gray[clean_mask]
        
    dithered = np.zeros((target_h, target_w), dtype=np.uint8)
    
    for y in range(target_h):
        if y % 2 == 0:
            x_range = range(target_w)
            direction = 1
        else:
            x_range = range(target_w - 1, -1, -1)
            direction = -1
            
        for x in x_range:
            if not clean_mask[y, x]:
                f_arr[y, x] = 0
                continue
            old_val = f_arr[y, x]
            new_val = 255 if old_val >= 128 else 0
            dithered[y, x] = 1 if new_val == 255 else 0
            err = old_val - new_val
            
            if direction == 1:
                if x + 1 < target_w and clean_mask[y, x + 1]:
                    f_arr[y, x + 1] += err * (7.0 / 16.0)
                if y + 1 < target_h:
                    if x - 1 >= 0 and clean_mask[y + 1, x - 1]:
                        f_arr[y + 1, x - 1] += err * (3.0 / 16.0)
                    if clean_mask[y + 1, x]:
                        f_arr[y + 1, x] += err * (5.0 / 16.0)
                    if x + 1 < target_w and clean_mask[y + 1, x + 1]:
                        f_arr[y + 1, x + 1] += err * (1.0 / 16.0)
            else:
                if x - 1 >= 0 and clean_mask[y, x - 1]:
                    f_arr[y, x - 1] += err * (7.0 / 16.0)
                if y + 1 < target_h:
                    if x + 1 < target_w and clean_mask[y + 1, x + 1]:
                        f_arr[y + 1, x + 1] += err * (3.0 / 16.0)
                    if clean_mask[y + 1, x]:
                        f_arr[y + 1, x] += err * (5.0 / 16.0)
                    if x - 1 >= 0 and clean_mask[y + 1, x - 1]:
                        f_arr[y + 1, x - 1] += err * (1.0 / 16.0)
                        
    # Extract dots coordinates
    # Grid placement in frame:
    # Frame starts at x=35, y=55, width=410, height=525.
    # Centered portrait: width 330, height 374 (scale = 1.1)
    grid_scale = 1.15
    grid_ox = 35 + (410 - target_w * grid_scale) / 2.0
    grid_oy = 110.0
    
    portrait_dots = []
    for y in range(target_h):
        for x in range(target_w):
            if dithered[y, x] == 1:
                px = grid_ox + x * grid_scale
                py = grid_oy + y * grid_scale
                portrait_dots.append((px, py, x, y))
                
    total_dots = len(portrait_dots)
    print(f"[{theme_name}] Extracted {total_dots} portrait dots")
    
    # 3. Logo Generation (~900 dots each)
    xc = grid_ox + (target_w * grid_scale) / 2.0
    yc = grid_oy + (target_h * grid_scale) / 2.0
    N_TRAV = 900
    
    # Logo 1: Python Logo
    # Draw two snakes / loops
    py_pts = []
    # Snake 1 (upper-left loop with head pointing right)
    for phi in np.linspace(0.2, 2*np.pi - 0.2, 380):
        r = 60 + 15 * np.cos(2*phi)
        py_pts.append((xc - 15 + r * np.cos(phi), yc - 15 + r * np.sin(phi)))
    # Eye 1
    for phi in np.linspace(0, 2*np.pi, 30):
        py_pts.append((xc - 25 + 6*np.cos(phi), yc - 45 + 6*np.sin(phi)))
    # Snake 2 (lower-right loop with head pointing left)
    for phi in np.linspace(0.2, 2*np.pi - 0.2, 380):
        r = 60 + 15 * np.cos(2*phi)
        py_pts.append((xc + 15 - r * np.cos(phi), yc + 15 - r * np.sin(phi)))
    # Eye 2
    for phi in np.linspace(0, 2*np.pi, 30):
        py_pts.append((xc + 25 + 6*np.cos(phi), yc + 45 + 6*np.sin(phi)))
    # Pad or trim to N_TRAV
    while len(py_pts) < N_TRAV:
        py_pts.append(py_pts[len(py_pts) % 50])
    pts_logo1 = np.array(py_pts[:N_TRAV])

    # Logo 2: React Logo
    react_pts = []
    # center nucleus
    for phi in np.linspace(0, 2*np.pi, 180, endpoint=False):
        react_pts.append((xc + 22*np.cos(phi), yc + 22*np.sin(phi)))
    for angle in [0, np.pi/3, 2*np.pi/3]:
        for phi in np.linspace(0, 2*np.pi, 240, endpoint=False):
            ex = 85 * np.cos(phi)
            ey = 32 * np.sin(phi)
            rx = ex * np.cos(angle) - ey * np.sin(angle) + xc
            ry = ex * np.sin(angle) + ey * np.cos(angle) + yc
            react_pts.append((rx, ry))
    pts_logo2 = np.array(react_pts[:N_TRAV])

    # Logo 3: Code Terminal Glyph `</>`
    code_pts = []
    # Left chevron `<` (apex at left)
    for s in np.linspace(0, 1, 260):
        code_pts.append((xc - 40 - 35 * s, yc - 50 * (1 - s)))
        code_pts.append((xc - 40 - 35 * s, yc + 50 * (1 - s)))
    # Slash `/`
    for s in np.linspace(-1, 1, 200):
        code_pts.append((xc + 22 * s, yc - 65 * s))
    # Right chevron `>` (apex at right)
    for s in np.linspace(0, 1, 260):
        code_pts.append((xc + 40 + 35 * s, yc - 50 * (1 - s)))
        code_pts.append((xc + 40 + 35 * s, yc + 50 * (1 - s)))
    while len(code_pts) < N_TRAV:
        code_pts.append(code_pts[len(code_pts) % 50])
    pts_logo3 = np.array(code_pts[:N_TRAV])

    # Optimal Transport / Nearest neighbor matching between logos
    def match_pts(p_from, p_to):
        avail = np.ones(len(p_to), dtype=bool)
        matched = np.zeros_like(p_to)
        # Sort spatially
        center = np.mean(p_from, axis=0)
        angles = np.arctan2(p_from[:, 1] - center[1], p_from[:, 0] - center[0])
        for idx in np.argsort(angles):
            pt = p_from[idx]
            dists = np.sum((p_to - pt)**2, axis=1)
            dists[~avail] = 1e9
            best = np.argmin(dists)
            matched[idx] = p_to[best]
            avail[best] = False
        return matched

    matched_logo2 = match_pts(pts_logo1, pts_logo2)
    matched_logo3 = match_pts(matched_logo2, pts_logo3)
    matched_logo1_return = match_pts(matched_logo3, pts_logo1)

    # 4. Grouping Portrait Dots into ~94 Drift Bands (with per-dot noise sigma ~4)
    N_BANDS = 94
    # Compute dot angle from center + noise
    p_arr = np.array([(p[0], p[1]) for p in portrait_dots])
    dx = p_arr[:, 0] - xc
    dy = p_arr[:, 1] - yc
    noise = np.random.normal(0, 4.0, size=len(p_arr))
    r_dist = np.sqrt(dx**2 + dy**2) + noise
    
    # Quantize into N_BANDS
    percentiles = np.linspace(0, 100, N_BANDS + 1)
    thresholds = np.percentile(r_dist, percentiles)
    band_indices = np.digitize(r_dist, thresholds[:-1]) - 1
    band_indices = np.clip(band_indices, 0, N_BANDS - 1)

    # Intro groupings: 60 interleaved random groups
    intro_groups = np.random.randint(0, 60, size=len(portrait_dots))

    # 5. Build SVG
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1180 610" width="100%" height="100%">')
    svg.append('<defs>')
    svg.append('''
        <style><![CDATA[
            @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&display=swap');
            text { font-family: 'Fira Code', 'Cascadia Code', 'Consolas', monospace; }
            .chrome { fill: ''' + chrome_col + '''; }
            .accent { fill: ''' + accent_col + '''; }
            .lbl { fill: ''' + lbl_col + '''; font-size: 13.5px; font-weight: 500; }
            .val { fill: ''' + val_col + '''; font-size: 13.5px; font-weight: 600; }
            .dots-line { stroke: ''' + dots_lead_col + '''; stroke-dasharray: 2 4; stroke-width: 1.2; }
            .crisp { shape-rendering: crispEdges; }
        ]]></style>
    ''')
    svg.append('</defs>')

    # Outer canvas background
    svg.append(f'<rect width="1180" height="610" rx="12" fill="{bg_col}" stroke="{border_col}" stroke-width="1.5" />')

    # Window Topbar
    svg.append(f'<rect x="0" y="0" width="1180" height="42" rx="12" fill="{card_bg}" />')
    svg.append(f'<path d="M 0,32 L 0,42 L 1180,42 L 1180,32 Z" fill="{card_bg}" />') # square bottom corners of topbar
    svg.append(f'<line x1="0" y1="42" x2="1180" y2="42" stroke="{border_col}" stroke-width="1" />')

    # Terminal buttons
    svg.append(f'<circle cx="28" cy="21" r="5.5" fill="#EF4444" />')
    svg.append(f'<circle cx="48" cy="21" r="5.5" fill="#F59E0B" />')
    svg.append(f'<circle cx="68" cy="21" r="5.5" fill="#10B981" />')

    # Title
    svg.append(f'<text x="96" y="26" fill="{lbl_col}" font-size="12.5" font-weight="600">profile.sh <tspan fill="{chrome_col}">--live</tspan></text>')
    svg.append(f'<text x="1152" y="26" text-anchor="end" fill="{lbl_col}" font-size="11.5">v2.4.0</text>')

    # Left Frame (VISUAL.MAP)
    svg.append(f'<rect x="30" y="55" width="410" height="525" rx="8" fill="{card_bg}" stroke="{frame_box_stroke}" stroke-width="1.2" />')
    # Frame Header
    svg.append(f'<rect x="30" y="55" width="410" height="34" rx="8" fill="{frame_header_bg}" />')
    svg.append(f'<path d="M 30,81 L 30,89 L 440,89 L 440,81 Z" fill="{frame_header_bg}" />')
    svg.append(f'<line x1="30" y1="89" x2="440" y2="89" stroke="{frame_box_stroke}" stroke-width="1" />')
    svg.append(f'<text x="45" y="77" fill="{chrome_col}" font-size="12" font-weight="700">┌─ VISUAL.MAP</text>')
    svg.append(f'<text x="425" y="77" text-anchor="end" fill="{lbl_col}" font-size="10.5">300×340 · DITHER</text>')

    # Left Frame Footer Info
    svg.append(f'<line x1="30" y1="545" x2="440" y2="545" stroke="{frame_box_stroke}" stroke-width="1" />')
    svg.append(f'<text x="45" y="563" fill="{lbl_col}" font-size="10">STATUS: ACTIVE // MORPH: SMIL 14.2s</text>')
    svg.append(f'<text x="425" y="563" text-anchor="end" fill="{accent_col}" font-size="10">ONLINE</text>')

    # Right Frame (SYSTEM.INFO)
    svg.append(f'<rect x="455" y="55" width="695" height="525" rx="8" fill="{card_bg}" stroke="{frame_box_stroke}" stroke-width="1.2" />')
    
    # Right Header
    svg.append(f'<rect x="455" y="55" width="695" height="34" rx="8" fill="{frame_header_bg}" />')
    svg.append(f'<path d="M 455,81 L 455,89 L 1150,89 L 1150,81 Z" fill="{frame_header_bg}" />')
    svg.append(f'<line x1="455" y1="89" x2="1150" y2="89" stroke="{frame_box_stroke}" stroke-width="1" />')
    svg.append(f'<text x="475" y="77" fill="{chrome_col}" font-size="12" font-weight="700">SYSTEM.INFO</text>')

    # Live pulse badge
    svg.append(f'<circle cx="955" cy="72" r="4.5" fill="#EF4444">')
    svg.append(f'  <animate attributeName="opacity" values="1;0.2;1" dur="1.8s" repeatCount="indefinite" />')
    svg.append(f'</circle>')
    svg.append(f'<text x="966" y="76" fill="#EF4444" font-size="11" font-weight="700">LIVE</text>')

    # Handle pill
    svg.append(f'<rect x="1015" y="60" width="120" height="23" rx="11.5" fill="{pill_bg}" stroke="{pill_stroke}" stroke-width="1" />')
    svg.append(f'<text x="1075" y="76" text-anchor="middle" fill="{pill_txt}" font-size="11.5" font-weight="600">@skartik06</text>')

    # Right Frame Rows
    rows_data = [
        ("Subject", "Kartik Sharma"),
        ("Role", "AI/ML & Full-Stack Systems Dev"),
        ("Origin", "Ajmer, Rajasthan, India"),
        ("Education", "B.Tech IT · GEC Ajmer (Expected 2028)"),
        ("Status", "Building + Learning + Shipping"),
        ("ToolChain", "VS Code, Git, Docker, Linux, Tauri v2"),
        None, # Divider
        ("Core.Lang", "Python, TypeScript, Rust, SQL"),
        ("Core.Frontend", "React, TypeScript, Tailwind, shadcn-ui"),
        ("Core.Backend", "FastAPI, Node.js, Tauri IPC, REST"),
        ("Core.Database", "SQLite, FAISS, Vector Databases"),
        ("Core.Infra", "PyTorch, LangChain, CI/CD, Vite"),
        None, # Divider
        ("Grid.Mail", "sharmakartik7274@gmail.com"),
        ("Grid.LinkedIn", "in/kartik-sharma-4b4b75333"),
        ("Grid.Instagram", "@krrish.diez10"),
        ("Grid.GitHub", "github.com/skartik06"),
        ("Grid.Portfolio", "skartik06/kartik-portfolio"),
    ]

    import html
    y_cur = 114
    for r in rows_data:
        if r is None:
            # Separator line
            svg.append(f'<line x1="475" y1="{y_cur - 8}" x2="1130" y2="{y_cur - 8}" stroke="{dots_lead_col}" stroke-width="1" stroke-dasharray="3 3" opacity="0.6"/>')
            y_cur += 12
            continue
            
        label, val = r
        lbl_x = 475
        val_x = 1130
        
        # Approximate widths for dotted leader start/end
        lbl_w = len(label) * 8.2 + 8
        val_w = len(val) * 8.2 + 8
        lead_x1 = lbl_x + lbl_w
        lead_x2 = val_x - val_w
        if lead_x2 > lead_x1 + 10:
            svg.append(f'<line x1="{lead_x1:.1f}" y1="{y_cur - 4}" x2="{lead_x2:.1f}" y2="{y_cur - 4}" class="dots-line" />')
            
        svg.append(f'<text x="{lbl_x}" y="{y_cur}" class="lbl">{html.escape(label)}</text>')
        svg.append(f'<text x="{val_x}" y="{y_cur}" text-anchor="end" class="val">{html.escape(val)}</text>')
        
        y_cur += 23

    # 6. Render Portrait Dots Layer with Intro Shimmer + Loop Drift Bands
    # Total loop: 14.2s (portrait 3.0s, each logo 2.0s, 1.3s transitions)
    # keyTimes: 0; 0.211; 0.303; 0.444; 0.535; 0.676; 0.768; 0.908; 1
    # Portrait visibility:
    # 0 -> 0.211 (0-3.0s): opacity 1, translate 0
    # 0.211 -> 0.303 (3.0-4.3s): fade out 1 -> 0, drift ~42%
    # 0.303 -> 0.908: opacity 0
    # 0.908 -> 1.0 (12.9-14.2s): fade in 0 -> 1, return to 0
    
    # Pre-render path runs for portrait by bands to keep SVG file size very compact
    # Group dots by band
    bands_dict = {}
    for i, (px, py, x, y) in enumerate(portrait_dots):
        b_idx = band_indices[i]
        if b_idx not in bands_dict:
            bands_dict[b_idx] = []
        bands_dict[b_idx].append((px, py, x, y, intro_groups[i]))
        
    svg.append(f'<!-- PORTRAIT DRIFT BANDS (TOTAL: {N_BANDS}) -->')
    svg.append(f'<g id="portrait-layer" fill="{portrait_col}" class="crisp">')
    
    # Render each band as a <path>
    for b_idx in range(N_BANDS):
        dots_in_band = bands_dict.get(b_idx, [])
        if not dots_in_band:
            continue
            
        # Compute drift vector for this band: translates ~42% toward logo centroid (xc, yc)
        b_mean_x = np.mean([d[0] for d in dots_in_band])
        b_mean_y = np.mean([d[1] for d in dots_in_band])
        # Drift toward xc, yc
        drift_dx = (xc - b_mean_x) * 0.42
        drift_dy = (yc - b_mean_y) * 0.42
        
        # Build path data for dots in this band (each dot is a 1.2 x 1.2 rect)
        d_str_parts = []
        for (px, py, x, y, ig) in dots_in_band:
            d_str_parts.append(f"M{px:.1f},{py:.1f}h1.2v1.2h-1.2Z")
        d_str = "".join(d_str_parts)
        
        svg.append(f'<path d="{d_str}">')
        # Intro shimmer: 60 interleaved groups fade in over ~2s
        avg_intro = np.mean([d[4] for d in dots_in_band])
        delay = (avg_intro / 60.0) * 1.8
        
        # Loop animation (repeat indefinitely after intro)
        svg.append(f'  <animateTransform attributeName="transform" type="translate"')
        svg.append(f'    values="0,0; 0,0; {drift_dx:.1f},{drift_dy:.1f}; {drift_dx:.1f},{drift_dy:.1f}; {drift_dx:.1f},{drift_dy:.1f}; {drift_dx:.1f},{drift_dy:.1f}; {drift_dx:.1f},{drift_dy:.1f}; 0,0; 0,0"')
        svg.append(f'    keyTimes="0; 0.211; 0.303; 0.444; 0.535; 0.676; 0.768; 0.908; 1"')
        svg.append(f'    dur="14.2s" repeatCount="indefinite" />')
        
        svg.append(f'  <animate attributeName="opacity"')
        svg.append(f'    values="1; 1; 0; 0; 0; 0; 0; 1; 1"')
        svg.append(f'    keyTimes="0; 0.211; 0.303; 0.444; 0.535; 0.676; 0.768; 0.908; 1"')
        svg.append(f'    dur="14.2s" repeatCount="indefinite" />')
        svg.append(f'</path>')
        
    svg.append('</g>')

    # 7. Travellers Layer (~900 dots morphing across Logo 1 -> Logo 2 -> Logo 3)
    # Opacity keyframes: 0 during portrait, 1 during logos:
    # 0 (t=0s): 0
    # 0.211 (t=3.0s): 0
    # 0.303 (t=4.3s): 1 (Logo 1 Python)
    # 0.444 (t=6.3s): 1 (Logo 1 hold end)
    # 0.535 (t=7.6s): 1 (Logo 2 React)
    # 0.676 (t=9.6s): 1 (Logo 2 hold end)
    # 0.768 (t=10.9s): 1 (Logo 3 Code </>)
    # 0.908 (t=12.9s): 1 (Logo 3 hold end)
    # 1.0 (t=14.2s): 0 (fade back to portrait)
    svg.append(f'<!-- TRAVELLERS LAYER (900 DOTS MORPHING LOGOS) -->')
    svg.append(f'<g id="travellers-layer" fill="{chrome_col}" class="crisp">')
    
    # We can render the travellers in batch or individual dots with animate motion
    # Since 900 dots have coordinate paths:
    # To keep SVG size lean and blazing fast, group travellers into 15 batches or render path d animations
    # In SVG SMIL, animate attributeName="d" interpolates path shapes directly!
    # Let's create 3 path shape strings: d_l1, d_l2, d_l3!
    # Because every path has EXACTLY N_TRAV rects in identical order, SMIL interpolates path `d` attribute seamlessly!
    
    d_l1_parts = [f"M{p[0]:.1f},{p[1]:.1f}h1.8v1.8h-1.8Z" for p in pts_logo1]
    d_l2_parts = [f"M{p[0]:.1f},{p[1]:.1f}h1.8v1.8h-1.8Z" for p in matched_logo2]
    d_l3_parts = [f"M{p[0]:.1f},{p[1]:.1f}h1.8v1.8h-1.8Z" for p in matched_logo3]
    
    d1 = "".join(d_l1_parts)
    d2 = "".join(d_l2_parts)
    d3 = "".join(d_l3_parts)
    
    svg.append(f'<path d="{d1}">')
    svg.append(f'  <animate attributeName="d"')
    svg.append(f'    values="{d1}; {d1}; {d1}; {d1}; {d2}; {d2}; {d3}; {d3}; {d1}"')
    svg.append(f'    keyTimes="0; 0.211; 0.303; 0.444; 0.535; 0.676; 0.768; 0.908; 1"')
    svg.append(f'    dur="14.2s" repeatCount="indefinite" />')
    
    svg.append(f'  <animate attributeName="opacity"')
    svg.append(f'    values="0; 0; 1; 1; 1; 1; 1; 1; 0"')
    svg.append(f'    keyTimes="0; 0.211; 0.303; 0.444; 0.535; 0.676; 0.768; 0.908; 1"')
    svg.append(f'    dur="14.2s" repeatCount="indefinite" />')
    svg.append(f'</path>')
    svg.append('</g>')

    svg.append('</svg>')
    
    out_svg = "\n".join(svg)
    filename = f"{theme_name}.svg"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(out_svg)
        
    size_kb = len(out_svg.encode('utf-8')) / 1024.0
    print(f"Generated {filename}: {size_kb:.1f} KB")

if __name__ == '__main__':
    generate_banner(is_dark=True)
    generate_banner(is_dark=False)
