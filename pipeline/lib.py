"""Primitivas de dibujo de En Cristiano (colores, personajes, objetos)."""
import math, cairo
W, H, FPS = 1080, 1920, 30
FONT = "Poppins"
INK = (0x2F/255, 0x2F/255, 0x3D/255)
def hx(h): h = h.lstrip('#'); return tuple(int(h[i:i+2], 16)/255 for i in (0, 2, 4))
CREAM, MINT, ROSE, SKY, LAV, PEACH, YEL = map(hx, ["FFF6EC", "BDE8D0", "F8C8D4", "C6E2F5", "DCCFF3", "FFD8B5", "FFE7A3"])
GREEN, RED, HIL, WHITE, SKIN = hx("4FB386"), hx("E57C7C"), hx("FFD84D"), (1, 1, 1), hx("FFD8B5")
FONT = "Poppins"

# ---------- utilidades ----------
def clamp(x, a=0, b=1): return max(a, min(b, x))
def ease_out_back(p):
    c1 = 1.70158; c3 = c1 + 1; p = clamp(p)
    return 1 + c3 * (p - 1) ** 3 + c1 * (p - 1) ** 2
def ease_out(p): p = clamp(p); return 1 - (1 - p) ** 3
def pop(t, t0, d=0.35): return 0 if t < t0 else ease_out_back((t - t0) / d)
def appear(t, t0, d=0.25): return ease_out((t - t0) / d) if t >= t0 else 0

def rrect(c, x, y, w, h, r):
    c.new_sub_path()
    c.arc(x + w - r, y + r, r, -math.pi/2, 0); c.arc(x + w - r, y + h - r, r, 0, math.pi/2)
    c.arc(x + r, y + h - r, r, math.pi/2, math.pi); c.arc(x + r, y + r, r, math.pi, 1.5*math.pi)
    c.close_path()
def fs(c, fill, lw=8, stroke=INK):
    if fill is not None:
        c.set_source_rgb(*fill); c.fill_preserve()
    c.set_source_rgb(*stroke); c.set_line_width(lw); c.stroke()
def font(c, size, bold=True):
    c.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    c.set_font_size(size)
def text(c, s, x, y, size, color=INK, anchor="c", stroke=None, sw=10):
    font(c, size); e = c.text_extents(s)
    tx = x - e.x_advance/2 if anchor == "c" else (x if anchor == "l" else x - e.x_advance)
    ty = y + size*0.35
    c.move_to(tx, ty); c.text_path(s)
    if stroke:
        c.set_source_rgb(*stroke); c.set_line_width(sw); c.set_line_join(cairo.LINE_JOIN_ROUND); c.stroke_preserve()
    c.set_source_rgb(*color); c.fill()
    return e.x_advance
def scaled(c, x, y, s):
    """Contexto escalado alrededor de (x, y)."""
    s = max(s, 0.001); c.save(); c.translate(x, y); c.scale(s, s); c.translate(-x, -y)

def pill(c, s, x, y, size, bg, fg, anchor="c", pad=26):
    font(c, size); e = c.text_extents(s); w = e.x_advance + 2*pad; h = size*1.55
    x0 = x - w/2 if anchor == "c" else x
    rrect(c, x0, y - h/2, w, h, h/2); fs(c, bg, 6)
    text(c, s, x0 + w/2, y, size, fg)
    return w

# ---------- personajes y objetos ----------
def face(c, x, y, r, mood="happy", glasses=False):
    c.set_source_rgb(*INK)
    ex = r*0.36
    for sx in (-1, 1):
        c.arc(x + sx*ex, y - r*0.05, r*0.09, 0, 2*math.pi); c.fill()
    c.set_source_rgb(*hx("F8C8D4"))
    for sx in (-1, 1):
        c.save(); c.translate(x + sx*r*0.55, y + r*0.28); c.scale(1, 0.62); c.arc(0, 0, r*0.17, 0, 2*math.pi); c.restore(); c.fill()
    c.set_source_rgb(*INK); c.set_line_width(max(4, r*0.09)); c.set_line_cap(cairo.LINE_CAP_ROUND)
    if mood == "happy":
        c.arc(x, y + r*0.12, r*0.33, 0.15*math.pi, 0.85*math.pi); c.stroke()
    elif mood == "big":
        c.arc(x, y + r*0.1, r*0.36, 0, math.pi); c.close_path(); c.set_source_rgb(*hx("E57C7C")); c.fill_preserve()
        c.set_source_rgb(*INK); c.stroke()
    elif mood == "sad":
        c.arc(x, y + r*0.55, r*0.28, 1.2*math.pi, 1.8*math.pi); c.stroke()
    elif mood == "o":
        c.arc(x, y + r*0.38, r*0.14, 0, 2*math.pi); c.stroke()
    if glasses:
        c.set_line_width(max(4, r*0.08))
        for sx in (-1, 1):
            c.arc(x + sx*ex, y - r*0.05, r*0.26, 0, 2*math.pi); c.stroke()
        c.move_to(x - ex + r*0.26, y - r*0.08); c.line_to(x + ex - r*0.26, y - r*0.08); c.stroke()

def mascot(c, x, y, r):
    """La cara de la foto de perfil."""
    c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.move_to(x - r*0.26, y - r*0.92); c.curve_to(x - r*0.2, y - r*1.25, x - r*0.05, y - r*1.05, x, y - r*1.05)
    c.curve_to(x + r*0.05, y - r*1.3, x + r*0.22, y - r*1.12, x + r*0.28, y - r*0.92); fs(c, SKIN, r*0.06)
    c.arc(x, y, r, 0, 2*math.pi); fs(c, SKIN, r*0.07)
    face(c, x, y, r, "happy", glasses=True)

def person(c, x, y, s=1.0, head=PEACH, mood="happy", arms="down", d=1, hat=False, bounce=0):
    """Monigote. (x, y) = centro de la cabeza. Devuelve la posición de la mano delantera."""
    y -= bounce
    c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.set_source_rgb(*INK); c.set_line_width(11*s)
    neck = y + 62*s; hip = y + 210*s
    c.move_to(x, neck); c.line_to(x, hip); c.stroke()
    for sx in (-1, 1):
        c.move_to(x, hip); c.line_to(x + sx*42*s, hip + 105*s + bounce*0.0); c.stroke()
    sh = y + 100*s
    hand = None
    if arms == "down":
        for sx in (-1, 1): c.move_to(x, sh); c.line_to(x + sx*55*s, sh + 85*s); c.stroke()
    elif arms == "up":
        for sx in (-1, 1): c.move_to(x, sh); c.line_to(x + sx*70*s, sh - 85*s); c.stroke()
    elif arms == "hold":
        c.move_to(x, sh); c.line_to(x - d*55*s, sh + 85*s); c.stroke()
        c.move_to(x, sh); c.line_to(x + d*45*s, sh + 40*s); c.line_to(x + d*95*s, sh + 20*s); c.stroke()
        hand = (x + d*110*s, sh + 5*s)
    elif arms == "wave":
        c.move_to(x, sh); c.line_to(x - d*55*s, sh + 85*s); c.stroke()
        c.move_to(x, sh); c.line_to(x + d*75*s, sh - 80*s); c.stroke()
    elif arms == "point":
        c.move_to(x, sh); c.line_to(x - d*55*s, sh + 85*s); c.stroke()
        c.move_to(x, sh); c.line_to(x + d*110*s, sh - 10*s); c.stroke()
        hand = (x + d*110*s, sh - 10*s)
    c.arc(x, y, 62*s, 0, 2*math.pi); fs(c, head, 9*s)
    face(c, x, y, 62*s, mood)
    if hat:  # gorro de panadero
        c.move_to(x - 48*s, y - 50*s)
        c.curve_to(x - 85*s, y - 120*s, x - 30*s, y - 160*s, x, y - 130*s)
        c.curve_to(x + 30*s, y - 165*s, x + 90*s, y - 120*s, x + 48*s, y - 50*s); c.close_path(); fs(c, WHITE, 8*s)
    return hand

def chicken(c, x, y, s=1.0, mood="happy"):
    c.set_line_join(cairo.LINE_JOIN_ROUND); c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.set_source_rgb(*hx("F2A65A")); c.set_line_width(7*s)
    for dx in (-18, 18):
        c.move_to(x + dx*s, y + 45*s); c.line_to(x + dx*s, y + 80*s); c.stroke()
    c.save(); c.translate(x, y); c.scale(1, 0.8); c.arc(0, 0, 70*s, 0, 2*math.pi); c.restore(); fs(c, WHITE, 8*s)
    c.move_to(x - 62*s, y - 10*s); c.line_to(x - 105*s, y - 40*s); c.line_to(x - 90*s, y + 5*s); c.close_path(); fs(c, WHITE, 7*s)
    hx_, hy = x + 50*s, y - 55*s
    for i, dx in enumerate((-14, 0, 14)):
        c.arc(hx_ + dx*s, hy - 38*s - (6 if i == 1 else 0)*s, 13*s, 0, 2*math.pi); fs(c, hx("E57C7C"), 5*s)
    c.arc(hx_, hy, 38*s, 0, 2*math.pi); fs(c, WHITE, 8*s)
    c.move_to(hx_ + 32*s, hy - 6*s); c.line_to(hx_ + 62*s, hy + 4*s); c.line_to(hx_ + 32*s, hy + 14*s); c.close_path(); fs(c, hx("F2A65A"), 5*s)
    c.set_source_rgb(*INK); c.arc(hx_ + 10*s, hy - 6*s, 6*s, 0, 2*math.pi); c.fill()
    if mood == "sad":
        c.set_line_width(5*s); c.move_to(hx_ - 4*s, hy - 22*s); c.line_to(hx_ + 20*s, hy - 16*s); c.stroke()
    c.move_to(x - 30*s, y - 5*s); c.curve_to(x - 10*s, y + 25*s, x + 25*s, y + 20*s, x + 30*s, y - 5*s)
    c.set_source_rgb(*INK); c.set_line_width(6*s); c.stroke()

def bread(c, x, y, s=1.0):
    c.save(); c.translate(x, y); c.rotate(-0.2); c.scale(1, 0.5); c.arc(0, 0, 80*s, 0, 2*math.pi); c.restore(); fs(c, hx("E8B77A"), 8*s)
    c.set_source_rgb(*INK); c.set_line_width(6*s); c.set_line_cap(cairo.LINE_CAP_ROUND)
    for dx in (-35, 0, 35):
        c.move_to(x + dx*s - 10*s, y + 10*s - dx*0.2*s); c.line_to(x + dx*s + 12*s, y - 18*s - dx*0.2*s); c.stroke()

def coin(c, x, y, r, spin=1.0, smile=True, sym="€"):
    sx = max(0.08, abs(spin))
    c.save(); c.translate(x, y); c.scale(sx, 1)
    c.arc(0, 0, r, 0, 2*math.pi); c.restore(); fs(c, HIL, max(6, r*0.08))
    c.save(); c.translate(x, y); c.scale(sx, 1); c.arc(0, 0, r*0.78, 0, 2*math.pi); c.restore()
    c.set_source_rgb(*hx("E8B830")); c.set_line_width(max(3, r*0.05)); c.stroke()
    if sx > 0.6:
        if smile:
            c.save(); c.translate(x, y); c.scale(sx, 1); face(c, 0, -r*0.05, r*0.75, "happy"); c.restore()
        else:
            text(c, sym, x, y, r*1.0, hx("C8941E"))

def shell(c, x, y, s=1.0):
    c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.move_to(x, y + 70*s)
    for i in range(7):
        a0 = math.pi*(1.1 + i*0.8/7); a1 = math.pi*(1.1 + (i+1)*0.8/7)
        c.line_to(x + 85*s*math.cos(a0), y + 30*s + 85*s*math.sin(a0))
        c.curve_to(x + 100*s*math.cos((a0+a1)/2), y + 30*s + 100*s*math.sin((a0+a1)/2),
                   x + 100*s*math.cos((a0+a1)/2), y + 30*s + 100*s*math.sin((a0+a1)/2),
                   x + 85*s*math.cos(a1), y + 30*s + 85*s*math.sin(a1))
    c.close_path(); fs(c, ROSE, 7*s)
    c.set_line_width(5*s)
    for i in range(1, 7):
        a = math.pi*(1.1 + i*0.8/7)
        c.move_to(x, y + 62*s); c.line_to(x + 82*s*math.cos(a), y + 30*s + 82*s*math.sin(a)); c.stroke()

def note(c, x, y, w, h, label="50", rot=0):
    c.save(); c.translate(x, y); c.rotate(rot)
    rrect(c, -w/2, -h/2, w, h, h*0.12); fs(c, hx("BFE3C4"), 9)
    rrect(c, -w/2 + h*0.1, -h/2 + h*0.1, w - h*0.2, h*0.8, h*0.08)
    c.set_source_rgb(*hx("7FBF8C")); c.set_line_width(5); c.stroke()
    c.arc(w*0.18, 0, h*0.27, 0, 2*math.pi); fs(c, hx("DFF2E2"), 6, hx("7FBF8C"))
    text(c, label, -w*0.2, 0, h*0.42, hx("3E8E55"))
    text(c, "€", w*0.18, 0, h*0.3, hx("3E8E55"))
    c.restore()

def phone(c, x, y, s, amount):
    rrect(c, x - 75*s, y - 130*s, 150*s, 260*s, 26*s); fs(c, hx("3A3A4A"), 8*s)
    rrect(c, x - 60*s, y - 108*s, 120*s, 205*s, 14*s); fs(c, WHITE, 4*s)
    text(c, amount, x, y - 10*s, 30*s, GREEN)
    c.set_source_rgb(*hx("E0E0E8"))
    for i in range(2):
        rrect(c, x - 45*s, y + 25*s + i*30*s, 90*s, 16*s, 8*s); c.fill()

def heart(c, x, y, s, color=RED):
    c.move_to(x, y + 30*s)
    c.curve_to(x - 70*s, y - 15*s, x - 35*s, y - 65*s, x, y - 30*s)
    c.curve_to(x + 35*s, y - 65*s, x + 70*s, y - 15*s, x, y + 30*s); c.close_path(); fs(c, color, 6*s)

def sparkle(c, x, y, s, color=HIL):
    c.move_to(x, y - 30*s)
    for i in range(4):
        a = math.pi/2*i
        c.curve_to(x + 5*s*math.cos(a + math.pi/4)*1.2, y - 5*s*math.sin(a+math.pi/4)*-1.2,
                   x + 5*s*math.cos(a + math.pi/4)*1.2, y + 5*s*math.sin(a+math.pi/4)*1.2,
                   x + 30*s*math.cos(a + math.pi/2 - math.pi/2 + math.pi/2), y + 30*s*math.sin(a + math.pi/2))
    c.close_path(); fs(c, color, 4*s)

def star4(c, x, y, s, color=HIL):
    c.move_to(x, y - 32*s); c.line_to(x + 9*s, y - 9*s); c.line_to(x + 32*s, y); c.line_to(x + 9*s, y + 9*s)
    c.line_to(x, y + 32*s); c.line_to(x - 9*s, y + 9*s); c.line_to(x - 32*s, y); c.line_to(x - 9*s, y - 9*s); c.close_path()
    fs(c, color, 4*s)

def bubble(c, x, y, w, h, s_txt, size=40, tail=(-1, 1)):
    rrect(c, x - w/2, y - h/2, w, h, 30)
    c.set_source_rgb(*WHITE); c.fill_preserve(); c.set_source_rgb(*INK); c.set_line_width(7); c.stroke()
    tx = x + tail[0]*w*0.25
    c.move_to(tx - 22, y + h/2 - 4); c.line_to(tx + tail[0]*10, y + h/2 + 45); c.line_to(tx + 22, y + h/2 - 4)
    c.set_source_rgb(*WHITE); c.fill_preserve(); c.set_source_rgb(*INK); c.stroke()
    c.rectangle(tx - 18, y + h/2 - 12, 36, 10); c.set_source_rgb(*WHITE); c.fill()
    text(c, s_txt, x, y, size)

def xmark(c, x, y, s, p=1):
    c.set_source_rgb(*RED); c.set_line_width(26*s); c.set_line_cap(cairo.LINE_CAP_ROUND)
    L = 70*s
    c.move_to(x - L, y - L); c.line_to(x - L + 2*L*clamp(p*2), y - L + 2*L*clamp(p*2)); c.stroke()
    if p > 0.5:
        q = clamp((p - 0.5)*2); c.move_to(x + L, y - L); c.line_to(x + L - 2*L*q, y - L + 2*L*q); c.stroke()

def arrow(c, x0, y0, x1, y1, bend=-80, p=1, color=INK, lw=10):
    mx, my = (x0 + x1)/2, (y0 + y1)/2 + bend
    pts = []
    for i in range(41):
        u = i/40*p
        pts.append(((1-u)**2*x0 + 2*(1-u)*u*mx + u*u*x1, (1-u)**2*y0 + 2*(1-u)*u*my + u*u*y1))
    c.set_source_rgb(*color); c.set_line_width(lw); c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.move_to(*pts[0])
    for pt in pts[1:]: c.line_to(*pt)
    c.stroke()
    if p > 0.95:
        (ax, ay), (bx, by) = pts[-2], pts[-1]
        a = math.atan2(by - ay, bx - ax)
        for da in (2.6, -2.6):
            c.move_to(bx, by); c.line_to(bx + 30*math.cos(a + da), by + 30*math.sin(a + da)); c.stroke()

def drop(c, x, y, s):
    c.move_to(x, y - 25*s); c.curve_to(x + 22*s, y, x + 18*s, y + 22*s, x, y + 22*s)
    c.curve_to(x - 18*s, y + 22*s, x - 22*s, y, x, y - 25*s); fs(c, SKY, 4*s)

def banner(c, s_txt, x, y, size, bg, p):
    if p <= 0: return
    scaled(c, x, y, p)
    c.save(); c.translate(x, y); c.rotate(-0.04); c.translate(-x, -y)
    pill(c, s_txt, x, y, size, bg, INK, pad=34)
    c.restore(); c.restore()

