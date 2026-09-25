"""
Script generador de assets oficiales para SmartBreak.
Genera icon.ico, icon.png, spin_up.png, spin_down.png y combo_down.png.
"""

import os
from PIL import Image, ImageDraw


def generate_all_assets(output_dir: str = "."):
    os.makedirs(output_dir, exist_ok=True)
    
    # -------------------------------------------------------------
    # 1. Iconos de la Aplicación (icon.png e icon.ico)
    # -------------------------------------------------------------
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    padding = 12
    draw.ellipse(
        [padding, padding, size - padding, size - padding],
        fill=(0, 230, 150, 255),
        outline=(255, 255, 255, 230),
        width=8
    )

    inner_pad = 28
    draw.ellipse(
        [inner_pad, inner_pad, size - inner_pad, size - inner_pad],
        fill=(13, 15, 23, 255),
        outline=(0, 180, 216, 180),
        width=4
    )

    head_r = 18
    head_cx = size // 2
    head_cy = 90
    draw.ellipse(
        [head_cx - head_r, head_cy - head_r, head_cx + head_r, head_cy + head_r],
        fill=(255, 255, 255, 255)
    )

    draw.line([(head_cx, head_cy + head_r + 4), (head_cx, 175)], fill=(0, 230, 150, 255), width=10)
    draw.line([(head_cx, 125), (head_cx - 45, 80)], fill=(0, 180, 216, 255), width=8)
    draw.line([(head_cx, 125), (head_cx + 45, 80)], fill=(0, 180, 216, 255), width=8)
    draw.line([(head_cx, 175), (head_cx - 24, 215)], fill=(255, 255, 255, 255), width=8)
    draw.line([(head_cx, 175), (head_cx + 24, 215)], fill=(255, 255, 255, 255), width=8)

    png_path = os.path.join(output_dir, "icon.png")
    ico_path = os.path.join(output_dir, "icon.ico")
    img.save(png_path, format="PNG")
    img.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

    # -------------------------------------------------------------
    # 2. Flechas Deportivas para QSpinBox (spin_up.png y spin_down.png)
    # Color Neón Volt (#CCFF00) sobre fondo transparente
    # -------------------------------------------------------------
    arrow_size = 32
    
    # Flecha Arriba (▲)
    img_up = Image.new("RGBA", (arrow_size, arrow_size), (0, 0, 0, 0))
    draw_up = ImageDraw.Draw(img_up)
    draw_up.polygon([(16, 7), (6, 23), (26, 23)], fill=(204, 255, 0, 255))
    spin_up_path = os.path.join(output_dir, "spin_up.png")
    img_up.save(spin_up_path, format="PNG")

    # Flecha Abajo (▼)
    img_down = Image.new("RGBA", (arrow_size, arrow_size), (0, 0, 0, 0))
    draw_down = ImageDraw.Draw(img_down)
    draw_down.polygon([(6, 9), (26, 9), (16, 25)], fill=(204, 255, 0, 255))
    spin_down_path = os.path.join(output_dir, "spin_down.png")
    img_down.save(spin_down_path, format="PNG")

    # -------------------------------------------------------------
    # 3. Flecha Deportiva para QComboBox (combo_down.png)
    # Color Cyan Eléctrico (#00F0FF)
    # -------------------------------------------------------------
    img_combo = Image.new("RGBA", (arrow_size, arrow_size), (0, 0, 0, 0))
    draw_combo = ImageDraw.Draw(img_combo)
    draw_combo.polygon([(8, 11), (24, 11), (16, 21)], fill=(0, 240, 255, 255))
    combo_down_path = os.path.join(output_dir, "combo_down.png")
    img_combo.save(combo_down_path, format="PNG")

    print(f"[Assets] Generados con éxito en {output_dir}:")
    print(f"  - icon.ico / icon.png")
    print(f"  - spin_up.png / spin_down.png (Flechas Neón Volt)")
    print(f"  - combo_down.png (Flecha Cyan Eléctrico)")


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    generate_all_assets(current_dir)
