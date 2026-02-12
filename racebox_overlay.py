import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import subprocess

# --- ORIGINAL RESOLUTION (for reference) ---
BASE_WIDTH = 960
BASE_HEIGHT = 720

# --- NEW RESOLUTION ---
WIDTH = BASE_WIDTH*2
HEIGHT = BASE_HEIGHT*2
FPS = 25

# --- scaling factors ---
SCALE_X = WIDTH / BASE_WIDTH
SCALE_Y = HEIGHT / BASE_HEIGHT
SCALE = (SCALE_X + SCALE_Y) / 2  # average scale for sizes

# --- sizes ---
TRACK_PADDING = int(150 * SCALE)
DOT_RADIUS = int(15 * SCALE)
G_METER_RADIUS = int(100 * SCALE)

# font sizes
FONT_SPEED = int(72 * SCALE)
FONT_LABEL = int(28 * SCALE)
FONT_G = int(36 * SCALE)

font_speed = ImageFont.truetype("arial.ttf", FONT_SPEED)
font_label = ImageFont.truetype("arial.ttf", FONT_LABEL)
font_g = ImageFont.truetype("arial.ttf", FONT_G)

def moving_average(data, window=5):
    kernel = np.ones(window) / window
    return np.convolve(data, kernel, mode="same")


def load_csv(path):
    lat = []
    lon = []
    speed = []
    gx = []
    gy = []

    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            if not line or not line[0].isdigit():
                continue

            parts = line.strip().split(",")

            if len(parts) < 8:
                continue

            try:
                lat.append(float(parts[2]))
                lon.append(float(parts[3]))
                speed.append(float(parts[5]))
                gx.append(-float(parts[7]))
                gy.append(float(parts[6]))
            except ValueError:
                continue

    lat = np.array(lat)
    lon = np.array(lon)
    speed = np.array(speed)
    gx = np.array(gx)
    gy = np.array(gy)

    print("Loaded samples:", len(lat))
    print("Lat range:", lat.min(), lat.max())
    print("Lon range:", lon.min(), lon.max())

    return lat, lon, speed, gx, gy


def normalize_track(lat, lon, trim=5, minimap_size=600):
    # discard first/last points
    lat = lat[trim:-trim]
    lon = lon[trim:-trim]

    lat0 = lat.mean()
    lon0 = lon.mean()

    # convert to local meters
    x = (lon - lon0) * 111320 * np.cos(np.radians(lat0))
    y = (lat - lat0) * 110540

    minx, maxx = x.min(), x.max()
    miny, maxy = y.min(), y.max()

    track_w = maxx - minx
    track_h = maxy - miny

    # scale to minimap
    scale = minimap_size / max(track_w, track_h)
    x = (x - minx) * scale
    y = (y - miny) * scale

    # flip Y so north is up
    y = minimap_size - y

    # offset to top-left
    offset_x = int(40 * SCALE)
    offset_y = int(40 * SCALE)
    x += offset_x
    y += offset_y
    y -= minimap_size / 2

    return x.astype(int), y.astype(int)

 



def build_track_layer(tx, ty):
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # skip first point to avoid bad line
    for i in range(1, len(tx)):
        # ignore huge jumps (optional)
        # if abs(tx[i] - tx[i-1]) > 1000 or abs(ty[i] - ty[i-1]) > 1000:
        #     continue

        # Glow: draw thicker semi-transparent line first
        # glow_width = int(2 * SCALE)
        # draw.line(
        #     [(tx[i - 1], ty[i - 1]), (tx[i], ty[i])],
        #     fill=(255, 255, 255, 50),  # low alpha for glow
        #     width=glow_width,
        # )

        # Main track line on top
        draw.line(
            [(tx[i - 1], ty[i - 1]), (tx[i], ty[i])],
            fill=(255, 255, 255, 180),
            width=int(4 * SCALE),
        )

    return img





def draw_g_meter(img, draw, gx_val, gy_val):
    """
    Draw a G-force meter in bottom-right corner.
    gx_val, gy_val: lateral and longitudinal G (in G units)
    """
    # meter position
    x0 = WIDTH - G_METER_RADIUS
    y0 = HEIGHT - int(40 * SCALE) - G_METER_RADIUS

    max_g = 1.5

    # outer circle
    draw.ellipse(
        [x0 - G_METER_RADIUS, y0 - G_METER_RADIUS, x0 + G_METER_RADIUS, y0 + G_METER_RADIUS],
        outline=(255, 255, 255, 255),
        width=int(3 * SCALE)
    )

    # inner circles (0.5G increments)
    for g in [0.5, 1.0, 1.5]:
        r = g / max_g * G_METER_RADIUS
        draw.ellipse(
            [x0 - r, y0 - r, x0 + r, y0 + r],
            outline=(200, 200, 200, 120),
            width=int(1 * SCALE)
        )

    # crosshairs
    draw.line([x0 - G_METER_RADIUS, y0, x0 + G_METER_RADIUS, y0], fill=(255, 255, 255, 255))
    draw.line([x0, y0 - G_METER_RADIUS, x0, y0 + G_METER_RADIUS], fill=(255, 255, 255, 255))

    # G vector
    r = G_METER_RADIUS * np.sqrt(gx_val ** 2 + gy_val ** 2) / max_g
    angle = np.arctan2(-gy_val, gx_val)
    gx_screen = x0 + r * np.cos(angle)
    gy_screen = y0 + r * np.sin(angle)
    dot_size = int(12 * SCALE)
    draw.ellipse(
        [gx_screen - dot_size, gy_screen - dot_size, gx_screen + dot_size, gy_screen + dot_size],
        fill=(255, 0, 0, 255)
    )

    # G magnitude text
    g_mag = np.sqrt(gx_val ** 2 + gy_val ** 2)
    text = f"{g_mag:.2f}G"
    tw, th = draw.textbbox((0,0), text, font=font_g)[2:]
    draw.text((x0 - tw/2, y0 - th/2), text, fill=(255, 255, 255, 150), font=font_g)


def draw_speed_box(img, draw, speed_val):
    box_w = int(260 * SCALE)
    box_h = int(140 * SCALE)
    x = 0
    y = HEIGHT - box_h - int(40 * SCALE)

    # background
    draw.rounded_rectangle(
        [x, y, x + box_w, y + box_h],
        radius=int(20 * SCALE),
        fill=(0, 0, 0, 160),
        outline=(255, 255, 255, 180),
        width=int(3 * SCALE),
    )


    speed_text = f"{int(speed_val)}"
    unit_text = "MPH"

    tw, th = draw.textbbox((0, 0), speed_text, font=font_speed)[2:]
    uw, uh = draw.textbbox((0, 0), unit_text, font=font_label)[2:]

    draw.text(
        (x + (box_w - tw) / 2, y + 20 * SCALE),
        speed_text,
        fill=(255, 255, 255, 255),
        font=font_speed,
    )

    draw.text(
        (x + (box_w - uw) / 2, y + box_h - uh - 15 * SCALE),
        unit_text,
        fill=(200, 200, 200, 255),
        font=font_label,
    )


def main(csv_path, out_dir="frames"):
    lat, lon, speed, gx, gy = load_csv(csv_path)
    tx, ty = normalize_track(lat, lon)
    track_layer = build_track_layer(tx, ty)

    os.makedirs(out_dir, exist_ok=True)


    cmd = [
    "ffmpeg",
    "-y",
    "-f", "rawvideo",        # raw video frames
    "-pixel_format", "rgba", # PIL uses RGBA
    "-video_size", f"{WIDTH}x{HEIGHT}",
    "-framerate", str(FPS),
    "-i", "-",               # read from stdin
    "-c:v", "qtrle",         # codec that supports alpha
    "-pix_fmt", "argb",
    "race_overlay.mov"
    ]
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    for i in range(len(tx)):
        print("Progress: " + str(round(i/len(tx)*100.0)) + "%")
        img = track_layer.copy()
        draw = ImageDraw.Draw(img)

        # Car dot
        cx = tx[i]
        cy = ty[i]

        draw.ellipse(
          [cx - DOT_RADIUS, cy - DOT_RADIUS,
            cx + DOT_RADIUS, cy + DOT_RADIUS],
           fill=(255, 0, 0, 255),
        )


        # Speed box
        draw_speed_box(img, draw, speed[i])

        # G-meter
        draw_g_meter(img, draw, gx[i], gy[i])

        process.stdin.write(img.tobytes())
    
    process.stdin.close()
    process.wait()
    print("Frames written")

    print("Transparent video created:", "race_overlay.mov")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python racebox_overlay.py data.csv")
    else:
        main(sys.argv[1])
