# -*- coding: utf-8 -*-
"""동명동 카페거리 인포그래픽 영상 생성기 (세로 9:16, 프랑스어 + 한국어 자막)
모든 그림과 음악은 이 스크립트가 직접 만듭니다(외부 이미지·음원 없음).
실행: python3 make_video.py  ->  dongmyeong_cafe.mp4
"""
import math, os, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 720, 1280, 30
TR = 0.45  # 장면 전환(크로스페이드) 길이

# ---------------------------------------------------------------- 색상
CREAM = (246, 239, 228)
INK = (43, 36, 32)
COFFEE = (107, 66, 38)
LATTE = (196, 154, 108)
TERRA = (214, 96, 58)
TEAL = (38, 122, 122)
TEAL_L = (190, 222, 214)
GRAY = (120, 110, 104)
WHITE = (255, 255, 255)
BLUE = (52, 88, 160)

# ---------------------------------------------------------------- 글꼴
FR_DIR = "/usr/share/fonts/opentype/inter/"
KR_DIR = "/usr/share/fonts/truetype/nanum/"
_fc = {}
def font(name, size):
    key = (name, size)
    if key not in _fc:
        path = {"black": FR_DIR + "Inter-Black.otf", "bold": FR_DIR + "Inter-Bold.otf",
                "semi": FR_DIR + "Inter-SemiBold.otf", "reg": FR_DIR + "Inter-Regular.otf",
                "krb": KR_DIR + "NanumSquareRoundB.ttf", "kr": KR_DIR + "NanumSquareRoundR.ttf"}[name]
        _fc[key] = ImageFont.truetype(path, size)
    return _fc[key]

# ---------------------------------------------------------------- 보조 함수
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))

def ease(x):  # easeOutCubic
    x = clamp(x)
    return 1 - (1 - x) ** 3

def back(x):  # easeOutBack (살짝 튀는 등장)
    x = clamp(x)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2

def appear(t, start, dur=0.5):
    return ease((t - start) / dur)

KR_FALLBACK = {"black": "krb", "bold": "krb", "semi": "krb", "reg": "kr", "krb": "bold", "kr": "reg"}

def is_kr(c):
    return "\uac00" <= c <= "\ud7a3" or "\u3130" <= c <= "\u318f" or c in "○"

def runs(line, fname, size):
    """한 줄을 (글자들, 글꼴) 조각으로 나눈다: 한글은 나눔, 라틴(é, É 등)은 Inter"""
    fp, fk = font(fname, size), font(KR_FALLBACK[fname], size)
    kr_primary = fname in ("krb", "kr")
    out = []
    for c in line:
        if is_kr(c):
            f = fp if kr_primary else fk
        elif kr_primary and ord(c) > 127 and c not in "·":
            f = fk
        else:
            f = fp
        if out and out[-1][1] is f:
            out[-1][0] += c
        else:
            out.append([c, f])
    return out

def mlen(line, fname, size):
    return sum(f.getlength(s_) for s_, f in runs(line, fname, size))

def fr_typo(text):
    # 프랑스어 문장부호 앞 공백을 줄바꿈 없는 공백으로
    for a, b in [(" :", "\u00a0:"), (" !", "\u00a0!"), (" ?", "\u00a0?"), (" »", "\u00a0»"), ("« ", "«\u00a0")]:
        text = text.replace(a, b)
    return text

def wrap(text, fname, size, max_w):
    out = []
    for para in text.split("\n"):
        words, line = para.split(" "), ""
        for w_ in words:
            test = (line + " " + w_).strip()
            if mlen(test, fname, size) <= max_w or not line:
                line = test
            else:
                out.append(line)
                line = w_
        out.append(line)
    return out

_tc = {}
def text_img(text, fname, size, color, max_w=640, align="center", spacing=8):
    key = (text, fname, size, color, max_w, align, spacing)
    if key in _tc:
        return _tc[key]
    text = fr_typo(text)
    f = font(fname, size)
    lines = wrap(text, fname, size, max_w)
    asc, desc = f.getmetrics()
    lh = asc + desc + spacing
    widths = [mlen(l, fname, size) for l in lines]
    w = int(max(widths)) + 6
    h = lh * len(lines) - spacing + 6
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        x = (w - widths[i]) / 2 if align == "center" else 3
        base = 3 + i * lh + asc
        for s_, ff in runs(l, fname, size):
            d.text((x, base), s_, font=ff, fill=color + (255,), anchor="ls")
            x += ff.getlength(s_)
    _tc[key] = im
    return im

_lut = {}
def put(canvas, im, x, y, alpha=1.0, anchor="c", scale=1.0):
    """RGBA 이미지를 canvas 위에 붙인다. anchor: c(중앙) / lt(좌상단) / mt(상단중앙)"""
    if alpha <= 0.003:
        return
    if scale != 1.0:
        if scale <= 0.01:
            return
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if anchor == "c":
        x, y = x - im.width / 2, y - im.height / 2
    elif anchor == "mt":
        x = x - im.width / 2
    elif anchor == "lm":
        y = y - im.height / 2
    mask = im.getchannel("A")
    if alpha < 0.999:
        a = int(alpha * 255)
        if a not in _lut:
            _lut[a] = [v * a // 255 for v in range(256)]
        mask = mask.point(_lut[a])
    canvas.paste(im, (int(round(x)), int(round(y))), mask)

def txt(canvas, text, fname, size, color, x, y, t=1.0, start=0.0, dur=0.5,
        max_w=640, anchor="mt", align="center", rise=24):
    a = appear(t, start, dur)
    if a <= 0:
        return
    im = text_img(text, fname, size, color, max_w, align)
    put(canvas, im, x, y + (1 - a) * rise, a, anchor)
    return im

_pc = {}
def plate(key, w, h, draw_fn, ss=3):
    """초과 해상도(ss배)로 그린 뒤 줄여서 부드러운 도형을 만든다."""
    if key in _pc:
        return _pc[key]
    big = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    draw_fn(d, ss, big)
    im = big.resize((w, h), Image.LANCZOS)
    _pc[key] = im
    return im

def chip(label, fg=WHITE, bg=TERRA, size=24, pad=18, fname="bold"):
    ti = text_img(label, fname, size, fg, 2000)
    tw = ti.width
    w, h = tw + pad * 2, size + 22
    def dr(d, s, _):
        d.rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=h * s // 2, fill=bg + (255,))
    im = plate(("chip", label, bg, size, fname), w, h, dr).copy()
    im.alpha_composite(ti, (pad - 3, (h - ti.height) // 2))
    return im

def solid_bg(color):
    return Image.new("RGB", (W, H), color)

_bgc = {}
def gradient(top, bottom):
    key = (top, bottom)
    if key not in _bgc:
        y = np.linspace(0, 1, H)[:, None, None]
        a = np.array(top)[None, None, :] * (1 - y) + np.array(bottom)[None, None, :] * y
        a = np.repeat(a, W, axis=1).astype(np.uint8)
        _bgc[key] = Image.fromarray(a, "RGB")
    return _bgc[key].copy()

# ---------------------------------------------------------------- 그림(스프라이트)
def cup_sprite(size=300):
    def dr(d, s, _):
        S = size * s
        # 받침
        d.ellipse([S * .05, S * .78, S * .95, S * .98], fill=(232, 222, 208, 255))
        d.ellipse([S * .12, S * .80, S * .88, S * .94], fill=(250, 246, 240, 255))
        # 손잡이
        d.ellipse([S * .66, S * .40, S * .94, S * .70], outline=(250, 246, 240, 255), width=int(S * .06))
        # 컵 몸통
        d.rounded_rectangle([S * .18, S * .30, S * .76, S * .86], radius=int(S * .14), fill=(250, 246, 240, 255))
        d.rectangle([S * .18, S * .30, S * .76, S * .5], fill=(250, 246, 240, 255))
        d.rectangle([S * .18, S * .52, S * .76, S * .60], fill=TERRA + (255,))
        # 커피 표면
        d.ellipse([S * .18, S * .24, S * .76, S * .38], fill=(250, 246, 240, 255))
        d.ellipse([S * .22, S * .26, S * .72, S * .36], fill=COFFEE + (255,))
        d.ellipse([S * .36, S * .28, S * .58, S * .33], fill=LATTE + (255,))
    return plate(("cup", size), size, size, dr)

def mini_cup(size=40, col=COFFEE):
    def dr(d, s, _):
        S = size * s
        d.ellipse([0, 0, S - 1, S - 1], fill=col + (255,))
        d.rounded_rectangle([S * .27, S * .32, S * .66, S * .72], radius=int(S * .08), fill=WHITE + (255,))
        d.ellipse([S * .58, S * .38, S * .80, S * .60], outline=WHITE + (255,), width=max(2, int(S * .06)))
    return plate(("mcup", size, col), size, size, dr)

def pin_sprite(size=70, col=TERRA):
    def dr(d, s, _):
        S = size * s
        d.ellipse([S * .1, 0, S * .9, S * .8], fill=col + (255,))
        d.polygon([(S * .2, S * .55), (S * .8, S * .55), (S * .5, S)], fill=col + (255,))
        d.ellipse([S * .32, S * .22, S * .68, S * .58], fill=WHITE + (255,))
    return plate(("pin", size, col), size, size, dr)

# 전남·광주 개략 지도 (도식화한 형태, 실제 경계와 다름)
MAP_PTS = [(0.16, 0.06), (0.30, 0.02), (0.46, 0.05), (0.60, 0.00), (0.76, 0.04), (0.86, 0.14),
           (0.92, 0.30), (0.97, 0.46), (0.93, 0.58), (0.84, 0.62), (0.80, 0.74), (0.70, 0.70),
           (0.62, 0.80), (0.52, 0.76), (0.46, 0.88), (0.36, 0.84), (0.30, 0.99), (0.22, 0.88),
           (0.20, 0.76), (0.10, 0.72), (0.12, 0.60), (0.04, 0.52), (0.09, 0.40), (0.03, 0.30),
           (0.10, 0.20)]
GJ = (0.47, 0.26)  # 광주 위치(도식)

def map_sprite(w=560, h=520):
    def dr(d, s, _):
        pts = [(x * w * s, y * h * s) for x, y in MAP_PTS]
        d.polygon(pts, fill=TEAL_L + (255,))
        d.line(pts + [pts[0]], fill=TEAL + (255,), width=4 * s, joint="curve")
        # 섬들(신안 등 서남해 섬을 단순화)
        for (ix, iy, r) in [(-0.02, 0.48, .018), (0.00, 0.62, .022), (0.03, 0.78, .016), (0.12, 0.90, .02),
                            (0.40, 0.97, .016), (0.60, 0.92, .02), (0.78, 0.86, .015), (-0.01, 0.36, .014)]:
            cx, cy = ix * w * s + 20 * s, iy * h * s
            d.ellipse([cx - r * w * s, cy - r * w * s, cx + r * w * s, cy + r * w * s], fill=TEAL_L + (255,),
                      outline=TEAL + (255,), width=2 * s)
        # 광주 (가운데 위쪽)
        gx, gy = GJ[0] * w * s, GJ[1] * h * s
        r = 0.085 * w * s
        d.ellipse([gx - r, gy - r * .85, gx + r, gy + r * .85], fill=TEAL + (255,))
    return plate(("map", w, h), w, h, dr)

def street_plan(size=300):
    """동명동 주변 도식 지도 (원형 확대 창)"""
    def dr(d, s, big):
        S = size * s
        mask = Image.new("L", (S, S), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, S - 1, S - 1], fill=255)
        layer = Image.new("RGBA", (S, S), (238, 232, 220, 255))
        ld = ImageDraw.Draw(layer)
        # 길
        for i in range(-1, 6):
            ld.line([(0, S * (.12 + i * .2)), (S, S * (.02 + i * .2))], fill=WHITE + (255,), width=int(S * .045))
        for i in range(-1, 6):
            ld.line([(S * (.1 + i * .22), 0), (S * (.2 + i * .22), S)], fill=WHITE + (255,), width=int(S * .03))
        # 큰길(ACC와 동명동 사이)
        ld.line([(S * .50, 0), (S * .58, S)], fill=(250, 250, 250, 255), width=int(S * .07))
        # ACC 부지
        ld.rounded_rectangle([S * .06, S * .30, S * .44, S * .76], radius=int(S * .04), fill=(150, 190, 120, 255))
        ld.rounded_rectangle([S * .13, S * .44, S * .37, S * .62], radius=int(S * .02), fill=(240, 240, 236, 255))
        layer.putalpha(mask)
        big.paste(layer, (0, 0), layer)
        d.ellipse([0, 0, S - 1, S - 1], outline=INK + (255,), width=int(5 * s))
    return plate(("plan", size), size, size, dr)

def icon_circle(kind, size=150, bg=TEAL):
    def dr(d, s, _):
        S = size * s
        d.ellipse([0, 0, S - 1, S - 1], fill=bg + (255,))
        w_ = WHITE + (255,)
        if kind == "school":  # 책 + 연필 (학원가)
            d.polygon([(S * .2, S * .38), (S * .5, S * .46), (S * .5, S * .76), (S * .2, S * .68)], fill=w_)
            d.polygon([(S * .8, S * .38), (S * .5, S * .46), (S * .5, S * .76), (S * .8, S * .68)], fill=(225, 238, 236, 255))
            d.line([(S * .5, S * .46), (S * .5, S * .76)], fill=bg + (255,), width=int(S * .02))
            d.polygon([(S * .58, S * .18), (S * .66, S * .14), (S * .80, S * .34), (S * .72, S * .38)], fill=(250, 200, 90, 255))
        elif kind == "clock":  # 시계 (기다림)
            d.ellipse([S * .22, S * .22, S * .78, S * .78], fill=w_)
            d.line([(S * .5, S * .5), (S * .5, S * .32)], fill=bg + (255,), width=int(S * .05))
            d.line([(S * .5, S * .5), (S * .64, S * .58)], fill=bg + (255,), width=int(S * .05))
            d.ellipse([S * .46, S * .46, S * .54, S * .54], fill=bg + (255,))
        elif kind == "cups":  # 컵 세 개 (카페 거리)
            for i, cx in enumerate([.28, .5, .72]):
                y0 = .40 if i != 1 else .32
                d.rounded_rectangle([S * (cx - .1), S * y0, S * (cx + .1), S * (y0 + .26)], radius=int(S * .04), fill=w_)
                d.rectangle([S * (cx - .1), S * (y0 + .08), S * (cx + .1), S * (y0 + .12)], fill=(250, 200, 90, 255))
    return plate(("icon", kind, size, bg), size, size, dr)

def word_box(top, bottom, w=200, h=150, bg=WHITE, fg=INK, accent=TERRA, kcol=None):
    def dr(d, s, _):
        d.rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=24 * s, fill=bg + (255,),
                            outline=accent + (255,), width=4 * s)
    im = plate(("wbox", top, bottom, w, h, bg, accent), w, h, dr).copy()
    t1 = text_img(top, "bold", 28, fg, w - 20)
    t2 = text_img(bottom, "krb", 26, kcol or accent, w - 20)
    im.alpha_composite(t1, ((w - t1.width) // 2, 34))
    im.alpha_composite(t2, ((w - t2.width) // 2, 86))
    return im

def card(w, h, col=WHITE, radius=26, outline=None):
    def dr(d, s, _):
        d.rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=radius * s, fill=col + (255,),
                            outline=(outline + (255,)) if outline else None, width=3 * s if outline else 0)
    return plate(("card", w, h, col, radius, outline), w, h, dr)

def circle(r, col):
    def dr(d, s, _):
        d.ellipse([0, 0, 2 * r * s - 1, 2 * r * s - 1], fill=col + (255,))
    return plate(("circ", r, col), 2 * r, 2 * r, dr)

def heading(cv, t, fr, kr, y=120, col=TERRA):
    c = chip(fr, bg=col, size=26)
    a = appear(t, 0.1, 0.5)
    put(cv, c, W / 2, y + (1 - a) * 20, a)
    txt(cv, kr, "krb", 30, INK, W / 2, y + 40, t, 0.25)

def subtitle(cv, t, fr, kr, y=1000, start=0.4):
    """하단 자막 블록: 프랑스어(크게) + 한국어(작게)"""
    im = txt(cv, fr, "semi", 34, INK, W / 2, y, t, start, max_w=640)
    h = im.height if im is not None else text_img(fr, "semi", 34, INK, 640).height
    txt(cv, kr, "kr", 26, GRAY, W / 2, y + h + 14, t, start + 0.25, max_w=640)

# ---------------------------------------------------------------- 장면 1: 제목
def sc_title(t):
    cv = solid_bg(CREAM)
    sc = back(t / 0.8)
    put(cv, circle(250, TERRA), W / 2, 470, 1, scale=max(sc, 0.01))
    put(cv, circle(205, (226, 128, 92)), W / 2, 470, appear(t, .2), scale=max(back((t - .2) / .8), .01))
    cup = cup_sprite(320)
    bob = math.sin(t * 2.2) * 6
    put(cv, cup, W / 2, 500 + bob + (1 - ease((t - .3) / .7)) * 80, appear(t, .3, .6))
    # 김(증기)
    d = ImageDraw.Draw(cv)
    if t > 0.8:
        for k, x0 in enumerate([318, 360, 402]):
            pts = []
            for i in range(20):
                yy = 380 - i * 7
                xx = x0 + math.sin(i * .5 + t * 3 + k) * 9
                pts.append((xx, yy + bob))
            d.line(pts, fill=(255, 240, 230), width=6, joint="curve")
    txt(cv, "DONGMYEONG-DONG", "black", 62, INK, W / 2, 790, t, .6)
    txt(cv, "동명동 카페거리", "krb", 58, TERRA, W / 2, 880, t, .85)
    txt(cv, "La rue des cafés de Gwangju", "semi", 38, INK, W / 2, 975, t, 1.1)
    txt(cv, "광주의 커피 골목으로 산책을 떠나요", "kr", 27, GRAY, W / 2, 1030, t, 1.3)
    return cv

# ---------------------------------------------------------------- 장면 2: 위치
def sc_map(t):
    cv = solid_bg(CREAM)
    heading(cv, t, "OÙ ?", "어디에 있나요?")
    mw, mh = 520, 480
    mx, my = 60, 230
    put(cv, map_sprite(mw, mh), mx, my, appear(t, .2, .6), anchor="lt")
    gx, gy = mx + GJ[0] * mw, my + GJ[1] * mh
    # 지역 이름
    txt(cv, "Jeonnam-Gwangju", "bold", 26, TEAL, mx + 0.33 * mw, my + 0.56 * mh, t, .6, max_w=300)
    txt(cv, "전남광주통합특별시 (2026)", "krb", 20, TEAL, mx + 0.33 * mw, my + 0.56 * mh + 36, t, .75, max_w=300)
    # 광주 핀 (통통 튀며 등장)
    p = back((t - 1.0) / .6)
    if t > 1.0:
        put(cv, pin_sprite(64), gx, gy - 34 - 8 * abs(math.sin(t * 3)) * (t > 1.6), 1, scale=max(p, .01))
    # 확대 창 : 광주 → 동명동
    zs = ease((t - 1.8) / .7)
    zx, zy = 520, 560
    if t > 1.8:
        d = ImageDraw.Draw(cv)
        d.line([(gx, gy), (gx + (zx - gx) * zs, gy + (zy - gy) * zs)], fill=INK, width=3)
        plan = street_plan(270)
        put(cv, plan, zx, zy, 1, scale=max(zs, .01))
        if zs > .98:
            # 카페 핀들
            cups = [(.70, .20), (.82, .36), (.66, .48), (.88, .58), (.72, .72), (.62, .30), (.80, .84)]
            for i, (u, v) in enumerate(cups):
                a = back((t - 2.6 - i * .12) / .4)
                if a > 0:
                    put(cv, mini_cup(30), zx - 135 + u * 270, zy - 135 + v * 270, 1, scale=max(a, .01))
            c = chip("ACC", bg=(88, 140, 70), size=20, pad=12)
            put(cv, c, zx - 135 + .25 * 270, zy - 135 + .53 * 270, appear(t, 2.6))
            c2 = chip("Dongmyeong-dong", bg=COFFEE, size=20, pad=12)
            put(cv, c2, zx + 10, zy + 150, appear(t, 3.0))
    txt(cv, "* carte schématique · 도식화한 지도", "reg", 18, GRAY, 40, 950, t, .8, anchor="lt", max_w=400, align="left")
    subtitle(cv, t, "Au cœur de Gwangju (Dong-gu), juste à côté de l'Asia Culture Center (ACC).",
             "광주 동구, 국립아시아문화전당(ACC)과 길 하나 사이", y=1000, start=.6)
    return cv

# ---------------------------------------------------------------- 장면 3: 연표
TIMELINE = [
    ("1970–90", "Quartier aisé : belles maisons et vieux hanoks", "고급 주택과 한옥이 모인 부촌", COFFEE),
    ("2005", "Le siège provincial du Jeonnam part à Muan : le quartier décline",
     "전남도청 무안 이전, 동네가 활기를 잃다", GRAY),
    ("2015", "L'ACC ouvre sur le site de l'ancien siège provincial, lieu de mémoire du 18 mai 1980",
     "5·18의 현장, 옛 전남도청 자리에 ACC 개관", (88, 140, 70)),
    ("2021", "1er festival « Promenade café de Dongmyeong »", "제1회 '동명커피산책' 축제", TERRA),
    ("2026", "Gwangju et le Jeonnam, séparés en 1986, sont de nouveau réunis",
     "1986년 나뉜 광주·전남, 다시 하나로", TEAL),
]

def sc_timeline(t):
    cv = solid_bg(CREAM)
    heading(cv, t, "HISTOIRE", "동명동이 걸어온 길")
    top, step = 215, 196
    lx = 108
    d = ImageDraw.Draw(cv)
    n = len(TIMELINE)
    per = 2.95
    # 세로선 (자라남)
    prog = clamp((t - .3) / (per * (n - 1) + .6))
    y_end = top + 20 + prog * step * (n - 1)
    d.line([(lx, top + 20), (lx, y_end)], fill=(214, 200, 184), width=8)
    for i, (yr, fr, kr, col) in enumerate(TIMELINE):
        st = .4 + i * per
        y = top + i * step
        a = back((t - st) / .5)
        if t < st:
            continue
        put(cv, circle(22, col), lx, y + 20, 1, scale=max(a, .01))
        put(cv, circle(10, WHITE), lx, y + 20, 1, scale=max(a, .01))
        c = chip(yr, bg=col, size=22, pad=14)
        put(cv, c, lx + 44, y + 2, appear(t, st + .05), anchor="lt")
        # 지금 등장한 항목은 진하게, 지난 항목은 흐리게
        cur = i == n - 1 or t < st + per
        fc = INK if cur else (150, 140, 132)
        kc = GRAY if cur else (175, 166, 158)
        im = txt(cv, fr, "semi", 26, fc, lx + 44, y + 48, t, st + .15, max_w=550, anchor="lt", align="left")
        if im is not None:
            txt(cv, kr, "kr", 22, kc, lx + 44, y + 54 + im.height, t, st + .3, max_w=550, anchor="lt", align="left")
    return cv

# ---------------------------------------------------------------- 장면 4: 왜 카페가 많을까
def sc_why(t):
    cv = solid_bg((240, 232, 220))
    heading(cv, t, "POURQUOI TANT DE CAFÉS ?", "왜 카페가 많아졌을까?", col=COFFEE)
    steps = [("school", "Un quartier de hagwon (cours privés)", "학원이 모인 동네"),
             ("clock", "Les parents attendent… au café", "기다리는 부모님은 카페로"),
             ("cups", "Des cafés au style unique", "개성 있는 카페 거리로")]
    cols = [TEAL, TERRA, COFFEE]
    y0, gap = 260, 215
    d = ImageDraw.Draw(cv)
    for i, (k, fr, kr) in enumerate(steps):
        st = .5 + i * 1.3
        y = y0 + i * gap
        if t < st:
            continue
        a = back((t - st) / .5)
        put(cv, icon_circle(k, 140, cols[i]), 140, y + 70, 1, scale=max(a, .01))
        txt(cv, fr, "semi", 30, INK, 235, y + 30, t, st + .1, max_w=440, anchor="lt", align="left")
        h = text_img(fr, "semi", 30, INK, 440, "left").height
        txt(cv, kr, "kr", 24, GRAY, 235, y + 40 + h, t, st + .25, max_w=440, anchor="lt", align="left")
        if i < len(steps) - 1 and t > st + .5:
            ar = ease((t - st - .5) / .4)
            ys, ye = y + 148, y + 148 + 50 * ar
            d.line([(140, ys), (140, ye)], fill=INK, width=5)
            if ar > .95:
                d.polygon([(128, ye - 4), (152, ye - 4), (140, ye + 12)], fill=INK)
    subtitle(cv, t, "On raconte que tout a commencé avec les parents qui attendaient leurs enfants.",
             "학원 간 아이를 기다리던 부모님들에게서 시작됐다고 해요.", y=980, start=3.4)
    return cv

# ---------------------------------------------------------------- 장면 5: 이름 풀이
def sc_name(t):
    cv = solid_bg(CREAM)
    heading(cv, t, "UN SURNOM", "'동리단길'이라는 별명")
    b1 = word_box("Dong-gu", "동구", 210, 150, accent=TEAL)
    b2 = word_box("Gyeongnidan-gil", "경리단길 (서울)", 300, 150, accent=BLUE)
    b3 = word_box("Dongnidan-gil", "동리단길", 380, 160, bg=TERRA, fg=WHITE, accent=TERRA, kcol=WHITE)
    put(cv, b1, 155, 330, 1, scale=max(back((t - .4) / .5), .01))
    put(cv, b2, 500, 330, 1, scale=max(back((t - 1.0) / .5), .01))
    put(cv, text_img("+", "black", 64, INK), 315, 330, appear(t, .8))
    put(cv, text_img("=", "black", 70, INK), W / 2, 480, appear(t, 1.6))
    s3 = back((t - 1.9) / .6)
    put(cv, b3, W / 2, 620, 1, scale=max(s3, .01))
    txt(cv, "Gyeongnidan-gil : rue branchée de Séoul", "reg", 22, GRAY, W / 2, 430 - 20, t, 1.2, max_w=600)
    txt(cv, "-gil = rue · 길 = 거리", "bold", 26, TEAL, W / 2, 740, t, 2.4)
    subtitle(cv, t, "En Corée, on surnomme les rues à la mode d'après Gyeongnidan-gil, à Séoul.",
             "서울 '경리단길'을 본떠 '○리단길'이라 부르는 유행이 있어요.", y=880, start=2.6)
    return cv

# ---------------------------------------------------------------- 장면 6: 한국 카페 vs 프랑스 카페
ROWS = [
    ("Commande", "주문", "Au comptoir + bipeur", "카운터 주문 · 진동벨", "Service à table", "테이블 서빙"),
    ("Boisson", "음료", "Americano glacé, même en hiver", "한겨울에도 아이스 아메리카노", "Espresso", "에스프레소"),
    ("Pour…", "용도", "Étudier, travailler, photos", "카공 · 사진", "Discuter en terrasse", "테라스 수다"),
    ("Règle", "규칙", "Souvent 1 boisson / personne", "1인 1음료인 곳이 많음", "Pas de règle écrite", "정해진 규칙 없음"),
]

def sc_compare(t):
    cv = solid_bg(CREAM)
    heading(cv, t, "CAFÉ CORÉEN vs CAFÉ FRANÇAIS", "한국 카페 vs 프랑스 카페", col=INK)
    cx1, cx2 = 255, 545   # 두 열 중심
    cw = 270
    y = 225
    put(cv, chip("CORÉE · 한국", bg=TERRA, size=24, fname="krb"), cx1, y, appear(t, .4))
    put(cv, chip("FRANCE · 프랑스", bg=BLUE, size=24, fname="krb"), cx2, y, appear(t, .5))
    rh, ry = 168, 275
    for i, (lab, labk, k1, k1k, f1, f1k) in enumerate(ROWS):
        st = .9 + i * 1.6
        if t < st:
            continue
        a = appear(t, st, .45)
        yy = ry + i * rh + (1 - a) * 20
        put(cv, card(cw, rh - 18, WHITE, 22, (232, 205, 190)), cx1, yy + (rh - 18) / 2, a)
        put(cv, card(cw, rh - 18, WHITE, 22, (200, 210, 232)), cx2, yy + (rh - 18) / 2, a)
        # 항목 이름 (왼쪽 세로 띠)
        put(cv, text_img(lab, "bold", 18, GRAY), 62, yy + 52, a)
        put(cv, text_img(labk, "krb", 18, GRAY), 62, yy + 80, a)
        for cx, fr, kr, col in [(cx1, k1, k1k, TERRA), (cx2, f1, f1k, BLUE)]:
            im = text_img(fr, "bold", 24, col, cw - 30)
            ik = text_img(kr, "kr", 20, GRAY, cw - 30)
            tot = im.height + 8 + ik.height
            top = yy + (rh - 18 - tot) / 2
            put(cv, im, cx, top, a, anchor="mt")
            put(cv, ik, cx, top + im.height + 8, a, anchor="mt")
    txt(cv, "* tendances générales · 일반적인 경향", "reg", 18, GRAY, W / 2, 960, t, 1.0)
    subtitle(cv, t, "Petites différences, grandes surprises !", "작은 차이, 큰 재미!", y=1015, start=7.4)
    return cv

# ---------------------------------------------------------------- 장면 7: 마무리
def sc_outro(t):
    cv = gradient((222, 108, 66), (196, 82, 48))
    d = ImageDraw.Draw(cv)
    put(cv, circle(190, (232, 140, 104)), W / 2, 420, 1, scale=max(back(t / .7), .01))
    bob = math.sin(t * 2.4) * 5
    put(cv, cup_sprite(260), W / 2, 440 + bob, appear(t, .2))
    for k, x0 in enumerate([326, 360, 394]):
        if t > .6:
            pts = [(x0 + math.sin(i * .5 + t * 3 + k) * 8, 330 - i * 6 + bob) for i in range(18)]
            d.line(pts, fill=(255, 236, 226), width=5, joint="curve")
    txt(cv, "Venez flâner à Dongmyeong-dong !", "black", 46, WHITE, W / 2, 690, t, .5, max_w=620)
    txt(cv, "동명동에서 커피 한잔 어때요?", "krb", 40, (255, 232, 214), W / 2, 830, t, .8)
    put(cv, chip("Gwangju · Jeonnam", fg=TERRA, bg=WHITE, size=26), W / 2, 930, appear(t, 1.1))
    txt(cv, "Infographie & musique : création originale · 그림·음악 직접 제작", "reg", 18,
        (255, 225, 205), W / 2, 1140, t, 1.4, max_w=660)
    return cv

SCENES = [(sc_title, 4.5), (sc_map, 6.5), (sc_timeline, 15.6), (sc_why, 7.6),
          (sc_name, 6.6), (sc_compare, 9.4), (sc_outro, 5.2)]
STARTS = []
_acc = 0.0
for _, dur in SCENES:
    STARTS.append(_acc)
    _acc += dur
TOTAL = _acc

def chrome(cv, T, i):
    """모든 장면 공통: 상단 머리말, 하단 진행 막대"""
    d = ImageDraw.Draw(cv)
    dark = i == len(SCENES) - 1
    col = WHITE if dark else INK
    f = font("bold", 18)
    d.text((34, 34), "G W A N G J U  ·  J E O N N A M", font=f, fill=col)
    fk = font("krb", 20)
    lab = "동명동 카페거리"
    d.text((W - 34 - fk.getlength(lab), 31), lab, font=fk, fill=col)
    d.rounded_rectangle([34, 1236, W - 34, 1244], radius=4, fill=(255, 255, 255) if not dark else (230, 130, 100))
    d.rounded_rectangle([34, 1236, 34 + (W - 68) * T / TOTAL, 1244], radius=4, fill=TERRA if not dark else WHITE)

def frame_at(T):
    i = max(k for k in range(len(SCENES)) if STARTS[k] <= T + 1e-9)
    fn, dur = SCENES[i]
    lt = T - STARTS[i] + (TR if i > 0 else 0)
    cv = fn(lt)
    if i + 1 < len(SCENES):
        nxt = STARTS[i + 1]
        if T > nxt - TR:
            k = (T - (nxt - TR)) / TR
            cv2 = SCENES[i + 1][0](T - (nxt - TR))
            cv = Image.blend(cv, cv2, ease(k))
            i = i if k < .5 else i + 1
    chrome(cv, T, i)
    return cv

# ---------------------------------------------------------------- 음악 (직접 합성한 로파이 기타풍)
def make_music(path, total):
    sr = 44100
    n = int(sr * (total + 0.5))
    out = np.zeros(n)
    bpm = 84
    beat = 60 / bpm
    rng = np.random.default_rng(7)

    def pluck(freq, dur, amp):
        N = int(sr / freq)
        buf = rng.uniform(-1, 1, N)
        m = int(sr * dur)
        y = np.empty(m)
        for i in range(m):
            y[i] = buf[i % N]
            buf[i % N] = 0.996 * 0.5 * (buf[i % N] + buf[(i + 1) % N])
        env = np.minimum(1, np.arange(m) / 200)
        return y * env * amp

    def add(sig, t0):
        s = int(t0 * sr)
        e = min(n, s + len(sig))
        if s < n:
            out[s:e] += sig[: e - s]

    def hz(m):
        return 440 * 2 ** ((m - 69) / 12)

    # Cmaj7 - Am7 - Fmaj7 - G6 (한 마디 4박)
    chords = [[48, 55, 59, 64], [45, 52, 55, 60], [41, 48, 52, 57], [43, 50, 55, 59]]
    melody = [76, 74, 72, 74, 76, 79, 76, 74, 72, 69, 72, 74, 72, 71, 67, 69]
    cache = {}
    def cp(m, d_, a):
        key = (m, d_, a)
        if key not in cache:
            cache[key] = pluck(hz(m), d_, a)
        return cache[key]

    bar = 4 * beat
    t, b = 0.0, 0
    while t < total:
        ch = chords[b % 4]
        add(cp(ch[0] - 12, bar, .35), t)
        for k, m in enumerate(ch):  # 아르페지오
            add(cp(m, 1.6, .16), t + k * beat * .5)
            add(cp(ch[(k + 2) % 4] + 12, 1.0, .07), t + 2 * beat + k * beat * .5)
        if b >= 1:  # 멜로디는 둘째 마디부터
            for k in range(4):
                m = melody[(b * 4 + k) % len(melody)]
                if (b + k) % 3 != 2:
                    add(cp(m, 1.2, .14), t + k * beat)
        # 부드러운 킥 + 하이햇
        for k in range(4):
            tt = t + k * beat
            if k in (0, 2):
                L = int(.25 * sr)
                x = np.arange(L) / sr
                kick = np.sin(2 * np.pi * (55 + 60 * np.exp(-x * 30)) * x) * np.exp(-x * 14) * .35
                add(kick, tt)
            L = int(.06 * sr)
            hat = rng.uniform(-1, 1, L) * np.exp(-np.arange(L) / sr * 70) * .04
            hat = np.diff(hat, prepend=0)
            add(hat, tt + beat * .5)
        t += bar
        b += 1
    # 따뜻한 느낌 : 간단한 저역 통과 + 페이드
    kernel = np.ones(6) / 6
    out = np.convolve(out, kernel, mode="same")
    fade_in = np.minimum(1, np.arange(n) / (sr * 1.0))
    fade_out = np.clip((total + 0.3 - np.arange(n) / sr) / 2.5, 0, 1)
    out *= fade_in * fade_out
    out = out / (np.max(np.abs(out)) + 1e-9) * 0.55
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())

# ---------------------------------------------------------------- 실행
def main(preview=None):
    if preview is not None:  # 특정 시각의 정지 화면만 저장
        for T in preview:
            frame_at(T).save(os.path.join(HERE, "preview_%05.1f.png" % T))
        return
    wav = os.path.join(HERE, "music.wav")
    make_music(wav, TOTAL)
    out = os.path.join(HERE, "dongmyeong_cafe.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-", "-i", wav,
           "-c:v", "libx264", "-preset", "slow", "-crf", "23", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    nf = int(TOTAL * FPS)
    for f in range(nf):
        p.stdin.write(frame_at(f / FPS).tobytes())
    p.stdin.close()
    p.wait()
    os.remove(wav)
    print("done", out, "%.1fs" % TOTAL)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        main([float(x) for x in sys.argv[1:]])
    else:
        main()
