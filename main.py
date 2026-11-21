# Passport spread for the Republic of Velmora — an invented country.
# Pure stdlib: draws a 1024x1024 PNG (entry.png) of an open passport spread:
# data page (portrait, fields, MRZ with real ICAO check digits) + visa page
# (Talmar visa sticker, four arrival/departure stamps, harbour-tax seal).
# Deterministic: no time, no randomness, no network. Two runs are byte-identical.
# Run: python3 -P -s main.py   (writes /output/entry.png)
import math
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows, 5 bits each, stored as 7 strings of 5 chars.
FONT = {
    'A': ('01110', '10001', '10001', '11111', '10001', '10001', '10001'),
    'B': ('11110', '10001', '10001', '11110', '10001', '10001', '11110'),
    'C': ('01110', '10001', '10000', '10000', '10000', '10001', '01110'),
    'D': ('11110', '10001', '10001', '10001', '10001', '10001', '11110'),
    'E': ('11111', '10000', '10000', '11110', '10000', '10000', '11111'),
    'F': ('11111', '10000', '10000', '11110', '10000', '10000', '10000'),
    'G': ('01110', '10001', '10000', '10111', '10001', '10001', '01111'),
    'H': ('10001', '10001', '10001', '11111', '10001', '10001', '10001'),
    'I': ('01110', '00100', '00100', '00100', '00100', '00100', '01110'),
    'J': ('00111', '00010', '00010', '00010', '00010', '10010', '01100'),
    'K': ('10001', '10010', '10100', '11000', '10100', '10010', '10001'),
    'L': ('10000', '10000', '10000', '10000', '10000', '10000', '11111'),
    'M': ('10001', '11011', '10101', '10101', '10001', '10001', '10001'),
    'N': ('10001', '11001', '10101', '10011', '10001', '10001', '10001'),
    'O': ('01110', '10001', '10001', '10001', '10001', '10001', '01110'),
    'P': ('11110', '10001', '10001', '11110', '10000', '10000', '10000'),
    'Q': ('01110', '10001', '10001', '10001', '10101', '10010', '01101'),
    'R': ('11110', '10001', '10001', '11110', '10100', '10010', '10001'),
    'S': ('01111', '10000', '10000', '01110', '00001', '00001', '11110'),
    'T': ('11111', '00100', '00100', '00100', '00100', '00100', '00100'),
    'U': ('10001', '10001', '10001', '10001', '10001', '10001', '01110'),
    'V': ('10001', '10001', '10001', '10001', '10001', '01010', '00100'),
    'W': ('10001', '10001', '10001', '10101', '10101', '10101', '01010'),
    'X': ('10001', '10001', '01010', '00100', '01010', '10001', '10001'),
    'Y': ('10001', '10001', '01010', '00100', '00100', '00100', '00100'),
    'Z': ('11111', '00001', '00010', '00100', '01000', '10000', '11111'),
    '0': ('01110', '10001', '10011', '10101', '11001', '10001', '01110'),
    '1': ('00100', '01100', '00100', '00100', '00100', '00100', '01110'),
    '2': ('01110', '10001', '00001', '00110', '01000', '10000', '11111'),
    '3': ('11111', '00010', '00100', '00010', '00001', '10001', '01110'),
    '4': ('00010', '00110', '01010', '10010', '11111', '00010', '00010'),
    '5': ('11111', '10000', '11110', '00001', '00001', '10001', '01110'),
    '6': ('00110', '01000', '10000', '11110', '10001', '10001', '01110'),
    '7': ('11111', '00001', '00010', '00100', '01000', '01000', '01000'),
    '8': ('01110', '10001', '10001', '01110', '10001', '10001', '01110'),
    '9': ('01110', '10001', '10001', '01111', '00001', '00010', '01100'),
    ' ': ('00000', '00000', '00000', '00000', '00000', '00000', '00000'),
    '.': ('00000', '00000', '00000', '00000', '00000', '01100', '01100'),
    ',': ('00000', '00000', '00000', '00000', '01100', '00100', '01000'),
    '-': ('00000', '00000', '00000', '01110', '00000', '00000', '00000'),
    '/': ('00001', '00010', '00010', '00100', '01000', '01000', '10000'),
    ':': ('00000', '01100', '01100', '00000', '01100', '01100', '00000'),
    '(': ('00010', '00100', '01000', '01000', '01000', '00100', '00010'),
    ')': ('01000', '00100', '00010', '00010', '00010', '00100', '01000'),
    '<': ('00010', '00100', '01000', '10000', '01000', '00100', '00010'),
    '>': ('01000', '00100', '00010', '00001', '00010', '00100', '01000'),
    "'": ('00100', '00100', '01000', '00000', '00000', '00000', '00000'),
    '&': ('01100', '10010', '10100', '01000', '10101', '10010', '01101'),
    '+': ('00000', '00100', '00100', '01110', '00100', '00100', '00000'),
    '=': ('00000', '00000', '11111', '00000', '11111', '00000', '00000'),
    '*': ('00000', '10101', '01110', '11111', '01110', '10101', '00000'),
    '%': ('11001', '11010', '00010', '00100', '01000', '01011', '10011'),
    '!': ('00100', '00100', '00100', '00100', '00100', '00000', '00100'),
    '?': ('01110', '10001', '00001', '00110', '00100', '00000', '00100'),
    ';': ('00000', '01100', '01100', '00000', '01100', '00100', '01000'),
    '_': ('00000', '00000', '00000', '00000', '00000', '00000', '11111'),
    '"': ('01010', '01010', '01010', '00000', '00000', '00000', '00000'),
    '#': ('01010', '01010', '11111', '01010', '11111', '01010', '01010'),
    '@': ('01110', '10001', '10111', '10101', '10110', '10000', '01110'),
    '[': ('01110', '01000', '01000', '01000', '01000', '01000', '01110'),
    ']': ('01110', '00010', '00010', '00010', '00010', '00010', '01110'),
    '•': ('00000', '00000', '01110', '01110', '01110', '00000', '00000'),
}


def text_width(s, scale, gap=1):
    return len(s) * (5 * scale + gap * scale) - gap * scale


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, color):
        self.w, self.h = w, h
        self.px = bytearray(color) * (w * h)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            return tuple(self.px[i:i + 3])
        return (0, 0, 0)

    def blend(self, x, y, color, a):
        # a in 0..1: paint color over existing pixel
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            for k in range(3):
                self.px[i + k] = int(self.px[i + k] * (1 - a) + color[k] * a)

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color)

    def hline(self, x, y, w, color):
        for xx in range(x, x + w):
            self.set(xx, y, color)

    def vline(self, x, y, h, color):
        for yy in range(y, y + h):
            self.set(x, yy, color)

    def line(self, x0, y0, x1, y1, color):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, color)

    def ring(self, cx, cy, r, t, color):
        for yy in range(cy - r - t, cy + r + t + 1):
            for xx in range(cx - r - t, cx + r + t + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if (r - t) ** 2 <= d2 <= (r + t) ** 2:
                    self.set(xx, yy, color)

    def ellipse(self, cx, cy, rx, ry, color):
        for yy in range(cy - ry, cy + ry + 1):
            for xx in range(cx - rx, cx + rx + 1):
                if ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1:
                    self.set(xx, yy, color)

    def ellipse_ring(self, cx, cy, rx, ry, t, color):
        for yy in range(cy - ry - t, cy + ry + t + 1):
            for xx in range(cx - rx - t, cx + rx + t + 1):
                v = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
                if (1 - t / max(rx, ry)) ** 2 <= v <= (1 + t / max(rx, ry)) ** 2:
                    self.set(xx, yy, color)

    def poly(self, pts, color):
        # scanline fill of a simple polygon
        ys = [p[1] for p in pts]
        for yy in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= yy < y1) or (y1 <= yy < y0):
                    xs.append(x0 + (yy - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                for xx in range(int(xs[i]), int(xs[i + 1]) + 1):
                    self.set(xx, yy, color)

    def text(self, x, y, s, color, scale=1, hs=1, vs=1):
        # hs/vs: independent horizontal/vertical scale (MRZ uses hs=1, vs=2)
        cx = x
        for ch in s.upper():
            g = FONT.get(ch, FONT[' '])
            for r in range(7):
                for c in range(5):
                    if g[r][c] == '1':
                        for dy in range(vs * scale):
                            for dx in range(hs * scale):
                                self.set(cx + c * hs * scale + dx,
                                         y + r * vs * scale + dy, color)
            cx += 5 * hs * scale + scale
        return cx

    def text_center(self, cx, y, s, color, scale=1):
        w = text_width(s, scale)
        self.text(cx - w // 2, y, s, color, scale)
        return w

    def blit_rotated(self, src, cx, cy, angle_deg, alpha=0.85, key=None):
        # paste src canvas rotated by angle_deg around its centre onto (cx, cy)
        ang = math.radians(angle_deg)
        ca, sa = math.cos(ang), math.sin(ang)
        sw, sh = src.w, src.h
        for yy in range(sh):
            for xx in range(sw):
                col = src.get(xx, yy)
                if key is not None and col == key:
                    continue
                dx, dy = xx - sw / 2, yy - sh / 2
                rx = int(cx + dx * ca - dy * sa)
                ry = int(cy + dx * sa + dy * ca)
                self.blend(rx, ry, col, alpha)


def png_bytes(cv):
    raw = b''.join(b'\x00' + bytes(cv.px[y * cv.w * 3:(y + 1) * cv.w * 3])
                   for y in range(cv.h))

    def chunk(tag, data):
        c = struct.pack('>I', len(data)) + tag + data
        return c + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)

    ihdr = struct.pack('>IIBBBBB', cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr)
            + chunk(b'IDAT', zlib.compress(raw, 9))
            + chunk(b'IEND', b''))


# ---------------------------------------------------------------- palette
DESK = (35, 39, 46)
PAGE = (244, 239, 228)
PAGE_LINE = (227, 220, 201)
INK = (28, 36, 48)
NAVY = (31, 58, 95)
TEAL = (14, 107, 107)
GOLD = (176, 138, 46)
GOLD_LT = (201, 164, 74)
GREY = (110, 112, 108)
SKIN = (217, 169, 134)
SKIN_DK = (198, 148, 112)
HAIR = (58, 42, 30)
JACKET = (31, 58, 95)
SHIRT = (246, 244, 238)
PHOTO_BG = (168, 182, 190)
STAMP_BLUE = (36, 71, 168)
STAMP_RED = (168, 35, 42)
STAMP_PURPLE = (91, 45, 142)
STAMP_GREEN = (30, 107, 52)
STAMP_BROWN = (122, 90, 32)

# ---------------------------------------------------------------- MRZ (ICAO 9303)
def _mrz_val(ch):
    if ch.isdigit():
        return int(ch)
    if ch == '<':
        return 0
    return ord(ch) - ord('A') + 10


def _mrz_check(s):
    w = (7, 3, 1)
    return str(sum(_mrz_val(c) * w[i % 3] for i, c in enumerate(s)) % 10)


def mrz_lines():
    line1 = ('P<VLMHALDEN<<MARA<ELIN').ljust(44, '<')
    doc, nat, dob, sex, exp = 'VM4829137', 'VLM', '880512', 'F', '340313'
    pers = '<' * 14
    body = (doc + _mrz_check(doc) + nat + dob + _mrz_check(dob) + sex
            + exp + _mrz_check(exp) + pers + _mrz_check(pers))
    line2 = body + _mrz_check(body)
    assert len(line1) == 44 and len(line2) == 44, (line1, line2)
    return line1, line2


def star_points(cx, cy, r_out, r_in, rot=-90):
    pts = []
    for i in range(10):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(rot + i * 36)
        pts.append((int(cx + r * math.cos(a)), int(cy + r * math.sin(a))))
    return pts


def coat_of_arms(cv, x, y, w, h):
    # shield with gold border, navy field, gold star, three waves
    pts = [(x, y), (x + w, y), (x + w, y + h - 12),
           (x + w // 2, y + h), (x, y + h - 12)]
    cv.poly(pts, NAVY)
    for i in range(len(pts)):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % len(pts)]
        cv.line(x0, y0, x1, y1, GOLD)
    cv.poly(star_points(x + w // 2, y + h // 2 - 6, 11, 4), GOLD)
    for k, yy in enumerate((y + h - 20, y + h - 14)):
        cv.line(x + 8, yy, x + w - 8, yy, (240, 238, 230))


def flag(cv, x, y, w, h):
    band = h // 3
    cv.rect(x, y, w, band, TEAL)
    cv.rect(x, y + band, w, band, (246, 244, 238))
    cv.rect(x, y + 2 * band, w, h - 2 * band, GOLD)
    cv.poly(star_points(x + w // 2, y + h // 2, 7, 3), NAVY)
    for i in range(4):
        cv.line(x, y + i * band, x + w, y + i * band, INK)


def portrait(cv, x, y, w, h):
    cv.rect(x, y, w, h, PHOTO_BG)
    for yy in range(y, y + h, 6):
        cv.hline(x, yy, w, (158, 172, 180))
    cx = x + w // 2
    # shoulders / jacket
    cv.poly([(x + 8, y + h), (x + w - 8, y + h), (x + w - 30, y + h - 78),
             (cx + 16, y + h - 66), (cx - 16, y + h - 66),
             (x + 30, y + h - 78)], JACKET)
    cv.poly([(cx - 16, y + h - 66), (cx + 16, y + h - 66),
             (cx, y + h - 40)], SHIRT)
    # neck
    cv.rect(cx - 15, y + h - 96, 30, 34, SKIN)
    cv.ellipse(cx, y + h - 62, 17, 8, SKIN_DK)
    # hair, then headscarf, then face
    cv.ellipse(cx, y + 78, 58, 64, HAIR)
    cv.ellipse(cx, y + 46, 66, 46, TEAL)
    cv.ellipse(cx, y + 104, 50, 62, SKIN)
    # scarf drapes over the shoulders
    cv.poly([(x + 6, y + 128), (cx - 34, y + 128), (cx - 26, y + h),
             (x + 2, y + h)], TEAL)
    cv.poly([(cx + 34, y + 128), (x + w - 6, y + 128), (x + w - 2, y + h),
             (cx + 26, y + h)], TEAL)
    # face
    cv.ellipse(cx - 21, y + 96, 5, 3, INK)
    cv.ellipse(cx + 21, y + 96, 5, 3, INK)
    cv.line(cx - 28, y + 86, cx - 14, y + 85, HAIR)
    cv.line(cx + 14, y + 85, cx + 28, y + 86, HAIR)
    cv.line(cx, y + 100, cx - 2, y + 118, SKIN_DK)
    cv.line(cx - 11, y + 138, cx + 11, y + 138, (150, 80, 70))
    cv.line(cx - 11, y + 139, cx + 11, y + 139, (150, 80, 70))
    # frame
    cv.rect(x, y, w, 2, NAVY)
    cv.rect(x, y + h - 2, w, 2, NAVY)
    cv.rect(x, y, 2, h, NAVY)
    cv.rect(x + w - 2, y, 2, h, NAVY)


def make_stamp(lines, color, w, h, oval=False, big=2):
    cv = Canvas(w, h, (255, 0, 255))
    if oval:
        cv.ellipse_ring(w // 2, h // 2, w // 2 - 4, h // 2 - 4, 2, color)
        cv.ellipse_ring(w // 2, h // 2, w // 2 - 10, h // 2 - 10, 1, color)
    else:
        cv.rect(2, 2, w - 4, 2, color)
        cv.rect(2, h - 4, w - 4, 2, color)
        cv.rect(2, 2, 2, h - 4, color)
        cv.rect(w - 4, 2, 2, h - 4, color)
        cv.rect(8, 8, w - 16, 1, color)
        cv.rect(8, h - 9, w - 16, 1, color)
        cv.rect(8, 8, 1, h - 16, color)
        cv.rect(w - 9, 8, 1, h - 16, color)
    y = (h - (len(lines) * 14 + (len(lines) - 1) * 6)) // 2
    for i, (txt, sc) in enumerate(lines):
        cv.text_center(w // 2, y, txt, color, sc)
        y += 7 * sc + 6
    return cv


def field(cv, x, y, label, value, width):
    cv.text(x, y, label, GREY, 1)
    cv.text(x, y + 10, value, INK, 2)


def guilloche(cv, x0, y0, x1, y1):
    for k in range(9):
        yy = y0 + 60 + k * 100
        if yy > y1 - 20:
            break
        for xx in range(x0, x1):
            if int(3 * math.sin(xx / 28.0)) == 0:
                cv.set(xx, yy + int(3 * math.sin(xx / 28.0)), PAGE_LINE)


def draw_data_page(cv):
    x0, y0, x1, y1 = 24, 36, 512, 988
    cv.rect(x0, y0, x1 - x0, y1 - y0, PAGE)
    guilloche(cv, x0 + 8, y0 + 8, x1 - 8, y1 - 8)
    # header
    coat_of_arms(cv, 48, 58, 42, 50)
    cv.text(102, 60, 'REPUBLIC OF VELMORA', NAVY, 3)
    cv.text(102, 92, 'PASSPORT', INK, 2)
    cv.text(102, 114, 'PASSEPORT - PASAPORTA', GREY, 1)
    cv.hline(48, 134, 420, NAVY)
    cv.hline(48, 137, 420, GOLD)
    # portrait + fields
    portrait(cv, 48, 152, 190, 250)
    fx = 256
    rows = [('SURNAME', 'HALDEN'), ('GIVEN NAMES', 'MARA ELIN'),
            ('NATIONALITY', 'VELMORAN'), ('DATE OF BIRTH', '12 MAY 1988'),
            ('PLACE OF BIRTH', 'PORT VELMORA'), ('SEX', 'F')]
    for i, (lab, val) in enumerate(rows):
        field(cv, fx, 152 + i * 42, lab, val, 236)
    # second block
    cv.hline(48, 420, 420, PAGE_LINE)
    grid = [('TYPE', 'P', 48), ('COUNTRY CODE', 'VLM', 168),
            ('PASSPORT NO.', 'VM4829137', 308)]
    for lab, val, gx in grid:
        field(cv, gx, 436, lab, val, 140)
    grid2 = [('DATE OF ISSUE', '14 MAR 2024', 48),
             ('DATE OF EXPIRY', '13 MAR 2034', 198)]
    for lab, val, gx in grid2:
        field(cv, gx, 484, lab, val, 150)
    field(cv, 48, 532, 'AUTHORITY', 'MINISTRY OF THE SEA', 420)
    cv.hline(48, 580, 420, PAGE_LINE)
    # observations — the telling paperwork detail
    cv.text(48, 596, 'OBSERVATIONS', GREY, 1)
    obs = ['HOLDER IS A REGISTERED SEAFARER OF THE',
           'MERIDIAN PACT. HARBOUR TAX PAID ANNUALLY.',
           'VISAS: NOT REQUIRED FOR SEAFARERS OF THE',
           'MERIDIAN PACT (ALBIONA, KORVATH, TALMAR).',
           'HEIGHT 172 CM - EYES BROWN - EMERGENCY',
           'CONTACT: MINISTRY OF THE SEA, PORT VELMORA.']
    for i, ln in enumerate(obs):
        cv.text(48, 614 + i * 12, ln, INK, 1)
    # signature + seal
    cv.text(48, 706, 'M. HALDEN', INK, 2)
    cv.line(48, 728, 200, 728, INK)
    cv.text(48, 736, "HOLDER'S SIGNATURE", GREY, 1)
    cv.ring(398, 722, 62, 2, GOLD)
    cv.ring(398, 722, 54, 1, GOLD)
    cv.text_center(398, 684, 'REPUBLIC', GOLD, 1)
    cv.text_center(398, 696, 'OF VELMORA', GOLD, 1)
    cv.poly(star_points(398, 722, 12, 5), GOLD)
    cv.text_center(398, 748, 'MINISTRY', GOLD, 1)
    cv.text_center(398, 760, 'OF THE SEA', GOLD, 1)
    # MRZ
    cv.rect(48, 812, 420, 62, (232, 226, 210))
    l1, l2 = mrz_lines()
    cv.text(136, 824, l1, INK, 1, hs=1, vs=2)
    cv.text(136, 846, l2, INK, 1, hs=1, vs=2)


def draw_visa_page(cv):
    x0, y0, x1, y1 = 512, 36, 1000, 988
    cv.rect(x0, y0, x1 - x0, y1 - y0, PAGE)
    guilloche(cv, x0 + 8, y0 + 8, x1 - 8, y1 - 8)
    cv.text_center(756, 54, 'VISAS', GREY, 2)
    cv.hline(540, 82, 432, PAGE_LINE)
    # Talmar visa sticker
    vx, vy, vw, vh = 540, 96, 432, 156
    cv.rect(vx, vy, vw, vh, (253, 251, 245))
    cv.rect(vx, vy, vw, 3, NAVY)
    cv.rect(vx, vy + vh - 3, vw, 3, NAVY)
    cv.rect(vx, vy, 3, vh, NAVY)
    cv.rect(vx + vw - 3, vy, 3, vh, NAVY)
    flag(cv, vx + 14, vy + 14, 66, 40)
    cv.text(vx + 96, vy + 16, 'VISA - TALMAR', NAVY, 2)
    cv.text(vx + 96, vy + 38, 'SINGLE ENTRY - 30 DAYS', INK, 1)
    cv.text(vx + 14, vy + 66, 'ISSUED: 11 JAN 2025 - PORT VELMORA', INK, 1)
    cv.text(vx + 14, vy + 84, 'VALID UNTIL: 10 FEB 2025', INK, 1)
    cv.text(vx + 14, vy + 102, 'FEE: 40 TAL - PAID', INK, 1)
    cv.text(vx + 14, vy + 120, 'NO. TV-2025-01184', INK, 1)
    # stamps, two rows
    s1 = make_stamp([('ALBIONA', 2), ('ARRIVED', 1), ('02 JUN 2024', 1)],
                    STAMP_BLUE, 220, 110, oval=True)
    cv.blit_rotated(s1, 650, 330, -8, 0.85, key=(255, 0, 255))
    s2 = make_stamp([('KORVATH', 2), ('DEPARTED', 1), ('18 SEP 2024', 1)],
                    STAMP_RED, 220, 110, oval=False)
    cv.blit_rotated(s2, 862, 330, 6, 0.85, key=(255, 0, 255))
    s3 = make_stamp([('ALBIONA', 2), ('ARRIVED', 1), ('11 JAN 2025', 1)],
                    STAMP_PURPLE, 220, 110, oval=True)
    cv.blit_rotated(s3, 650, 466, 5, 0.85, key=(255, 0, 255))
    s4 = make_stamp([('TALMAR', 2), ('DEPARTED', 1), ('28 JAN 2025', 1)],
                    STAMP_GREEN, 220, 110, oval=False)
    cv.blit_rotated(s4, 862, 466, -7, 0.85, key=(255, 0, 255))
    # harbour-tax seal
    seal = Canvas(190, 190, (255, 0, 255))
    seal.ring(95, 95, 88, 3, STAMP_BROWN)
    seal.ring(95, 95, 78, 1, STAMP_BROWN)
    seal.text_center(95, 34, 'HARBOUR TAX', STAMP_BROWN, 1)
    seal.text_center(95, 48, 'PAID', STAMP_BROWN, 2)
    seal.poly(star_points(95, 100, 16, 6), STAMP_BROWN)
    seal.text_center(95, 128, '12.50 VLM', STAMP_BROWN, 1)
    seal.text_center(95, 144, '2025', STAMP_BROWN, 1)
    cv.blit_rotated(seal, 756, 640, -12, 0.85, key=(255, 0, 255))
    # Meridian Pact entry permit
    p = make_stamp([('MERIDIAN PACT', 2),
                    ('SEAFARER ENTRY PERMITTED - 90 DAYS', 1),
                    ('ISSUED WITH PASSPORT - 14 MAR 2024', 1)],
                   TEAL, 432, 84, oval=False)
    cv.blit_rotated(p, 756, 790, -2, 0.85, key=(255, 0, 255))
    # compass rose, faint, bottom left
    cv.ring(590, 900, 40, 1, PAGE_LINE)
    cv.line(590, 852, 590, 948, PAGE_LINE)
    cv.line(542, 900, 638, 900, PAGE_LINE)
    cv.text(586, 856, 'N', GREY, 1)
    cv.text(586, 930, 'S', GREY, 1)
    cv.text(544, 896, 'W', GREY, 1)
    cv.text(630, 896, 'E', GREY, 1)
    cv.text(920, 956, 'PAGE 4', GREY, 1)


def main():
    cv = Canvas(W, H, DESK)
    # soft shadow under the spread
    cv.rect(30, 42, 976, 952, (22, 25, 30))
    draw_data_page(cv)
    draw_visa_page(cv)
    # gutter shadow
    for i in range(8):
        cv.vline(508 + i, 36, 952, (200 - i * 12, 194 - i * 12, 180 - i * 12))
    cv.vline(511, 36, 952, (120, 114, 100))
    out = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, 'entry.png')
    with open(path, 'wb') as f:
        f.write(png_bytes(cv))
    print('wrote', path, os.path.getsize(path), 'bytes')


if __name__ == '__main__':
    main()
