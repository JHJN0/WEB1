# -*- coding: utf-8 -*-
"""동명동 카페거리 일러스트 지도 (손그림 느낌) — 모든 그림을 코드로 직접 그립니다.
좌표는 720x1280 '단위' 기준이며, 실제로는 K배 크게 그려서 확대(줌)해도 선명합니다.
build() -> (배경 이미지, 아이콘 목록)
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

K = 3
PW, PH = 720, 1280
ND = "/usr/share/fonts/truetype/nanum/"
FD = "/usr/share/fonts/opentype/inter/"

SEA = (46, 160, 178)
SEA_D = (36, 138, 158)
LAND = (146, 201, 92)
LAND_D = (118, 178, 72)
ROAD = (245, 234, 205)
WHITE = (255, 255, 255)
CREAM = (252, 246, 232)
INK = (60, 48, 40)
BROWN = (128, 82, 48)
TERRA = (222, 102, 64)
ORANGE = (245, 150, 50)
YELLOW = (247, 200, 60)
GREEN_D = (52, 128, 70)
GREEN = (82, 160, 82)
GRAY = (150, 150, 146)
ROOF = (72, 78, 86)
BRICK = (184, 86, 62)


def U(v):
    return v * K


def F(name, size):
    path = {"brush": ND + "NanumBrush.ttf", "pen": ND + "NanumBarunpenB.ttf",
            "black": FD + "Inter-Black.otf", "bold": FD + "Inter-Bold.otf",
            "semi": FD + "Inter-SemiBold.otf", "krb": ND + "NanumSquareRoundB.ttf"}[name]
    return ImageFont.truetype(path, int(size * K))


def rgba(c, a=255):
    return tuple(c[:3]) + (a,)


# ------------------------------------------------------------- 손그림 도형
def wobble_ellipse(cx, cy, rx, ry, amp=0.04, seed=0, n=72):
    r = random.Random(seed)
    ph = [r.uniform(0, 6.28) for _ in range(4)]
    pts = []
    for i in range(n):
        a = i / n * 2 * math.pi
        k = 1 + amp * (math.sin(2 * a + ph[0]) * .6 + math.sin(3 * a + ph[1]) * .4 + math.sin(5 * a + ph[2]) * .25)
        pts.append((U(cx + rx * k * math.cos(a)), U(cy + ry * k * math.sin(a))))
    return pts


def wobble_poly(pts, amp=1.2, seed=0, steps=6):
    r = random.Random(seed)
    out = []
    for i in range(len(pts)):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % len(pts)]
        for s in range(steps):
            t = s / steps
            j = amp if 0 < s else amp * .3
            out.append((U(x0 + (x1 - x0) * t + r.uniform(-j, j)), U(y0 + (y1 - y0) * t + r.uniform(-j, j))))
    return out


def ell(d, cx, cy, rx, ry, col, amp=0.04, seed=0):
    d.polygon(wobble_ellipse(cx, cy, rx, ry, amp, seed), fill=rgba(col))


def poly(d, pts, col, amp=0.8, seed=0):
    d.polygon(wobble_poly(pts, amp, seed), fill=rgba(col))


def rect(d, x0, y0, x1, y1, col, amp=0.6, seed=0):
    poly(d, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], col, amp, seed)


def line(d, pts, col, w, seed=0, amp=0.6):
    r = random.Random(seed)
    p = [(U(x + r.uniform(-amp, amp)), U(y + r.uniform(-amp, amp))) for x, y in pts]
    d.line(p, fill=rgba(col), width=int(U(w)), joint="curve")
    rr = U(w) / 2
    for x, y in (p[0], p[-1]):
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=rgba(col))


def text(d, x, y, s, fnt, col, anchor="mm"):
    d.text((U(x), U(y)), s, font=fnt, fill=rgba(col), anchor=anchor)


def sprite(w, h, fn):
    im = Image.new("RGBA", (int(U(w)), int(U(h))), (0, 0, 0, 0))
    fn(ImageDraw.Draw(im))
    return im


# ------------------------------------------------------------- 아이콘들
def tree(seed=0, col=GREEN, dark=GREEN_D):
    def fn(d):
        rect(d, 15, 30, 19, 44, BROWN, .3, seed)
        ell(d, 17, 20, 15, 17, dark, .08, seed)
        ell(d, 15, 17, 11, 12, col, .08, seed + 1)
    return sprite(34, 46, fn)


def ginkgo(seed=0):
    def fn(d):
        rect(d, 15, 32, 19, 46, BROWN, .3, seed)
        poly(d, [(17, 2), (32, 34), (2, 34)], (232, 172, 40), 1.2, seed)
        poly(d, [(16, 6), (27, 30), (6, 30)], YELLOW, 1.0, seed + 2)
    return sprite(34, 48, fn)


def hanok_cafe(seed=0, label="CAFÉ"):
    def fn(d):
        # 기단
        rect(d, 8, 78, 122, 88, (200, 190, 170), .5, seed)
        # 벽 + 기둥
        rect(d, 16, 46, 114, 80, CREAM, .5, seed)
        for x in (16, 40, 66, 90, 110):
            rect(d, x, 46, x + 5, 80, BROWN, .3, seed + x)
        # 창살 문
        for x0 in (46, 72):
            rect(d, x0, 52, x0 + 14, 78, (235, 205, 150), .3, seed + x0)
            for k in range(3):
                line(d, [(x0 + 1, 58 + k * 7), (x0 + 13, 58 + k * 7)], BROWN, 1, seed)
        # 곡선 기와 지붕 (처마가 살짝 들림)
        roof = []
        for i in range(21):
            t = i / 20
            x = -2 + t * 134
            y = 44 - 10 * (abs(t - .5) * 2) ** 2.4
            roof.append((x, y))
        roof += [(110, 22), (66, 14), (22, 22)]
        poly(d, roof, ROOF, .5, seed)
        for k in range(9):
            x = 16 + k * 12
            line(d, [(x, 24), (x - 2, 40)], (98, 104, 112), 1.4, seed + k)
        line(d, [(22, 21), (110, 21)], (50, 54, 60), 3, seed)
        # 간판
        rect(d, 92, 56, 118, 68, (60, 40, 30), .3, seed)
        text(d, 105, 62.5, label, F("bold", 6), YELLOW)
    return sprite(132, 92, fn)


def brick_cafe(seed=0):
    def fn(d):
        rect(d, 10, 34, 96, 96, BRICK, .6, seed)
        for r in range(9):
            y = 40 + r * 6.5
            off = 0 if r % 2 else 6
            for c in range(7):
                x = 14 + off + c * 12
                if x < 92:
                    line(d, [(x, y), (x + 8, y)], (160, 70, 50), 1, seed + r * 10 + c, .2)
        poly(d, [(4, 36), (53, 6), (102, 36)], (90, 56, 46), .8, seed)
        for x0, y0 in ((22, 44), (64, 44)):
            rect(d, x0, y0, x0 + 18, y0 + 16, (200, 232, 240), .3, seed + x0)
        rect(d, 40, 70, 64, 96, (90, 60, 40), .4, seed)
        # 줄무늬 차양
        for k in range(6):
            col = WHITE if k % 2 else TERRA
            poly(d, [(14 + k * 13, 62), (27 + k * 13, 62), (27 + k * 13, 70), (14 + k * 13, 70)], col, .2, seed + k)
    return sprite(106, 100, fn)


def white_cafe(seed=0):
    def fn(d):
        rect(d, 8, 26, 98, 84, (250, 250, 246), .6, seed)
        rect(d, 8, 20, 98, 28, (60, 60, 60), .4, seed)
        rect(d, 16, 40, 66, 76, (180, 220, 232), .4, seed)
        line(d, [(41, 40), (41, 76)], WHITE, 1.4, seed)
        rect(d, 72, 46, 90, 84, (120, 170, 110), .4, seed)
        for k in range(5):
            col = GREEN if k % 2 else WHITE
            poly(d, [(14 + k * 11, 30), (25 + k * 11, 30), (25 + k * 11, 38), (14 + k * 11, 38)], col, .2, seed + k)
        # 화분
        ell(d, 100, 80, 6, 7, GREEN_D, .1, seed)
        rect(d, 96, 82, 104, 90, TERRA, .3, seed)
    return sprite(108, 92, fn)


def big_cup(seed=0):
    def fn(d):
        ell(d, 70, 112, 62, 14, (230, 220, 200), .03, seed)
        ell(d, 70, 110, 52, 10, CREAM, .03, seed)
        # 손잡이
        d.ellipse([U(102), U(56), U(132), U(92)], outline=rgba(CREAM), width=int(U(8)))
        poly(d, [(24, 46), (116, 46), (106, 104), (34, 104)], CREAM, .6, seed)
        rect(d, 28, 66, 112, 76, TERRA, .5, seed)
        ell(d, 70, 46, 46, 11, (232, 222, 206), .02, seed)
        ell(d, 70, 46, 41, 8.5, (120, 72, 40), .03, seed)
        # 라테 아트 하트
        ell(d, 64, 45, 7, 4.2, (232, 204, 168), .05, seed)
        ell(d, 76, 45, 7, 4.2, (232, 204, 168), .05, seed + 1)
        poly(d, [(58, 46), (82, 46), (70, 52)], (232, 204, 168), .3, seed)
    return sprite(140, 128, fn)


def acc(seed=0):
    def fn(d):
        # 지하에 묻힌 건물 + 옥상 정원, 유리 채광창
        ell(d, 100, 70, 96, 42, (110, 170, 80), .05, seed)
        ell(d, 100, 66, 88, 36, (160, 212, 110), .05, seed + 1)
        for i, (x, y) in enumerate([(50, 60), (80, 76), (112, 56), (146, 72), (126, 84)]):
            poly(d, [(x, y), (x + 16, y - 4), (x + 22, y + 8), (x + 6, y + 12)], (190, 228, 240), .4, seed + i)
            line(d, [(x + 3, y + 4), (x + 18, y + 1)], WHITE, 1, seed + i)
        rect(d, 82, 92, 120, 108, WHITE, .4, seed)
        text(d, 101, 100.5, "ACC", F("black", 11), (52, 110, 60))
    return sprite(200, 116, fn)


def old_dochung(seed=0):
    def fn(d):
        rect(d, 6, 30, 134, 84, (238, 232, 218), .6, seed)
        rect(d, 50, 16, 90, 84, (246, 242, 230), .6, seed)
        poly(d, [(46, 18), (70, 6), (94, 18)], (180, 170, 150), .5, seed)
        rect(d, 4, 26, 136, 32, (200, 192, 176), .4, seed)
        for r in range(2):
            for c in range(10):
                x = 12 + c * 12.4
                if 46 < x < 92:
                    continue
                rect(d, x, 38 + r * 20, x + 7, 48 + r * 20, (150, 170, 186), .2, seed + r * 20 + c)
        rect(d, 62, 58, 78, 84, (140, 110, 80), .3, seed)
        for c in range(3):
            rect(d, 54 + c * 12, 24, 60 + c * 12, 40, (150, 170, 186), .2, seed + c)
    return sprite(140, 90, fn)


def fountain(seed=0):
    def fn(d):
        ell(d, 50, 40, 46, 16, (200, 196, 186), .03, seed)
        ell(d, 50, 38, 40, 12, (120, 196, 226), .04, seed)
        for k, dx in enumerate((-16, 0, 16)):
            h = 30 if dx == 0 else 20
            line(d, [(50 + dx, 38), (50 + dx * 1.1, 38 - h)], (220, 244, 252), 3, seed + k)
            ell(d, 50 + dx * 1.15, 38 - h, 4, 3, WHITE, .1, seed + k)
    return sprite(100, 58, fn)


def hagwon(seed=0):
    def fn(d):
        rect(d, 14, 8, 76, 104, (236, 214, 170), .6, seed)
        cols = [TERRA, (70, 120, 190), (90, 170, 90), (150, 90, 170)]
        for i in range(4):
            y = 14 + i * 22
            rect(d, 18, y, 72, y + 8, cols[i], .3, seed + i)
            for c in range(4):
                rect(d, 21 + c * 13, y + 11, 29 + c * 13, y + 18, (180, 210, 230), .2, seed + i * 10 + c)
        rect(d, 76, 20, 92, 64, WHITE, .4, seed)
        text(d, 84, 32, "학", F("krb", 9), TERRA)
        text(d, 84, 50, "원", F("krb", 9), TERRA)
        # 책 더미
        for i, c in enumerate([(70, 120, 190), YELLOW, TERRA]):
            rect(d, 80 - i * 2, 96 - i * 8, 108 - i * 2, 103 - i * 8, c, .3, seed + 40 + i)
    return sprite(112, 108, fn)


def tents(seed=0):
    def fn(d):
        # 깃발 줄
        pts = [(4 + i * 7, 10 + 6 * math.sin(i / 21 * math.pi)) for i in range(22)]
        line(d, pts, INK, 1, seed, 0)
        for i in range(0, 21, 2):
            x, y = pts[i]
            col = [TERRA, YELLOW, (70, 120, 190), GREEN][i // 2 % 4]
            poly(d, [(x, y), (x + 7, y), (x + 3.5, y + 9)], col, .2, seed + i)
        for k, x in enumerate((10, 58, 106)):
            for j in range(4):
                col = WHITE if j % 2 else (TERRA if k != 1 else (70, 120, 190))
                poly(d, [(x + 24, 30), (x + j * 12, 52), (x + (j + 1) * 12, 52)], col, .3, seed + k * 5 + j)
            rect(d, x + 2, 52, x + 46, 74, CREAM, .4, seed + k)
            rect(d, x + 4, 60, x + 44, 64, (200, 160, 110), .3, seed + k)
    return sprite(160, 78, fn)


def signpost(seed=0):
    def fn(d):
        rect(d, 52, 20, 60, 110, (140, 96, 60), .4, seed)
        poly(d, [(8, 22), (92, 22), (104, 33), (92, 44), (8, 44)], (176, 124, 78), .5, seed)
        text(d, 52, 33.5, "DONGNIDAN-GIL", F("bold", 8.5), WHITE)
        poly(d, [(14, 52), (98, 52), (98, 72), (14, 72), (2, 62)], (176, 124, 78), .5, seed + 1)
        text(d, 56, 62.5, "동리단길", F("krb", 9.5), WHITE)
    return sprite(108, 112, fn)


def mudeung(seed=0):
    def fn(d):
        ell(d, 90, 118, 88, 18, LAND, .06, seed)
        poly(d, [(6, 116), (48, 60), (78, 36), (104, 34), (134, 60), (174, 116)], (122, 140, 110), 1.2, seed)
        poly(d, [(30, 116), (62, 72), (90, 52), (120, 70), (150, 116)], (98, 120, 96), 1.0, seed + 1)
        # 정상 부근의 바위 기둥(주상절리)
        for k, (x, hgt) in enumerate([(72, 9), (79, 13), (86, 11), (93, 14), (100, 10), (107, 8)]):
            top = 48 - hgt
            poly(d, [(x, top + 2), (x + 3, top), (x + 6, top + 2), (x + 6, 52), (x, 52)], (190, 186, 176), .2, seed + k)
            line(d, [(x + 1.5, top + 3), (x + 1.5, 50)], (220, 216, 208), .8, seed + k, .1)
        poly(d, [(56, 64), (78, 48), (110, 48), (126, 66), (90, 60)], (98, 120, 96), .6, seed + 7)
        for i, x in enumerate((40, 128, 152)):
            ell(d, x, 104, 7, 8, GREEN_D, .1, seed + i)
    return sprite(180, 136, fn)


def walker(seed=0, shirt=TERRA):
    def fn(d):
        ell(d, 20, 12, 8, 8.5, (245, 210, 170), .05, seed)
        poly(d, [(12, 9), (20, 2), (29, 9), (28, 6), (20, 3)], (60, 40, 30), .3, seed)
        rect(d, 12, 22, 28, 46, shirt, .5, seed)
        line(d, [(16, 46), (12, 66)], (60, 70, 100), 4.5, seed)
        line(d, [(24, 46), (28, 66)], (60, 70, 100), 4.5, seed + 1)
        line(d, [(28, 26), (36, 36)], shirt, 4, seed)
        rect(d, 33, 30, 40, 40, WHITE, .2, seed)
        rect(d, 33, 33, 40, 35, BROWN, .1, seed)
    return sprite(44, 70, fn)


def cat(seed=0):
    def fn(d):
        ell(d, 22, 26, 14, 9, (240, 170, 80), .06, seed)
        ell(d, 34, 16, 8, 7.5, (240, 170, 80), .06, seed)
        poly(d, [(28, 12), (30, 3), (34, 10)], (240, 170, 80), .2, seed)
        poly(d, [(36, 10), (40, 3), (41, 12)], (240, 170, 80), .2, seed)
        line(d, [(8, 26), (2, 14)], (240, 170, 80), 3, seed)
        ell(d, 31, 16, 1.2, 1.4, INK, 0, seed)
        ell(d, 37, 16, 1.2, 1.4, INK, 0, seed)
    return sprite(46, 36, fn)


def croissant(seed=0):
    def fn(d):
        for k, (x, r) in enumerate([(12, 8), (22, 10), (34, 10), (44, 8)]):
            ell(d, x, 16 + abs(k - 1.5) * 3, r, r * .8, (222, 160, 80) if k % 2 else (236, 182, 96), .06, seed + k)
    return sprite(56, 32, fn)


def cake(seed=0):
    def fn(d):
        poly(d, [(4, 30), (40, 30), (40, 14), (4, 22)], (250, 236, 210), .4, seed)
        poly(d, [(4, 22), (40, 14), (40, 18), (4, 26)], (240, 120, 130), .3, seed)
        ell(d, 34, 10, 4, 4, (220, 40, 60), .1, seed)
    return sprite(44, 34, fn)


def plane(seed=0):
    def fn(d):
        poly(d, [(4, 20), (60, 4), (26, 26)], WHITE, .4, seed)
        poly(d, [(26, 26), (60, 4), (32, 36)], (220, 232, 240), .4, seed)
    return sprite(64, 40, fn)


def islet_2026(seed=0):
    def fn(d):
        ell(d, 60, 64, 54, 16, LAND, .08, seed)
        ell(d, 60, 62, 46, 12, (170, 214, 120), .08, seed + 1)
        line(d, [(60, 58), (60, 10)], (90, 80, 70), 2, seed, .1)
        poly(d, [(61, 10), (106, 14), (100, 24), (106, 34), (61, 32)], TERRA, .4, seed)
        text(d, 82, 22, "2026", F("black", 10), WHITE)
    return sprite(120, 84, fn)


def waves(seed=0):
    def fn(d):
        for row in range(2):
            pts = [(4 + i * 2, 8 + row * 9 + 3 * math.sin(i * .45)) for i in range(26)]
            line(d, pts, (220, 244, 248), 2.2, seed + row, .1)
    return sprite(60, 28, fn)


def bird(seed=0):
    def fn(d):
        line(d, [(2, 8), (8, 3), (13, 8)], WHITE, 2, seed, .1)
        line(d, [(13, 8), (18, 3), (24, 8)], WHITE, 2, seed, .1)
    return sprite(26, 12, fn)


def beans(seed=0):
    def fn(d):
        for k, (x, y) in enumerate([(10, 12), (26, 8), (20, 22)]):
            ell(d, x, y, 7, 5, (110, 66, 36), .05, seed + k)
            line(d, [(x - 4, y), (x + 4, y)], (70, 40, 20), 1, seed + k, .1)
    return sprite(36, 30, fn)


# ------------------------------------------------------------- 질감
def paper_grain(w, h, seed=3, strength=16):
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, (h // 6, w // 6)).astype(np.float32)
    im = Image.fromarray(((n * 40) + 128).clip(0, 255).astype(np.uint8), "L").resize((w, h), Image.BICUBIC)
    im = im.filter(ImageFilter.GaussianBlur(2))
    fine = Image.fromarray(rng.integers(108, 148, (h, w), dtype=np.uint8), "L")
    a = (np.asarray(im, np.float32) - 128) * .7 + (np.asarray(fine, np.float32) - 128) * .5
    return a / 128 * strength


def apply_grain(img, grain):
    a = np.asarray(img).astype(np.float32)
    a[..., :3] = (a[..., :3] + grain[..., None]).clip(0, 255)
    return Image.fromarray(a.astype(np.uint8), img.mode)


def brush_title(s, size, col=WHITE, seed=1):
    """붓으로 쓴 듯한 마른 붓 자국(갈필) 글씨"""
    f = F("brush", size)
    l, t, r, b = f.getbbox(s)
    w, h = r - l + 40, b - t + 40
    im = Image.new("L", (w, h), 0)
    ImageDraw.Draw(im).text((20 - l, 20 - t), s, font=f, fill=255)
    im = im.filter(ImageFilter.MaxFilter(13)).filter(ImageFilter.GaussianBlur(1.2))  # 획을 굵게
    rng = np.random.default_rng(seed)
    streak = rng.random((h // 5, max(2, w // 90))).astype(np.float32)
    st = Image.fromarray((streak * 255).astype(np.uint8), "L").resize((w, h), Image.BICUBIC)
    st = np.asarray(st, np.float32) / 255
    mask = np.asarray(im, np.float32) / 255
    dry = np.clip((st - .07) * 9, 0, 1)  # 대부분은 꽉 차고, 군데군데 갈필 자국
    alpha = (mask * (0.35 + 0.65 * dry)).clip(0, 1)
    out = Image.new("RGBA", (w, h), rgba(col))
    out.putalpha(Image.fromarray((alpha * 255).astype(np.uint8), "L"))
    return out


# ------------------------------------------------------------- 지도 조립
LAND_C = (372, 760)

def land_shape():
    cx, cy = LAND_C
    pts = []
    for i in range(140):
        a = i / 140 * 2 * math.pi
        k = 1 + .07 * math.sin(3 * a + .7) + .05 * math.sin(5 * a + 2.1) + .03 * math.sin(9 * a + 1.3)
        pts.append((U(cx + 312 * k * math.cos(a)), U(cy + 370 * k * math.sin(a))))
    return pts


def label(d, x, y, kr, fr=None, col=INK, bg=(255, 255, 255)):
    fk = F("pen", 15)
    ff = F("semi", 9.5)
    wk = d.textlength(kr, font=fk) / K
    wf = (d.textlength(fr, font=ff) / K) if fr else 0
    w = max(wk, wf) + 16
    h = 22 + (13 if fr else 0)
    pts = wobble_poly([(x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2, y + h / 2), (x - w / 2, y + h / 2)], .6, int(x * y) % 97, 4)
    d.polygon(pts, fill=rgba(bg, 235))
    text(d, x, y - (6.5 if fr else 0), kr, fk, col)
    if fr:
        text(d, x, y + 9, fr, ff, (110, 100, 92))


def label_sprite(kr, fr=None, col=INK):
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    fk, ff = F("pen", 15), F("semi", 9.5)
    w = max(tmp.textlength(kr, font=fk), tmp.textlength(fr, font=ff) if fr else 0) / K + 20
    h = 26 + (13 if fr else 0)
    def fn(d):
        label(d, w / 2, h / 2, kr, fr, col)
    return sprite(w, h, fn)


# (이름, 스프라이트 함수, x, y, 등장 순서 그룹)
def items():
    L = []
    add = lambda name, spr, x, y, g: L.append((name, spr, x, y, g))
    # 바다 장식
    for i, (x, y) in enumerate([(70, 420), (640, 600), (60, 760), (660, 1010), (330, 1210), (560, 1190), (110, 1020)]):
        add("wave%d" % i, waves(i), x, y, 0)
    for i, (x, y) in enumerate([(560, 300), (590, 290), (575, 318)]):
        add("bird%d" % i, bird(i), x, y, 0)
    add("plane", plane(), 110, 330, 0)
    add("beans", beans(), 640, 1110, 0)
    # 무등산(동쪽), 2026 섬
    add("mudeung", mudeung(), 612, 418, 1)
    add("islet", islet_2026(), 92, 1176, 1)
    # 나무
    trees = [(110, 640, "g"), (140, 720, "y"), (230, 430, "g"), (300, 560, "y"), (470, 410, "g"), (585, 640, "y"),
             (640, 640, "g"), (600, 830, "y"), (250, 780, "g"), (430, 1060, "y"), (520, 1080, "g"), (300, 1100, "y"),
             (150, 980, "g"), (90, 860, "y"), (400, 730, "g"), (520, 650, "y"), (650, 760, "g"), (390, 420, "y")]
    for i, (x, y, k) in enumerate(trees):
        add("tree%d" % i, ginkgo(i) if k == "y" else tree(i), x, y, 2)
    # 건물
    add("hagwon", hagwon(), 160, 540, 3)
    add("hanok1", hanok_cafe(1), 362, 488, 3)
    add("brick", brick_cafe(2), 540, 560, 3)
    add("white", white_cafe(3), 566, 720, 3)
    add("hanok2", hanok_cafe(4, "COFFEE"), 470, 860, 3)
    add("bigcup", big_cup(), 350, 668, 3)
    add("acc", acc(), 190, 890, 3)
    add("dochung", old_dochung(), 300, 1010, 3)
    add("fountain", fountain(), 170, 1060, 3)
    add("tents", tents(), 470, 980, 3)
    add("sign", signpost(), 618, 930, 3)
    # 소품
    add("walker1", walker(1), 440, 610, 4)
    add("walker2", walker(2, (70, 120, 190)), 250, 640, 4)
    add("cat", cat(), 640, 560, 4)
    add("croissant", croissant(), 620, 790, 4)
    add("cake", cake(), 520, 770, 4)
    # 라벨
    add("lb_hagwon", label_sprite("학원가", "quartier des hagwon"), 150, 615, 5)
    add("lb_cafe", label_sprite("카페 골목", "ruelles des cafés"), 460, 535, 5)
    add("lb_acc", label_sprite("국립아시아문화전당", "Asia Culture Center"), 175, 815, 5)
    add("lb_dochung", label_sprite("옛 전남도청", "ancien siège provincial"), 320, 1078, 5)
    add("lb_fountain", label_sprite("5·18 민주광장", "place du 18-Mai"), 150, 1112, 5)
    add("lb_fest", label_sprite("동명커피산책", "festival du café"), 470, 1046, 5)
    add("lb_mudeung", label_sprite("무등산 (동쪽)", "mont Mudeung"), 612, 500, 5)
    add("lb_islet", label_sprite("전남광주통합특별시", "Jeonnam-Gwangju"), 108, 1238, 5)
    return L


def build():
    W, H = int(U(PW)), int(U(PH))
    base = Image.new("RGBA", (W, H), rgba(SEA))
    d = ImageDraw.Draw(base)
    # 수채 얼룩
    r = random.Random(5)
    for i in range(40):
        x, y = r.uniform(0, PW), r.uniform(0, PH)
        rr = r.uniform(30, 110)
        col = SEA_D if i % 2 else (58, 172, 190)
        d.polygon(wobble_ellipse(x, y, rr, rr * r.uniform(.6, 1), .12, i), fill=rgba(col))
    base = base.filter(ImageFilter.GaussianBlur(U(14)))
    d = ImageDraw.Draw(base)
    # 섬(동명동 일대)
    shp = land_shape()
    d.polygon(shp, fill=rgba(LAND_D))
    inner = [(LAND_C[0] * K + (x - LAND_C[0] * K) * .965, LAND_C[1] * K + (y - LAND_C[1] * K) * .965 - U(4)) for x, y in shp]
    d.polygon(inner, fill=rgba(LAND))
    # 풀 무늬
    for i in range(70):
        x, y = r.uniform(110, 640), r.uniform(440, 1080)
        line(d, [(x, y), (x + 2, y - 5)], LAND_D, 1.2, i, .2)
        line(d, [(x + 4, y), (x + 5, y - 6)], LAND_D, 1.2, i + 1, .2)
    # 길
    roads = [
        ([(70, 780), (200, 760), (330, 770), (460, 740), (600, 720), (680, 690)], 12),   # 동서 큰길
        ([(320, 400), (330, 520), (322, 640), (320, 800), (360, 940), (380, 1110)], 12),  # 남북 큰길
        ([(330, 600), (430, 590), (560, 610), (650, 600)], 7),
        ([(420, 760), (420, 900), (440, 1060)], 7),
        ([(520, 450), (500, 600), (520, 740)], 6),
        ([(150, 470), (220, 520), (322, 520)], 6),
        ([(560, 740), (590, 860), (560, 1000)], 6),
        ([(200, 780), (180, 960), (220, 1100)], 7),
    ]
    for i, (pts, w) in enumerate(roads):
        line(d, pts, ROAD, w, i, .8)
    # 광장 바닥
    d.polygon(wobble_ellipse(220, 1040, 110, 56, .05, 9), fill=rgba((236, 226, 196)))
    # 제목
    t1 = brush_title("DONGMYEONG", 128)
    base.alpha_composite(t1, (int((W - t1.width) / 2), int(U(46))))
    fk = F("krb", 38)
    sub = "동명동 카페거리"
    d = ImageDraw.Draw(base)
    text(d, PW / 2 + 1.5, 242 + 2, sub, fk, (30, 110, 126))
    text(d, PW / 2, 242, sub, fk, CREAM)
    text(d, PW / 2, 286, "La rue des cafés de Gwangju", F("semi", 22), (226, 246, 248))
    text(d, PW - 70, PH - 14, "carte illustrée, non à l'échelle ·", F("semi", 9), (200, 232, 238), "rb")
    text(d, PW - 18, PH - 14, "도식 지도", F("krb", 9), (200, 232, 238), "rb")
    grain = paper_grain(W, H)
    base = apply_grain(base, grain)
    return base, items(), grain


if __name__ == "__main__":
    import os
    base, its, grain = build()
    for name, spr, x, y, g in its:
        base.alpha_composite(spr, (int(U(x) - spr.width / 2), int(U(y) - spr.height / 2)))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dongmyeong_map.png")
    base.convert("RGB").save(out)
    base.convert("RGB").resize((PW, PH), Image.LANCZOS).save("/tmp/claude-0/-home-user-WEB1/6b17e658-f25a-5bcb-baa4-0568b7c94a00/scratchpad/map_small.png")
    print(out)
