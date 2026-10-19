"""Native title layers: one restored background, existing transparent logo.

AI restoration is confined to the imported illustration master. Resampling,
alpha composition and GX encoding are deterministic. No generated menu text.
"""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
WORK = ROOT / 'translation_work/title_layered_preview'
LOGO_BOX = (24, 60, 389, 196)


def artwork(current_start):
    source = Image.open(WORK / 'sai-background-draft.png').convert('RGBA')
    # Locate the uninterrupted illustration using dark pixels across each row.
    # Exclude bottom copyright text: it is well below the illustration endpoint.
    rows = []
    for y in range(source.height):
        count = sum(min(source.getpixel((x, y))[:3]) < 220
                    for x in range(0, source.width, 8))
        if count > source.width / 8 * .60:
            rows.append(y)
        elif rows:
            break
    top = min(rows)
    bottom = max(rows) + 1
    assert abs(top / source.height - 52 / 480) < .015
    assert abs(bottom / source.height - 379 / 480) < .015
    clean = current_start.copy()
    clean.paste((255, 255, 255, 255), (0, 0, 640, 52))
    clean.paste(source.crop((0, top, source.width, bottom)).resize(
        (640, 327), Image.Resampling.LANCZOS), (0, 52))
    # Retain the released English copyright pixels, with no regeneration.
    assert clean.crop((0, 379, 640, 480)).tobytes() == current_start.crop(
        (0, 379, 640, 480)).tobytes()
    logo_source = Image.open(ROOT / 'GitHub_Release_v1/project-logo.png').convert('RGBA')
    width = LOGO_BOX[2] - LOGO_BOX[0]
    height = round(width * logo_source.height / logo_source.width)
    logo = logo_source.resize((width, height), Image.Resampling.LANCZOS)
    assert height == LOGO_BOX[3] - LOGO_BOX[1]
    start = clean.copy()
    start.alpha_composite(logo, LOGO_BOX[:2])
    menu = clean.copy()
    # Match v47's retained thin board grid, this time genuinely behind alpha.
    scale = 6
    grid = Image.new('RGBA', (640 * scale, 480 * scale))
    draw = ImageDraw.Draw(grid)
    for x in range(49, 640, 90):
        draw.line((x * scale, 52 * scale, x * scale, 378 * scale),
                  fill=(0, 0, 0, 100), width=scale)
    for y in range(70, 379, 85):
        draw.line((0, y * scale, 640 * scale, y * scale),
                  fill=(0, 0, 0, 100), width=scale)
    grid = grid.resize((640, 480), Image.Resampling.LANCZOS)
    grid.paste((0, 0, 0, 0), (0, 0, 640, 52))
    grid.paste((0, 0, 0, 0), (0, 379, 640, 480))
    menu.alpha_composite(grid)
    menu.alpha_composite(logo, LOGO_BOX[:2])
    for im in (start, menu):
        assert set(im.crop((0, 0, 640, 52)).getdata()) == {(255,255,255,255)}
        assert im.crop((0,379,640,480)).tobytes() == current_start.crop((0,379,640,480)).tobytes()
    clean.save(WORK / 'native-clean-background.png')
    logo.save(WORK / 'native-logo-layer.png')
    return {'tit00.D4': start, 'tit02.D4': menu}, {
        'restoration_crop': [0, top, source.width, bottom],
        'logo_box': list(LOGO_BOX),
        'logo_source': 'GitHub_Release_v1/project-logo.png',
        'generated_logo_master_used': False,
        'copyright_pixels_exact_v56': True,
        'upper_margin_uniform_white': True,
        'grid_composited_before_logo': True,
    }
