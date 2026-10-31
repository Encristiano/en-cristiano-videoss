"""Escenas a medida del episodio 1."""
import math
from lib import *

def sc_trueque(c, t, i):
    tg = at(i, "gallina"); tp = at(i, "pan"); tt = at(i, "trueque")
    ta = pop(t, 0.05); tb = pop(t, 0.2)
    if t < at(i, "gente"):
        q = pop(t, 0.0)
        scaled(c, CX, 640, q); pill(c, "⏳ HACE MILES DE AÑOS".replace("⏳ ", ""), CX, 640, 44, WHITE, INK); c.restore()
    scaled(c, 260, 820, ta); person(c, 260, 740, 1.0, PEACH, "happy", "hold", d=1, bounce=abs(math.sin(t*5))*8); c.restore()
    scaled(c, 800, 820, tb); person(c, 800, 740, 1.0, LAV, "happy", "hold", d=-1, hat=True, bounce=abs(math.sin(t*5 + 1))*8); c.restore()
    q = pop(t, tg - 0.15)
    if q > 0: scaled(c, 400, 860, q); chicken(c, 400, 860, 0.8); c.restore()
    q = pop(t, tp - 0.15)
    if q > 0: scaled(c, 660, 860, q); bread(c, 660, 860, 0.9); c.restore()
    ap = clamp((t - (tp + 0.1))/0.5)
    if ap > 0:
        arrow(c, 420, 760, 640, 760, bend=-110, p=ap, color=hx("3E8E55"))
        arrow(c, 640, 990, 420, 990, bend=110, p=ap, color=hx("3E8E55"))
    q = pop(t, tt - 0.1)
    if q > 0 and t >= at(i, "gente"):
        banner(c, "TRUEQUE", CX, 600, 64, HIL, q)

def sc_problema(c, t, i):
    tpd = at(i, "panadero"); tsin = at(i, "sin")
    sad = t >= tsin
    person(c, 260, 740, 1.0, PEACH, "sad" if sad else "o", "hold", d=1)
    person(c, 800, 740, 1.0, LAV, "sad" if t > tpd + 0.3 else "happy", "down", d=-1, hat=True)
    chicken(c, 400, 860 + (10*math.sin(t*20) if sad else 0), 0.8, "sad" if sad else "happy")
    if t < tpd - 0.05:
        q = pop(t, 0.05)
        if q > 0: scaled(c, CX, 600, q); text(c, "¿EL PROBLEMA?", CX, 600, 70, WHITE, stroke=INK, sw=16); c.restore()
    q = pop(t, tpd)
    if q > 0:
        scaled(c, 720, 560, q); bubble(c, 720, 560, 470, 110, "¡No quiero gallinas!", 40, tail=(1, 1)); c.restore()
        c.save(); c.translate(720 + 230 - 470*0.25 + 0, 0); c.restore()
        # cabeza que dice que no
    if t > tpd:
        pass
    q = pop(t, tsin - 0.1)
    if q > 0:
        bread(c, 660, 1010, 0.9)
        scaled(c, 660, 1010, q); xmark(c, 660, 1010, 0.8, clamp((t - tsin + 0.1)/0.4)); c.restore()
        drop(c, 340, 690 + 20*((t*2) % 1), 1.0)

def sc_invento(c, t, i):
    td = at(i, "dinero"); tac = at(i, "acepta")
    jump = abs(math.sin(t*7))*30 if t > td else 0
    person(c, 220, 760, 0.9, PEACH, "big" if t > td else "o", "up" if t > td else "down", bounce=jump)
    person(c, 860, 760, 0.9, LAV, "big" if t > td else "o", "up" if t > td else "down", hat=True, bounce=abs(math.sin(t*7 + 1))*30 if t > td else 0)
    q = pop(t, min(td, tac) - 0.15, 0.45)
    if q > 0:
        scaled(c, CX, 820, q); coin(c, CX, 820 + 10*math.sin(t*4), 150, spin=1, smile=True); c.restore()
        for k in range(6):
            a = t*1.5 + k*math.pi/3
            star4(c, CX + 230*math.cos(a), 820 + 200*math.sin(a), 0.7 + 0.2*math.sin(t*6 + k))
    if t < tac - 0.1:
        q = pop(t, 0.0)
        scaled(c, CX, 590, q); text(c, "INVENTAMOS ALGO…", CX, 590, 64, WHITE, stroke=INK, sw=16); c.restore()
    banner(c, "¡TODOS LO ACEPTAN!", CX, 1100, 56, HIL, pop(t, tac))

def sc_evolucion(c, t, i):
    keys = ["conchas", "monedas", "billetes", "pantalla"]
    xs = [180, 413, 646, 880]; y = 800
    times = [at(i, k) - 0.2 for k in keys]
    labels = ["CONCHAS", "MONEDAS", "BILLETES", "PANTALLA"]
    eras = ["hace milenios", "antigüedad", "siglos atrás", "hoy"]
    for k in range(4):
        q = pop(t, times[k])
        if q <= 0: continue
        if k > 0:
            arrow(c, xs[k-1] + 70, y - 10, xs[k] - 70, y - 10, bend=-40, p=clamp((t - times[k])/0.3), lw=8)
        scaled(c, xs[k], y, q)
        bob = 6*math.sin(t*5 + k)
        if k == 0: shell(c, xs[k], y - 40 + bob, 0.85)
        elif k == 1:
            coin(c, xs[k] - 20, y + 10 + bob, 52, smile=False); coin(c, xs[k] + 22, y - 25 + bob, 52, smile=False)
        elif k == 2: note(c, xs[k], y + bob, 190, 100, "10", rot=-0.1)
        else:
            amt = 1250*clamp((t - times[3])/1.2)
            phone(c, xs[k], y + bob, 0.85, f"{amt:,.0f} €".replace(",", "."))
        c.restore()
        text(c, labels[k], xs[k], y + 165, 34, INK)
        text(c, eras[k], xs[k], y + 210, 28, hx("6B6B80"), )
    if t < times[0] + 0.05:
        pass
    q = pop(t, 0.0)
    scaled(c, CX, 610, q); text(c, "ASÍ HA CAMBIADO", CX, 610, 64, WHITE, stroke=INK, sw=16); c.restore()
    tp = times[3]
    if t > tp + 0.6:
        banner(c, "¡CASI TODO DIGITAL!", CX, 1110, 50, HIL, pop(t, tp + 0.6))

def sc_billete(c, t, i):
    tb = at(i, "billete"); tpap = at(i, "papel"); tconf = at(i, "confiamos")
    q = pop(t, max(0, tb - 0.2), 0.45)
    if q > 0:
        scaled(c, CX, 790, q)
        note(c, CX, 790 + 8*math.sin(t*3), 520, 270, "50", rot=-0.05 + 0.03*math.sin(t*2))
        c.restore()
    if t < tpap - 0.1:
        q = pop(t, 0.0); scaled(c, CX, 590, q); text(c, "LO CURIOSO…", CX, 590, 64, WHITE, stroke=INK, sw=16); c.restore()
    if tpap - 0.1 <= t < tconf - 0.2:
        mx = CX - 160 + 320*clamp((t - tpap)/1.2)
        c.set_source_rgb(*INK); c.set_line_width(22); c.set_line_cap(cairo.LINE_CAP_ROUND)
        c.move_to(mx + 70, 860); c.line_to(mx + 140, 940); c.stroke()
        c.arc(mx, 800, 95, 0, 2*math.pi); c.set_source_rgba(1, 1, 1, 0.45); c.fill_preserve()
        c.set_source_rgb(*INK); c.set_line_width(14); c.stroke()
        banner(c, "SOLO PAPEL", CX, 1090, 56, WHITE, pop(t, tpap))
    if t >= tconf - 0.2:
        for k in range(5):
            hp = (t - tconf + 0.2 - k*0.15)
            if hp > 0:
                yy = 1000 - (hp*220) % 420; xx = 200 + k*170
                heart(c, xx, yy, 0.7 + 0.15*math.sin(t*6 + k))
        banner(c, "VALE POR CONFIANZA", CX, 1090, 50, HIL, pop(t, tconf))

def sc_acuerdo(c, t, i):
    q = pop(t, 0.0, 0.45)
    scaled(c, CX, 860, q)
    coin(c, CX, 860, 105, smile=True)
    heads = [PEACH, LAV, MINT, ROSE, SKY, YEL]
    n = 6
    for k in range(n):
        a = -math.pi/2 + k*2*math.pi/n + t*0.4
        px, py = CX + 300*math.cos(a), 860 + 180*math.sin(a)
        c.arc(px, py, 52, 0, 2*math.pi); fs(c, heads[k], 8); face(c, px, py, 52, "happy")
    for k in range(n):
        a = -math.pi/2 + (k + 0.5)*2*math.pi/n + t*0.4
        heart(c, CX + 300*math.cos(a), 860 + 180*math.sin(a), 0.38 + 0.08*math.sin(t*8 + k))
    c.restore()
    banner(c, "ACUERDO DE CONFIANZA", CX, 1165, 52, HIL, pop(t, at(i, "acuerdo") - 0.1))
    q = pop(t, 0.0); scaled(c, CX, 590, q); text(c, "EN RESUMEN", CX, 590, 64, WHITE, stroke=INK, sw=16); c.restore()

