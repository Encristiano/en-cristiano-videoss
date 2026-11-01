"""Motor de vídeo de En Cristiano.
Uso:
  python3 engine.py voice  <ep>            -> genera la voz por escenas
  python3 engine.py preview <ep> t1,t2,...  -> fotogramas de prueba
  python3 engine.py build  <ep>            -> vídeo final en out/<slug>.mp4
"""
import math, os, sys, io, wave, json, subprocess
import numpy as np, soundfile as sf, cairo
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from lib import *
import custom_ep01
from episodios import EPISODES

OUT = os.path.join(HERE, "out")
GAP = 0.12
SAY = {"IRPF": "i erre pe efe", "UE": "u e", "IPC": "i pe ce", "BCE": "be ce e", "INE": "ine"}
COLORS = dict(YEL=YEL, MINT=MINT, ROSE=ROSE, SKY=SKY, LAV=LAV, PEACH=PEACH, HIL=HIL, GREEN=GREEN, RED=RED)
CARD = (60, 470, 960, 760)
CX, CY = CARD[0] + CARD[2]/2, CARD[1] + CARD[3]/2
SUB_Y = 1335
GREY = hx("6B6B80")

# ======================================================== VOZ
def spoken(txt):
    for k, v in SAY.items(): txt = txt.replace(k, v)
    return txt

def make_voice(ep):
    from piper import PiperVoice, SynthesisConfig
    d = "/home/claude/tts/vits-piper-es_ES-davefx-medium"
    v = PiperVoice.load(f"{d}/es_ES-davefx-medium.onnx")
    cfg = SynthesisConfig(length_scale=0.82, noise_scale=0.85, noise_w_scale=1.0)
    vd = os.path.join(OUT, ep["slug"], "voz"); os.makedirs(vd, exist_ok=True)
    for i, (txt, _) in enumerate(ep["scenes"]):
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w: v.synthesize_wav(spoken(txt), w, syn_config=cfg)
        buf.seek(0); x, sr = sf.read(buf)
        thr = 0.01*np.max(np.abs(x)); idx = np.where(np.abs(x) > thr)[0]
        x = x[max(0, idx[0]-int(0.02*sr)): idx[-1]+int(0.04*sr)]
        win = int(0.01*sr); env = np.array([np.max(np.abs(x[k:k+win])) for k in range(0, len(x), win)])
        quiet = env < 0.02*np.max(env); keep = np.ones(len(env), bool); run = 0
        for k, q in enumerate(quiet):
            run = run + 1 if q else 0
            if run > 12: keep[k] = False
        x = np.concatenate([x[k*win:(k+1)*win] for k in range(len(env)) if keep[k]])
        sf.write(f"{vd}/{i:02d}.wav", x, sr)
    print("voz ok")

# ======================================================== TIEMPOS
class Timeline:
    def __init__(self, ep):
        self.ep = ep
        vd = os.path.join(OUT, ep["slug"], "voz")
        self.durs = [sf.info(f"{vd}/{i:02d}.wav").duration for i in range(len(ep["scenes"]))]
        # cada escena dura un número entero de fotogramas
        self.frames = [round((d + GAP)*FPS) for d in self.durs]
        self.len = [f/FPS for f in self.frames]
        self.starts = np.cumsum([0] + self.len[:-1]).tolist()
        self.total = sum(self.len)
        self.wt = [self.word_times(txt, d) for (txt, _), d in zip(ep["scenes"], self.durs)]
    @staticmethod
    def word_times(text, dur):
        words = text.split(); wts = []
        for w in words:
            wt = len(w.strip("¿?¡!.,:…")) + 2
            if w[-1] in ",:": wt += 3
            if w[-1] in ".?!…": wt += 5
            wts.append(wt)
        tot = sum(wts); t = 0; out = []
        for w, wt in zip(words, wts):
            out.append((w, t, t + dur*wt/tot)); t += dur*wt/tot
        return out
    def at(self, i, key, nth=1):
        n = 0
        for w, a, b in self.wt[i]:
            if key.lower() in w.lower():
                n += 1
                if n == nth: return a
        return 999.0

TL = None
def at(i, key, nth=1): return TL.at(i, key, nth)
custom_ep01.at = at; custom_ep01.CX = CX

# ======================================================== OBJETOS EXTRA
def building(c, x, y, s, roof_color, label=None, stars=False, dome=False):
    w, h = 230*s, 150*s
    if dome:
        c.arc(x, y - h/2 - 10*s, 70*s, math.pi, 2*math.pi); c.close_path(); fs(c, roof_color, 7*s)
        c.set_source_rgb(*INK); c.set_line_width(6*s); c.move_to(x, y - h/2 - 80*s); c.line_to(x, y - h/2 - 115*s); c.stroke()
        c.move_to(x, y - h/2 - 115*s); c.line_to(x + 30*s, y - h/2 - 105*s); c.line_to(x, y - h/2 - 95*s); c.close_path(); fs(c, RED, 4*s)
    else:
        c.move_to(x - w/2 - 15*s, y - h/2); c.line_to(x, y - h/2 - 75*s); c.line_to(x + w/2 + 15*s, y - h/2); c.close_path(); fs(c, roof_color, 7*s)
    c.rectangle(x - w/2, y - h/2, w, h); fs(c, WHITE, 7*s)
    for k in range(4):
        px = x - w/2 + 30*s + k*(w - 60*s)/3
        c.rectangle(px - 11*s, y - h/2 + 18*s, 22*s, h - 36*s); fs(c, hx("EDE7F6"), 5*s)
    c.rectangle(x - w/2 - 18*s, y + h/2, w + 36*s, 18*s); fs(c, roof_color, 6*s)
    if stars:
        c.arc(x, y - h/2 - 30*s, 26*s, 0, 2*math.pi); fs(c, hx("3B5BA9"), 4*s)
        for k in range(12):
            a = k*math.pi/6
            c.arc(x + 17*s*math.cos(a), y - h/2 - 30*s + 17*s*math.sin(a), 2.8*s, 0, 2*math.pi)
            c.set_source_rgb(*HIL); c.fill()
    if label:
        text(c, label, x, y + h/2 + 9*s, 22*s, INK)

def printer(c, x, y, s, t=0):
    rrect(c, x - 110*s, y - 60*s, 220*s, 120*s, 18*s); fs(c, hx("9AA6C8"), 7*s)
    rrect(c, x - 80*s, y - 95*s, 160*s, 40*s, 10*s); fs(c, hx("C9D2EA"), 6*s)
    c.arc(x + 70*s, y - 20*s, 10*s, 0, 2*math.pi); fs(c, GREEN, 4*s)
    off = (t*120) % 70
    c.save(); c.rectangle(x - 150*s, y + 40*s, 300*s, 150*s); c.clip()
    note(c, x, y + 50*s + off*s, 150*s, 75*s, "€")
    c.restore()
    c.rectangle(x - 95*s, y + 30*s, 190*s, 14*s); fs(c, INK, 2*s)

def cart(c, x, y, s, full=True):
    c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
    if full:
        for k, col in enumerate((RED, HIL, GREEN, SKY)):
            c.arc(x - 55*s + k*38*s, y - 40*s - (k % 2)*18*s, 26*s, 0, 2*math.pi); fs(c, col, 5*s)
    c.move_to(x - 130*s, y - 75*s); c.line_to(x - 100*s, y - 75*s); c.line_to(x - 80*s, y + 30*s)
    c.line_to(x + 85*s, y + 30*s); c.line_to(x + 105*s, y - 50*s); c.line_to(x - 92*s, y - 50*s)
    c.set_source_rgb(*INK); c.set_line_width(10*s); c.stroke()
    for dx in (-55, 60):
        c.arc(x + dx*s, y + 58*s, 15*s, 0, 2*math.pi); fs(c, WHITE, 7*s)

def piggy(c, x, y, s):
    c.save(); c.translate(x, y); c.scale(1.25, 1); c.arc(0, 0, 80*s, 0, 2*math.pi); c.restore(); fs(c, ROSE, 8*s)
    c.arc(x + 95*s, y + 5*s, 24*s, 0, 2*math.pi); fs(c, hx("F4A9BC"), 6*s)
    c.set_source_rgb(*INK)
    for dy in (-6, 6): c.arc(x + 95*s - 7*s, y + 5*s + dy*0.0 + dy*s*0, 3*s, 0, 2*math.pi)
    c.arc(x + 88*s, y + 5*s, 3.5*s, 0, 2*math.pi); c.arc(x + 102*s, y + 5*s, 3.5*s, 0, 2*math.pi); c.fill()
    c.arc(x + 45*s, y - 25*s, 7*s, 0, 2*math.pi); c.fill()
    c.move_to(x + 20*s, y - 70*s); c.line_to(x + 40*s, y - 105*s); c.line_to(x + 60*s, y - 62*s); c.close_path(); fs(c, ROSE, 6*s)
    for dx in (-55, -15, 25, 60):
        c.rectangle(x + dx*s - 10*s, y + 60*s, 20*s, 30*s); fs(c, ROSE, 6*s)
    c.rectangle(x - 30*s, y - 82*s, 60*s, 10*s); fs(c, INK, 2*s)

def pricetag(c, x, y, s, label="9,99 €"):
    c.save(); c.translate(x, y); c.rotate(-0.25)
    c.move_to(-110*s, -55*s); c.line_to(70*s, -55*s); c.line_to(120*s, 0); c.line_to(70*s, 55*s); c.line_to(-110*s, 55*s); c.close_path(); fs(c, HIL, 8*s)
    c.arc(75*s, 0, 12*s, 0, 2*math.pi); fs(c, WHITE, 5*s)
    text(c, label, -25*s, 0, 46*s, INK)
    c.restore()

def doc(c, x, y, s, label="DOC"):
    c.save(); c.translate(x, y); c.rotate(0.05)
    rrect(c, -90*s, -120*s, 180*s, 240*s, 14*s); fs(c, WHITE, 8*s)
    rrect(c, -70*s, -100*s, 140*s, 46*s, 8*s); fs(c, LAV, 5*s)
    text(c, label, 0, -77*s, 30*s if len(label) <= 7 else 22*s, INK)
    c.set_source_rgb(*hx("D8D8E4"))
    for k in range(4):
        rrect(c, -65*s, -25*s + k*30*s, 130*s - (k == 3)*50*s, 12*s, 6*s); c.fill()
    c.restore()

def house(c, x, y, s):
    c.move_to(x - 130*s, y - 20*s); c.line_to(x, y - 130*s); c.line_to(x + 130*s, y - 20*s); c.close_path(); fs(c, RED, 8*s)
    c.rectangle(x - 100*s, y - 20*s, 200*s, 130*s); fs(c, PEACH, 8*s)
    rrect(c, x - 25*s, y + 30*s, 50*s, 80*s, 6*s); fs(c, LAV, 6*s)
    c.rectangle(x + 40*s, y + 5*s, 40*s, 40*s); fs(c, SKY, 5*s)
    c.rectangle(x - 80*s, y + 5*s, 40*s, 40*s); fs(c, SKY, 5*s)

def vault(c, x, y, s):
    rrect(c, x - 110*s, y - 110*s, 220*s, 220*s, 20*s); fs(c, hx("B8BCC8"), 8*s)
    c.arc(x, y, 60*s, 0, 2*math.pi); fs(c, hx("DCDFE8"), 7*s)
    c.set_source_rgb(*INK); c.set_line_width(7*s)
    for k in range(3):
        a = k*2*math.pi/3
        c.move_to(x, y); c.line_to(x + 50*s*math.cos(a), y + 50*s*math.sin(a)); c.stroke()

def magnifier(c, x, y, s):
    c.set_source_rgb(*INK); c.set_line_width(22*s); c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.move_to(x + 55*s, y + 55*s); c.line_to(x + 115*s, y + 115*s); c.stroke()
    c.arc(x, y, 80*s, 0, 2*math.pi); c.set_source_rgba(1, 1, 1, 0.6); c.fill_preserve()
    c.set_source_rgb(*INK); c.set_line_width(13*s); c.stroke()

def factory(c, x, y, s, t=0):
    c.move_to(x - 120*s, y + 80*s); c.line_to(x - 120*s, y - 20*s); c.line_to(x - 60*s, y - 60*s); c.line_to(x - 60*s, y - 20*s)
    c.line_to(x, y - 60*s); c.line_to(x, y - 20*s); c.line_to(x + 60*s, y - 60*s); c.line_to(x + 60*s, y - 100*s)
    c.line_to(x + 100*s, y - 100*s); c.line_to(x + 100*s, y + 80*s); c.close_path(); fs(c, PEACH, 8*s)
    for k in range(3):
        r = (14 + ((t*30 + k*12) % 30))*s
        c.arc(x + 80*s + k*8*s, y - 125*s - k*30*s - (t*20 % 20)*s, r*0.7, 0, 2*math.pi); c.set_source_rgba(*INK, 0.15); c.fill()
    for k in range(3):
        c.rectangle(x - 95*s + k*65*s, y + 10*s, 35*s, 35*s); fs(c, HIL, 5*s)

def coins(c, x, y, s):
    for k in range(4):
        c.save(); c.translate(x - 40*s, y + 60*s - k*24*s); c.scale(1, 0.35); c.arc(0, 0, 60*s, 0, 2*math.pi); c.restore(); fs(c, HIL, 6*s)
    coin(c, x + 60*s, y + 10*s, 62*s, smile=False)

def hearts(c, x, y, s, t=0):
    heart(c, x - 45*s, y + 10*s, 1.0*s*(1 + 0.08*math.sin(t*6)), RED)
    heart(c, x + 55*s, y - 35*s, 0.7*s*(1 + 0.08*math.sin(t*6 + 1)), hx("F59AB3"))
    heart(c, x + 40*s, y + 70*s, 0.5*s*(1 + 0.08*math.sin(t*6 + 2)), hx("F59AB3"))

def bed(c, x, y, s, t=0):
    rrect(c, x - 140*s, y - 10*s, 280*s, 70*s, 14*s); fs(c, SKY, 8*s)
    rrect(c, x - 130*s, y - 40*s, 90*s, 40*s, 14*s); fs(c, WHITE, 6*s)
    for dx in (-130, 130):
        c.rectangle(x + dx*s - 8*s, y + 55*s, 16*s, 40*s); fs(c, PEACH, 5*s)
    note(c, x + 40*s, y - 35*s, 130*s, 66*s, "€", rot=-0.15)

def bolt(c, x, y, s):
    c.move_to(x + 20*s, y - 130*s); c.line_to(x - 70*s, y + 15*s); c.line_to(x - 5*s, y + 15*s)
    c.line_to(x - 30*s, y + 130*s); c.line_to(x + 75*s, y - 30*s); c.line_to(x + 10*s, y - 30*s); c.close_path(); fs(c, HIL, 8*s)

def calendar(c, x, y, s, t=0, label="IPC"):
    rrect(c, x - 100*s, y - 100*s, 200*s, 200*s, 18*s); fs(c, WHITE, 8*s)
    c.save(); rrect(c, x - 100*s, y - 100*s, 200*s, 200*s, 18*s); c.clip()
    c.rectangle(x - 100*s, y - 100*s, 200*s, 55*s); c.set_source_rgb(*RED); c.fill(); c.restore()
    rrect(c, x - 100*s, y - 100*s, 200*s, 200*s, 18*s); c.set_source_rgb(*INK); c.set_line_width(8*s); c.stroke()
    m = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN"][int(t*1.5) % 6]
    text(c, m, x, y - 73*s, 34*s, WHITE)
    text(c, label, x, y + 35*s, (58 if len(label) <= 4 else 44)*s, INK)

def arrowdown(c, x, y, s, up=False):
    d = -1 if up else 1
    c.move_to(x - 40*s, y - d*100*s); c.line_to(x + 40*s, y - d*100*s); c.line_to(x + 40*s, y + d*10*s); c.line_to(x + 85*s, y + d*10*s)
    c.line_to(x, y + d*110*s); c.line_to(x - 85*s, y + d*10*s); c.line_to(x - 40*s, y + d*10*s); c.close_path()
    fs(c, GREEN if up else RED, 8*s)

def clock(c, x, y, s, t=0):
    c.arc(x, y, 100*s, 0, 2*math.pi); fs(c, WHITE, 9*s)
    c.set_source_rgb(*INK); c.set_line_width(10*s); c.set_line_cap(cairo.LINE_CAP_ROUND)
    a = t*4
    c.move_to(x, y); c.line_to(x + 70*s*math.sin(a), y - 70*s*math.cos(a)); c.stroke()
    c.move_to(x, y); c.line_to(x + 45*s*math.sin(a/12), y - 45*s*math.cos(a/12)); c.stroke()

def snail(c, x, y, s, t=0):
    x = x + 15*s*math.sin(t)
    c.save(); c.translate(x, y + 40*s); c.scale(1, 0.4); c.arc(0, 0, 120*s, math.pi, 2*math.pi); c.restore(); fs(c, hx("C7E6A3"), 7*s)
    c.arc(x - 10*s, y - 10*s, 75*s, 0, 2*math.pi); fs(c, PEACH, 8*s)
    c.arc(x - 10*s, y - 10*s, 42*s, 0, 2*math.pi); c.set_source_rgb(*INK); c.set_line_width(6*s); c.stroke()
    c.arc(x - 10*s, y - 10*s, 16*s, 0, 2*math.pi); c.stroke()
    c.arc(x + 95*s, y + 5*s, 30*s, 0, 2*math.pi); fs(c, hx("C7E6A3"), 6*s)
    face(c, x + 95*s, y + 5*s, 30*s, "sad")

def ecb(c, x, y, s): building(c, x, y, s, hx("3B5BA9"), "BCE", stars=True)
def gov(c, x, y, s): building(c, x, y, s, hx("E8B77A"), None, dome=True)
def parliament(c, x, y, s): building(c, x, y, s, RED, "CORTES")
def bank(c, x, y, s): building(c, x, y, s, GREEN, "BANCO")
def commission(c, x, y, s): building(c, x, y, s, hx("3B5BA9"), "COMISIÓN", stars=True)
def euparl(c, x, y, s): building(c, x, y, s, hx("7FA7E0"), "PARLAMENTO", dome=True)
def council(c, x, y, s): building(c, x, y, s, hx("9C89D9"), "CONSEJO", stars=True)

def thermo(c, x, y, s, t=0):
    rrect(c, x - 30*s, y - 140*s, 60*s, 220*s, 30*s); fs(c, WHITE, 8*s)
    c.arc(x, y + 100*s, 50*s, 0, 2*math.pi); fs(c, RED, 8*s)
    lvl = 0.45 + 0.08*math.sin(t*3)
    rrect(c, x - 14*s, y - 120*s + 200*s*(1 - lvl), 28*s, 200*s*lvl + 40*s, 14*s); c.set_source_rgb(*RED); c.fill()
    for k in range(4):
        c.move_to(x + 30*s, y - 100*s + k*45*s); c.line_to(x + 55*s, y - 100*s + k*45*s)
        c.set_source_rgb(*INK); c.set_line_width(5*s); c.stroke()

def percent(c, x, y, s, t=0):
    c.arc(x, y, 110*s, 0, 2*math.pi); fs(c, HIL, 9*s)
    text(c, "%", x, y + 4*s, 140*s, INK)

def chartup(c, x, y, s, t=0):
    rrect(c, x - 150*s, y - 110*s, 300*s, 220*s, 18*s); fs(c, WHITE, 8*s)
    pts = [(-120, 70), (-60, 72), (-20, 40), (20, -10), (60, -50), (110, -75)]
    p = clamp(t/1.2)
    n = 1 + p*(len(pts) - 1)
    c.set_source_rgb(*RED); c.set_line_width(12*s); c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.move_to(x + pts[0][0]*s, y + pts[0][1]*s)
    for k in range(1, len(pts)):
        if k <= n: c.line_to(x + pts[k][0]*s, y + pts[k][1]*s)
        else:
            f = n - (k - 1)
            if f > 0:
                a, b = pts[k-1], pts[k]; c.line_to(x + (a[0] + (b[0]-a[0])*f)*s, y + (a[1] + (b[1]-a[1])*f)*s)
            break
    c.stroke()

def people(c, x, y, s, t=0):
    for k, (dx, col) in enumerate(((-90, PEACH), (0, LAV), (90, MINT))):
        yy = y - abs(math.sin(t*5 + k))*10*s
        c.arc(x + dx*s, yy - 40*s, 42*s, 0, 2*math.pi); fs(c, col, 7*s); face(c, x + dx*s, yy - 40*s, 42*s, "happy")
        c.save(); c.translate(x + dx*s, yy + 55*s); c.scale(1, 0.75); c.arc(0, 0, 48*s, math.pi, 2*math.pi); c.restore(); fs(c, col, 7*s)

def elder(c, x, y, s, t=0):
    c.arc(x, y - 30*s, 75*s, 0, 2*math.pi); fs(c, hx("FFE3CC"), 8*s)
    c.set_source_rgb(*WHITE)
    for dx in (-60, 60):
        c.arc(x + dx*s, y - 70*s, 28*s, 0, 2*math.pi); c.fill_preserve(); c.set_source_rgb(*INK); c.set_line_width(5*s); c.stroke(); c.set_source_rgb(*WHITE)
    face(c, x, y - 30*s, 75*s, "happy", glasses=True)
    c.set_source_rgb(*INK); c.set_line_width(9*s); c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.move_to(x + 110*s, y - 10*s); c.line_to(x + 110*s, y + 120*s); c.stroke()
    c.arc(x + 95*s, y - 10*s, 15*s, math.pi, 2*math.pi); c.stroke()

def docs(c, x, y, s, label="DEUDA"):
    for k in range(3):
        doc(c, x - 50*s + k*50*s, y + 20*s - k*20*s, 0.8*s, label)

PROPS = dict(coin=lambda c, x, y, s, t, it: coin(c, x, y, 105*s, spin=math.cos(t*3), smile=math.cos(t*3) > 0),
             cart=lambda c, x, y, s, t, it: cart(c, x, y, s),
             pricetag=lambda c, x, y, s, t, it: pricetag(c, x, y, s),
             piggy=lambda c, x, y, s, t, it: piggy(c, x, y, s),
             hearts=lambda c, x, y, s, t, it: hearts(c, x, y, s, t),
             gov=lambda c, x, y, s, t, it: gov(c, x, y + 25*s, s),
             parliament=lambda c, x, y, s, t, it: parliament(c, x, y + 25*s, s),
             ecb=lambda c, x, y, s, t, it: ecb(c, x, y + 25*s, s),
             bank=lambda c, x, y, s, t, it: bank(c, x, y + 25*s, s),
             commission=lambda c, x, y, s, t, it: commission(c, x, y + 25*s, s),
             euparl=lambda c, x, y, s, t, it: euparl(c, x, y + 25*s, s),
             council=lambda c, x, y, s, t, it: council(c, x, y + 25*s, s),
             doc=lambda c, x, y, s, t, it: doc(c, x, y, s, it.get("text", "DOC")),
             docs=lambda c, x, y, s, t, it: docs(c, x, y, s, it.get("ptext", "DEUDA")),
             printer=lambda c, x, y, s, t, it: printer(c, x, y, s, t),
             note=lambda c, x, y, s, t, it: note(c, x, y, 220*s, 115*s, "50", rot=-0.08),
             factory=lambda c, x, y, s, t, it: factory(c, x, y, s, t),
             coins=lambda c, x, y, s, t, it: coins(c, x, y, s),
             house=lambda c, x, y, s, t, it: house(c, x, y, s),
             vault=lambda c, x, y, s, t, it: vault(c, x, y, s),
             phone=lambda c, x, y, s, t, it: phone(c, x, y, 1.15*s, it.get("_amount", "")),
             magnifier=lambda c, x, y, s, t, it: magnifier(c, x, y, s),
             bed=lambda c, x, y, s, t, it: bed(c, x, y, s, t),
             bolt=lambda c, x, y, s, t, it: bolt(c, x, y, s),
             bread=lambda c, x, y, s, t, it: bread(c, x, y, 1.1*s),
             calendar=lambda c, x, y, s, t, it: calendar(c, x, y, s, t, it.get("ptext", "IPC")),
             arrowdown=lambda c, x, y, s, t, it: arrowdown(c, x, y, s),
             chartup=lambda c, x, y, s, t, it: chartup(c, x, y, s, t),
             clock=lambda c, x, y, s, t, it: clock(c, x, y, s, t),
             snail=lambda c, x, y, s, t, it: snail(c, x, y, s, t),
             thermo=lambda c, x, y, s, t, it: thermo(c, x, y, s, t),
             percent=lambda c, x, y, s, t, it: percent(c, x, y, s, t),
             people=lambda c, x, y, s, t, it: people(c, x, y, s, t),
             elder=lambda c, x, y, s, t, it: elder(c, x, y, s, t))

def eur(n):
    return f"{n:,.0f} €".replace(",", ".")

# ======================================================== PLANTILLAS
def head_text(c, txt, t):
    q = pop(t, 0.0)
    if txt and q > 0:
        scaled(c, CX, 585, q); text(c, txt, CX, 585, 60 if len(txt) < 20 else 50, WHITE, stroke=INK, sw=16); c.restore()

def tpl_title(c, t, i, sp):
    q = pop(t, 0.0, 0.4)
    scaled(c, CX - 190, 740, q); mascot(c, CX - 190, 740 + 8*math.sin(t*6), 115); c.restore()
    q = pop(t, 0.0)
    if q > 0:
        scaled(c, CX + 190, 730, q); PROPS[sp["prop"]](c, CX + 190, 730 + 8*math.sin(t*5 + 1), 0.9, t, {"text": sp["ptext"], "ptext": sp["ptext"]} if "ptext" in sp else {}); c.restore()
    for k, ln in enumerate(sp["lines"]):
        q = pop(t, 0.05 + 0.15*k)
        if q > 0:
            size = 92 if len(ln) <= 11 else 76
            scaled(c, CX, 960 + k*105, q); text(c, ln, CX, 960 + k*105, size, WHITE if k == 0 else HIL, stroke=INK, sw=18); c.restore()
    for k, (sx, sy, d0) in enumerate(((150, 560, 0.5), (920, 590, 0.7), (180, 1130, 0.9), (900, 1140, 1.1))):
        q = pop(t, d0)
        if q > 0: scaled(c, sx, sy, q*(0.8 + 0.2*math.sin(t*8 + k))); star4(c, sx, sy, 1.0); c.restore()

def tpl_items(c, t, i, sp):
    head_text(c, sp.get("head"), t)
    items = sp["items"]; n = len(items)
    xs = [CX] if n == 1 else ([310, 770] if n == 2 else [215, 540, 865])
    y = 830; s = 0.95 if n <= 2 else 0.78
    times = [at(i, it["key"], it.get("nth", 1)) - 0.15 for it in items]
    for k, it in enumerate(items):
        if sp.get("arrows") and k > 0 and t >= times[k]:
            arrow(c, xs[k-1] + 95, y - 120, xs[k] - 95, y - 120, bend=-35, p=clamp((t - times[k])/0.3), lw=8)
        q = pop(t, times[k])
        if q <= 0: continue
        it = dict(it)
        if "amount" in it:
            it["_amount"] = "+" + eur(it["amount"]*clamp((t - times[k])/1.0))
        scaled(c, xs[k], y, q)
        PROPS[it["prop"]](c, xs[k], y + 6*math.sin(t*4 + k), s, t - times[k], it)
        c.restore()
        if it.get("cross") and t > times[k] + 0.3:
            xmark(c, xs[k], y, 0.75, clamp((t - times[k] - 0.3)/0.4))
        a = appear(t, times[k] + 0.1)
        if a > 0:
            text(c, it["label"], xs[k], y + 170, 40 if len(it["label"]) <= 11 else 31, INK)
            if it.get("sub"): text(c, it["sub"], xs[k], y + 215, 28, GREY)
    b = sp.get("banner")
    if b: banner(c, b["text"], CX, 1150, 50, HIL, pop(t, at(i, b["key"])))

def tpl_big(c, t, i, sp):
    t0 = at(i, sp["key"]) if sp.get("key") else 0
    q = pop(t, 0.0, 0.4)
    it = dict(sp)
    cnt = sp.get("count")
    if sp["prop"] == "phone":
        frm, to = sp.get("amount_from", 0), sp.get("amount_to", 0)
        it["_amount"] = eur(frm + (to - frm)*ease_out((t - t0)/1.5) if t >= t0 else frm)
    scaled(c, CX, 735, q); PROPS[sp["prop"]](c, CX, 735 + 6*math.sin(t*4), 1.15, t, it); c.restore()
    if cnt:
        tc = at(i, cnt["key"], cnt.get("nth", 1))
        v = cnt["frm"] + (cnt["to"] - cnt["frm"])*ease_out((t - tc)/1.0) if t >= tc else cnt["frm"]
        col = RED if (t >= tc and cnt["to"] > cnt["frm"]) else (hx("E57C7C") if t >= tc else WHITE)
        text(c, eur(v), CX, 990, 120, WHITE if t < tc else HIL, stroke=INK, sw=20)
    elif sp.get("text"):
        qq = pop(t, t0 - 0.1)
        if qq > 0:
            size = 120 if len(sp["text"]) <= 8 else (96 if len(sp["text"]) <= 12 else 80)
            scaled(c, CX, 990, qq); text(c, sp["text"], CX, 990, size, HIL, stroke=INK, sw=20); c.restore()
    if sp.get("sub"):
        a = appear(t, (at(i, cnt["key"], cnt.get("nth", 1)) if cnt else t0) + 0.2)
        if a > 0: text(c, sp["sub"], CX, 1110, 38, INK)

def tpl_bars(c, t, i, sp):
    head_text(c, sp.get("head"), t)
    bars = sp["bars"]; y0 = 720
    for k, bdef in enumerate(bars):
        tb = at(i, bdef["key"]) + bdef.get("delay", 0)
        y = y0 + k*200
        a = appear(t, tb - 0.1)
        if a <= 0: continue
        text(c, bdef["label"], 110, y - 45, 40, INK, anchor="l")
        rrect(c, 110, y, 680, 70, 35); fs(c, WHITE, 7)
        p = ease_out((t - tb)/0.9)*bdef["value"]/100
        if p > 0.01:
            c.save(); rrect(c, 110, y, 680, 70, 35); c.clip()
            c.rectangle(110, y, 680*p, 70); c.set_source_rgb(*COLORS[bdef["color"]]); c.fill(); c.restore()
            rrect(c, 110, y, 680, 70, 35); c.set_source_rgb(*INK); c.set_line_width(7); c.stroke()
        text(c, f"{round(p*100)} %", 955, y + 35, 46, INK, anchor="r")
    b = sp.get("banner")
    if b: banner(c, b["text"], CX, 1150, 50, HIL, pop(t, at(i, b["key"])))

def tpl_crowd(c, t, i, sp):
    head_text(c, sp.get("head"), t)
    n = sp["n"]; cols = 9; heads = [PEACH, LAV, MINT, ROSE, SKY, YEL]
    for k in range(n):
        r, col = divmod(k, cols)
        x = 140 + col*100; y = 700 + r*105
        q = pop(t, 0.1 + k*0.04)
        if q <= 0: continue
        big = k < sp.get("hl", 6)
        scaled(c, x, y, q)
        c.arc(x, y, 40, 0, 2*math.pi); fs(c, hx("3B5BA9") if big else heads[k % 6], 6)
        face(c, x, y, 40, "happy")
        c.restore()
    a = appear(t, 0.8)
    if a > 0:
        text(c, sp.get("caption", "6 del Comité Ejecutivo  +  21 gobernadores"), CX, 1055, 34, INK)
    b = sp.get("banner")
    if b: banner(c, b["text"], CX, 1160, 46, HIL, pop(t, at(i, b["key"])))

def tpl_cta(c, t, i, sp):
    q = pop(t, 0.0, 0.4)
    scaled(c, 270, 700, q); mascot(c, 270, 710 + 8*math.sin(t*6), 115); c.restore()
    qb = pop(t, 0.2)
    if qb > 0:
        scaled(c, 690, 680, qb)
        rrect(c, 470, 590, 450, 190, 34); c.set_source_rgb(*WHITE); c.fill_preserve(); c.set_source_rgb(*INK); c.set_line_width(7); c.stroke()
        c.move_to(500, 700); c.line_to(420, 730); c.line_to(510, 740); c.close_path(); c.set_source_rgb(*WHITE); c.fill_preserve(); c.set_source_rgb(*INK); c.stroke()
        c.rectangle(492, 698, 22, 44); c.set_source_rgb(*WHITE); c.fill()
        for k, ln in enumerate(sp["question"]): text(c, ln, 695, 645 + k*70, 52, INK)
        c.restore()
    tn = at(i, sp["key"])
    qn = pop(t, tn - 0.1)
    if qn > 0:
        scaled(c, CX, 900, qn)
        pill(c, f"NIVEL SIGUIENTE", CX, 860, 34, HIL, INK)
        nx = sp["next"]
        text(c, nx, CX, 945, 52 if len(nx) <= 26 else 42, INK)
        c.restore()
    qs = pop(t, max(0.6, tn + 0.6))
    if qs > 0:
        pulse = 1 + 0.06*math.sin(t*10)
        scaled(c, CX, 1100, qs*pulse)
        rrect(c, CX - 230, 1100 - 62, 460, 124, 62); fs(c, hx("F59AB3"), 9)
        text(c, "+ Sígueme", CX, 1100, 62, WHITE, stroke=INK, sw=12)
        c.restore()

CUSTOM = dict(trueque=custom_ep01.sc_trueque, problema=custom_ep01.sc_problema, invento=custom_ep01.sc_invento,
              evolucion=custom_ep01.sc_evolucion, billete=custom_ep01.sc_billete, acuerdo=custom_ep01.sc_acuerdo)
TEMPLATES = dict(title=tpl_title, items=tpl_items, big=tpl_big, bars=tpl_bars, crowd=tpl_crowd, cta=tpl_cta)

# ======================================================== FOTOGRAMA
def background(c):
    c.set_source_rgb(*CREAM); c.paint()
    c.set_source_rgba(*INK, 0.06)
    for yy in range(18, H, 36):
        for xx in range(18 + (yy//36 % 2)*18, W, 36):
            c.arc(xx, yy, 3, 0, 2*math.pi); c.fill()

def header(c, gt, ep):
    w = pill(c, "EN CRISTIANO", 60, 330, 40, INK, WHITE, anchor="l")
    text(c, "EN CRISTIANO", 60 + w/2, 330, 40, WHITE)
    pill(c, f"NIVEL {ep['nivel']}", 60 + w + 18, 330, 40, HIL, INK, anchor="l")
    remaining = max(0.0, TL.total - gt)
    x0, y0, bw, bh = 60, 398, 790, 30
    rrect(c, x0, y0, bw, bh, bh/2); fs(c, WHITE, 6)
    frac = remaining/TL.total
    col = GREEN if remaining > 10 else (hx("F2A65A") if remaining > 5 else RED)
    if frac > 0.005:
        c.save(); rrect(c, x0, y0, bw, bh, bh/2); c.clip()
        c.rectangle(x0, y0, bw*frac, bh); c.set_source_rgb(*col); c.fill(); c.restore()
        rrect(c, x0, y0, bw, bh, bh/2); c.set_source_rgb(*INK); c.set_line_width(6); c.stroke()
    rrect(c, 870, y0 - 14, 150, bh + 28, (bh + 28)/2); fs(c, WHITE, 6)
    text(c, f"{math.ceil(remaining - 1e-6)} s", 945, y0 + bh/2, 38)

def subtitles(c, i, t):
    words = TL.wt[i]
    chunks, cur = [], []
    for k, (w, a, b) in enumerate(words):
        cur.append(k)
        if len(cur) >= 4 or w[-1] in ".,:?!…": chunks.append(cur); cur = []
    if cur: chunks.append(cur)
    active = chunks[0]
    for ch in chunks:
        if words[ch[0]][1] <= t + 0.05: active = ch
    size = 66; font(c, size); sp = c.text_extents(" ").x_advance
    widths = [c.text_extents(words[k][0]).x_advance for k in active]
    lines, cur, cw = [], [], 0
    for k, wd in zip(active, widths):
        if cur and cw + sp + wd > 880: lines.append(cur); cur, cw = [], 0
        cur.append((k, wd)); cw += (sp if len(cur) > 1 else 0) + wd
    lines.append(cur)
    ly = SUB_Y - (len(lines) - 1)*44
    for ln in lines:
        tw = sum(wd for _, wd in ln) + sp*(len(ln) - 1); xx = W/2 - tw/2
        for k, wd in ln:
            w, a, b = words[k]
            if a <= t < b:
                rrect(c, xx - 12, ly - 46, wd + 24, 92, 18); c.set_source_rgb(*HIL); c.fill()
                text(c, w, xx, ly, size, INK, anchor="l")
            else:
                text(c, w, xx, ly, size, WHITE, anchor="l", stroke=INK, sw=11)
            xx += wd + sp
        ly += 88

def draw_frame(ep, gt):
    i = max(k for k in range(len(TL.starts)) if TL.starts[k] <= gt + 1e-9)
    t = gt - TL.starts[i]
    sp = ep["scenes"][i][1]
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(surf)
    background(c); header(c, gt, ep)
    z = 1 + 0.06*(1 - ease_out(t/0.35))
    scaled(c, CX, CY, z)
    rrect(c, *CARD, 46); fs(c, COLORS[sp.get("bg", "YEL")], 10)
    tag = sp.get("tag") or f"EPISODIO {ep['num']}"
    if sp["type"] == "title": tag = f"EPISODIO {ep['num']}"
    c.save(); rrect(c, *CARD, 46); c.clip()
    if sp["type"] == "custom": CUSTOM[sp["name"]](c, t, i)
    else: TEMPLATES[sp["type"]](c, t, i, sp)
    c.restore()
    pill(c, tag, CARD[0] + 40, CARD[1] + 52, 30, WHITE, INK, anchor="l", pad=20)
    rrect(c, *CARD, 46); c.set_source_rgb(*INK); c.set_line_width(10); c.stroke()
    c.restore()
    subtitles(c, i, t)
    return surf

# ======================================================== RENDER
def render_scene(ep, i):
    d = os.path.join(OUT, ep["slug"]); tmp = f"{d}/scene_{i:02d}.tmp.mp4"; dst = f"{d}/scene_{i:02d}.mp4"
    f0 = round(TL.starts[i]*FPS)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                          "-pix_fmt", "yuv420p", "-r", str(FPS), tmp], stdin=subprocess.PIPE)
    for k in range(TL.frames[i]):
        p.stdin.write(bytes(draw_frame(ep, (f0 + k)/FPS).get_data()))
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, dst)

def make_audio(ep):
    d = os.path.join(OUT, ep["slug"]); sr = sf.info(f"{d}/voz/00.wav").samplerate
    t = np.arange(int(0.12*sr))/sr; f = 900*np.exp(-t*25) + 300
    popfx = 0.18*np.sin(2*np.pi*np.cumsum(f)/sr)*np.exp(-t*30)
    out = []
    for i in range(len(ep["scenes"])):
        a, _ = sf.read(f"{d}/voz/{i:02d}.wav")
        seg = np.zeros(int(round(TL.frames[i]/FPS*sr))); seg[:min(len(a), len(seg))] += a[:len(seg)]
        seg[:len(popfx)] += popfx; out.append(seg)
    sf.write(f"{d}/audio_raw.wav", np.concatenate(out), sr)

def build(ep):
    from concurrent.futures import ProcessPoolExecutor
    d = os.path.join(OUT, ep["slug"])
    with ProcessPoolExecutor(2) as ex:
        list(ex.map(_render_job, [(ep["num"], i) for i in range(len(ep["scenes"]))]))
    make_audio(ep)
    with open(f"{d}/list.txt", "w") as fh:
        for i in range(len(ep["scenes"])): fh.write(f"file 'scene_{i:02d}.mp4'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{d}/list.txt", "-c", "copy", f"{d}/mudo.mp4"], check=True)
    final = os.path.join(OUT, f"{ep['slug']}.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{d}/mudo.mp4", "-i", f"{d}/audio_raw.wav", "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-af", "highpass=f=80,equalizer=f=200:t=q:w=1:g=2,equalizer=f=3500:t=q:w=1:g=3,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,loudnorm=I=-14:TP=-1.5:LRA=11",
                    "-ar", "48000", "-c:a", "aac", "-b:a", "160k", "-shortest", final], check=True)
    print(final, round(TL.total, 1), "s")

def _render_job(args):
    global TL
    num, i = args
    ep = get_ep(num); TL = Timeline(ep); render_scene(ep, i)

def get_ep(num): return next(e for e in EPISODES if e["num"] == int(num))

if __name__ == "__main__":
    cmd, num = sys.argv[1], sys.argv[2]
    ep = get_ep(num)
    if cmd == "voice": make_voice(ep)
    else:
        TL = Timeline(ep)
        if cmd == "preview":
            d = os.path.join(OUT, ep["slug"], "preview"); os.makedirs(d, exist_ok=True)
            for m in sys.argv[3].split(","):
                draw_frame(ep, float(m)).write_to_png(f"{d}/f_{float(m):05.1f}.png")
            print("total", round(TL.total, 1), "starts", [round(s, 1) for s in TL.starts])
        elif cmd == "build": build(ep)
