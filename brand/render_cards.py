"""involveMINT branded text cards (feed 1080x1350 + story 1080x1920).
Used by chat sessions and by the newsletter-to-drafts scheduled task (run inside COMPOSIO_REMOTE_WORKBENCH).
render(spec, fonts_dir, header_png) -> (feed_jpeg_bytes, story_jpeg_bytes)
spec = {"kicker": "...", "headline": "...", "stats": [["70+", "label"], ...] (optional, max 3),
        "body": "..." (optional), "footer": "...", "url": "involvemint.io/donate", "accent": "green|orange|magenta"}
Brand kit in this repo: brand/fonts/Poppins-Bold.ttf, brand/fonts/Poppins-Medium.ttf, brand/header.png
"""
import io
from PIL import Image, ImageDraw, ImageFont

NAVY = (46, 45, 75); GREY = (120, 124, 140); BOX = (246, 248, 243); EDGE = (231, 232, 234)
ACC = {"green": (58, 171, 46), "orange": (245, 135, 46), "magenta": (184, 48, 143)}


def _f(d, name, size):
    return ImageFont.truetype(d.rstrip("/") + "/" + name, size)


def _wrap(dr, text, font, maxw):
    out = []
    for para in str(text).split("\n"):
        cur = ""
        for w in para.split():
            t = (cur + " " + w).strip()
            if dr.textlength(t, font=font) <= maxw:
                cur = t
            else:
                if cur:
                    out.append(cur)
                cur = w
        out.append(cur)
    return out


def _fit(dr, text, fonts_dir, name, start, minsize, maxw, maxlines):
    s = start
    while s > minsize:
        f = _f(fonts_dir, name, s)
        lines = _wrap(dr, text, f, maxw)
        if len(lines) <= maxlines and all(dr.textlength(l, font=f) <= maxw for l in lines):
            return f, lines, s
        s -= 4
    f = _f(fonts_dir, name, minsize)
    return f, _wrap(dr, text, f, maxw), minsize


def _card(W, H, spec, fonts_dir, header):
    acc = ACC.get(spec.get("accent", "green"), ACC["green"])
    im = Image.new("RGB", (W, H), "white"); dr = ImageDraw.Draw(im)
    story = H > 1500
    top = 70 if story else 0
    im.paste(header, (25, 20 + top))
    M = 54; maxw = W - 2 * M
    y = 165 + top
    if spec.get("kicker"):
        kf = _f(fonts_dir, "Poppins-Bold.ttf", 30)
        dr.text((M, y), spec["kicker"].upper(), font=kf, fill=acc); y += 52
    hf, hl, hs = _fit(dr, spec["headline"], fonts_dir, "Poppins-Bold.ttf", 92, 56, maxw, 3)
    for l in hl:
        dr.text((M, y), l, font=hf, fill=NAVY); y += int(hs * 1.08)
    y += 26
    foot_top = H - (300 if story else 250)
    stats = spec.get("stats") or []
    if stats:
        n = len(stats)
        gap = 24
        avail = foot_top - 40 - y
        bh = min(int((avail - gap * (n - 1)) / n), 300 if story else 230)
        for big, label in stats:
            dr.rounded_rectangle((M, y, W - M, y + bh), radius=18, fill=BOX, outline=EDGE, width=3)
            bf, _, bs = _fit(dr, big, fonts_dir, "Poppins-Bold.ttf", min(150, int(bh * 0.62)), 60, maxw - 80, 1)
            lf, ll, ls = _fit(dr, label, fonts_dir, "Poppins-Medium.ttf", 38, 26, maxw - 80, 2)
            block = bs * 1.18 + len(ll) * ls * 1.2
            ty = y + (bh - block) / 2 - bs * 0.12
            dr.text((M + 40, ty), big, font=bf, fill=acc)
            ty += bs * 1.18
            for l in ll:
                dr.text((M + 42, ty), l, font=lf, fill=GREY); ty += ls * 1.2
            y += bh + gap
    if spec.get("body"):
        bf, bl, bs = _fit(dr, spec["body"], fonts_dir, "Poppins-Medium.ttf", 60 if story else 52, 32, maxw, 7)
        avail = foot_top - 30 - y
        by = y + max(0, (avail - len(bl) * bs * 1.3) / 2) if not stats else y
        for l in bl:
            dr.text((M, by), l, font=bf, fill=NAVY); by += int(bs * 1.3)
    ly = foot_top
    dr.rectangle((0, ly, W, ly + 6), fill=acc)
    ff, fl, fs = _fit(dr, spec.get("footer", ""), fonts_dir, "Poppins-Bold.ttf", 40, 30, W - 110, 2)
    fy = ly + 34
    for l in fl:
        dr.text((55, fy), l, font=ff, fill=NAVY); fy += int(fs * 1.25)
    uf = _f(fonts_dir, "Poppins-Bold.ttf", 34)
    uy = H - (110 if story else 70)
    dr.text((55, uy), spec.get("url", "involvemint.io"), font=uf, fill=NAVY)
    hw = dr.textlength("@involvePGH", font=uf)
    dr.text((W - 57 - hw, uy), "@involvePGH", font=uf, fill=acc)
    b = io.BytesIO(); im.save(b, "JPEG", quality=90); return b.getvalue()


def render(spec, fonts_dir, header_png):
    header = Image.open(header_png).convert("RGB") if isinstance(header_png, str) else header_png
    return _card(1080, 1350, spec, fonts_dir, header), _card(1080, 1920, spec, fonts_dir, header)
