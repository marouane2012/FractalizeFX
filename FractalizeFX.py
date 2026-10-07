import pygame
import sys
import math,cmath
import time
import numpy as np
import threading, os
#v1.0!
pygame.init()
pygame.key.start_text_input()
width,height = 1600,900
window = pygame.display.set_mode((width,height))
pygame.display.set_caption('Fractalize! FX')
white = (255,255,255)
black = (0,0,0)
red = (255,0,0)
green = (0,255,0)
blue = (0,0,255)
yellow = (255,255,0)
pink = (255,0,255)
cyan = (0,255,255)
itercnt = 384
bailout = 8.0
typ = 0
param1 = 0.0
param2 = 0.0
param3 = 0.0
param4 = 0.0
size_w = 900
size_h = 900
xp = -2.1
yp = -1.75
xe = 1.4
ye = 1.75
mouse_nav = False
mouse_dragging = False
mouse_drag_start = (0, 0)
mouse_drag_bounds = None   # (xp, yp, xe, ye) snapshot at drag start
last_nav_event_time = 0.0
nav_debounce = 0.15        # seconds of quiet before launching
nav_pending = False
rendering = True
image_path = 'location-%Y%m%d-%H%M%S.png'
palleteLength = 16
#palleteLength = itercnt
thread_count = min(4, os.cpu_count() or 1)
smooth = False
outdated = False
saveImage = False
progressive = True
progressive_tiers = [16, 8, 4, 2, 1]
font = pygame.font.Font(None,24)
label_font = pygame.font.Font(None,22)
field_font = pygame.font.Font(None,28)
tab_font = pygame.font.Font(None,30)
collist = [None] * palleteLength
rs = 0
gs = 0
bs = 100
maxmode = 1
inside = (0,0,0)
r = 1
g = 1
b = 0
palette_stops = None
st = time.time()
mult = 1
sf = None
itercom = None
z_final = None
custom_formula = 'z**2 + c'
custom_compiled = None
FORMULA_NAMES = {
    -1: 'Custom',
     0: 'Mandelbrot',
     1: 'Generalized Mandelbrot',
     2: 'Mandelbrot + c^p1',
     3: 'Power sequence',
     4: 'Burning Ship',
     5: 'Julia',
     6: 'Mandelbar',
     7: 'Complex-power Mandelbrot',
     8: 'Perpendicular Mandelbrot',
     9: 'Parameterized power',
    10: 'Tetration',
    11: 'Burning Ship Julia',
    12: 'Lambda',
    13: 'Burning Mandelbrot',
    14: 'Feather',
    15: 'Sine Mandelbrot',
    16: 'Czzcpaczcp',
    17: 'Sinh Mandelbrot',
    18: 'Mandelbar Julia',
    19: 'Phoenix',
}

# For each type: (param1_label, param2_label, param3_label, param4_label)
# None means "unused for this formula"
PARAM_LABELS = {
    -1: ('p1', 'p2', 'p3', 'p4'),
     0: ('(unused)', '(unused)', '(unused)', '(unused)'),
     1: ('Power', '(unused)', '(unused)', '(unused)'),
     2: ('c exponent', '(unused)', '(unused)', '(unused)'),
     3: ('Power 1', 'Power 2', 'Power 3', 'Power 4'),
     4: ('Power', '(unused)', '(unused)', '(unused)'),
     5: ('c real', 'c imag', 'Power', '(unused)'),
     6: ('Power', '(unused)', '(unused)', '(unused)'),
     7: ('z exponent real', 'z exponent imag', 'c exponent real', 'c exponent imag'),
     8: ('Power', '(unused)', '(unused)', '(unused)'),
     9: ('c real', 'c imag', '(unused)', '(unused)'),
    10: ('(unused)', '(unused)', '(unused)', '(unused)'),
    11: ('c real', 'c imag', 'Power', '(unused)'),
    12: ('c real', 'c imag', '(unused)', '(unused)'),
    13: ('Power', '(unused)', '(unused)', '(unused)'),
    14: ('(unused)', '(unused)', '(unused)', '(unused)'),
    15: ('Power', '(unused)', '(unused)', '(unused)'),
    16: ('mult a', 'z exponent b', 'z exponent c', 'divisor d'),
    17: ('Power', '(unused)', '(unused)', '(unused)'),
    18: ('c real', 'c imag', 'Power', '(unused)'),
    19: ('Phoenix p', '(unused)', '(unused)', '(unused)'),
}
class RenderJob:
    def __init__(self, func, args, tier_k=1):
        self.func = func
        self.args = args
        self.tier_k = tier_k
        self.result = None
        self.cancelled = threading.Event()
        self.done = threading.Event()
        self.t = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        try:
            r = self.func(*self.args)
            if not self.cancelled.is_set():
                self.result = r
        except Exception as e:
            import traceback
            traceback.print_exc()
        finally:
            self.done.set()

    def start(self):
        self.t.start()
active_job = None
pending_tier_idx = -1   # next tier to launch when current finishes; -1 = none

def launch_tier(idx):
    global active_job, pending_tier_idx
    k = progressive_tiers[idx]
    sw = max(1, size_w // k)
    sh = max(1, size_h // k)
    args = (sw, sh, itercnt, xp, yp, xe, ye,
            param1, param2, param3, param4, bailout, typ)
    active_job = RenderJob(fractal, args, tier_k=k)
    pending_tier_idx = idx
    active_job.start()

def start_render():
    global pending_tier_idx
    if active_job is not None:
        active_job.cancelled.set()
    pending_tier_idx = -1
    if progressive:
        launch_tier(0)
    else:
        launch_tier(len(progressive_tiers) - 1)   # last tier = full res
def build_palette():
    global collist,palleteLength
    if palette_stops is not None:
        collist = []
        n = max(2,palleteLength)
        for i in range(n):
            t = i / (n-1)
            collist.append(sample_palette(palette_stops,t))
        collist.append(inside)
        return
    collist = []
    for col in range(palleteLength):
        collist.append((
            int((col*r*(256/palleteLength) + rs*256) / (1+rs)),
            int((col*g*(256/palleteLength) + gs*256) / (1+gs)),
            int((col*b*(256/palleteLength) + bs*256) / (1+bs))
        ))
    collist.append(inside)
build_palette()
#Fractal rendering
def _iterate_grid(grid, itercnt, param1, param2, param3, param4, bailout, typ):
    sw, sh = grid.shape
    iters = np.zeros((sw, sh), dtype=np.int32)
    if typ == -1:  # Custom
        if custom_compiled is None:
            return iters, np.zeros_like(grid, dtype=np.complex128)
        f = custom_compiled
        c = grid
        z = np.zeros_like(c, dtype=np.complex128)
        for i in range(itercnt):
            mask = np.abs(z) <= bailout
            if not mask.any():
                break
            with np.errstate(all='ignore'):
                try:
                    new_z = f(z[mask], c[mask], param1, param2, param3, param4)
                except Exception:
                    break
            z[mask] = new_z
            iters[mask] = i
        return iters, z
    if typ == 0: #Mandelbrot
        c = grid
        z = np.zeros_like(c,dtype=np.complex128)
        for i in range(itercnt):
            mask = np.abs(z) <= bailout
            z[mask] = z[mask] ** 2 + c[mask] #NumPy ** square
            iters[mask] = i
        return iters,z
    if typ == 1: #Mandelbrot (generalized)
        c = grid
        z = np.zeros_like(c,dtype=np.complex128)
        for i in range(itercnt):
            mask = np.abs(z) <= bailout
            z[mask] = z[mask] ** param1 + c[mask]
            iters[mask] = i
        return iters,z
    if typ == 2: #Mandelbrot with mutation
        c = grid
        z = np.zeros_like(c,dtype=np.complex128)
        for i in range(itercnt):
            mask = np.abs(z) <= bailout
            z[mask] = (z[mask] ** 2 + c[mask]) + c[mask]**param1
            iters[mask] = i
        return iters,z
    if typ == 3: #Power sequence
        c = grid
        z = np.zeros_like(c,dtype=np.complex128)
        for i in range(itercnt):
            mask = np.abs(z) <= bailout
            z[mask] = z[mask] ** param1 + c[mask]
            z[mask] = z[mask] ** param2 + c[mask]
            z[mask] = z[mask] ** param3 + c[mask]
            z[mask] = z[mask] ** param4 + c[mask]
            iters[mask] = i
        return iters,z
    if typ == 4: #Burning ship
        c = grid
        z = np.zeros_like(c,dtype=np.complex128)
        for i in range(itercnt):
            mask = np.abs(z) <= bailout
            zr = np.abs(z.real)
            zi = np.abs(z.imag)
            z_folded = zr + 1j*zi
            z[mask] = z_folded[mask] ** param1 + c[mask] #generalized
            iters[mask] = i
        return iters,z
    if typ == 5: #Julia
        c = param1 + 1j*param2
        z = grid
        for i in range(itercnt):
            mask = np.abs(z) <= bailout
            z[mask] = z[mask] ** param3 + c #generalized
            iters[mask] = i
        return iters,z
    if typ == 6: #Mandelbar
        c = grid
        z = np.zeros_like(c,dtype=np.complex128)
        for i in range(itercnt):
            mask = np.abs(z) <= bailout
            z_conj = z.real - (1j*z.imag)
            z[mask] = z_conj[mask] ** param1 + c[mask]
            iters[mask] = i
        return iters,z
    if typ == 7: #Mandelbrot complex power
        c = grid
        z = np.zeros_like(c,dtype=np.complex128)
        for i in range(itercnt):
            mask = np.abs(z) <= bailout
            z[mask] = z[mask] ** (param1 + 1j * param2) + c[mask] ** (param3 + 1j * param4)
            iters[mask] = i
        return iters,z
    if typ == 8: #Perpendicular mandelbrot
        c = grid
        z = np.zeros_like(c,dtype=np.complex128)
        for i in range(itercnt):
            mask = np.abs(z) <= bailout
            zr = np.abs(z.real)
            z_conj = zr - (1j*z.imag)
            z[mask] = z_conj[mask] ** param1 + c[mask]
            iters[mask] = i
        return iters,z
    if typ == 9: #Parameterized power
        c = param1 + 1j*param2
        p = grid
        z = np.zeros_like(p,dtype=np.complex128)
        for i in range(itercnt):
            mask = np.abs(z) <= bailout
            z[mask] = z[mask] ** p[mask] + c
            iters[mask] = i
        return iters,z
    if typ == 10: #Tetration
        c = grid
        z = np.zeros_like(c,dtype=np.complex128)
        for i in range(itercnt):
            mask = np.abs(z) <= bailout
            z[mask] = z[mask] ** z[mask] + c[mask] #NumPy ** square
            iters[mask] = i
        return iters,z
    if typ == 11: #Burning ship julia
        c = param1 + 1j*param2
        z = grid
        for i in range(itercnt):
            mask = np.abs(z) <= bailout
            zr = np.abs(z.real)
            zi = np.abs(z.imag)
            z_folded = zr + 1j*zi
            z[mask] = z_folded[mask] ** param3 + c #generalized
            iters[mask] = i
        return iters,z
    if typ == 12: #Lambda
        c = param1 + (1j*param2)
        z = grid.copy()
        for i in range(itercnt):
            mask = np.abs(z) <= bailout
            z[mask] = z[mask] * c * (1-z[mask])
            iters[mask] = i
        return iters,z
    if typ == 13: #Ah yes,the BURNING MANDELBROT.
        c = grid
        z = np.zeros_like(c,dtype=np.complex128)
        for i in range(itercnt):
            mask = np.abs(z) <= bailout
            zr = np.abs(z.real)
            zi = np.abs(z.imag)
            z_folded = zr + 1j*zi
            z[mask] = z_folded[mask] ** param1 + c[mask] #generalized
            z[mask] = z[mask] ** param1 + c[mask]
            iters[mask] = i
        return iters,z
    if typ == 14: #Feather fractal
        c = grid
        z = np.zeros_like(c,dtype=np.complex128)
        for i in range(itercnt):
            mask = np.abs(z) <= bailout
            zr = np.abs(z.real)
            zi = np.abs(z.imag)
            a = (1+(zr**2) + 1j * zi**2)
            z[mask] = z[mask] ** 3 / a[mask] + c[mask] #generalized
            iters[mask] = i
        return iters,z
    if typ == 15: #Sine+mandelbrot
        c = grid
        z = np.zeros_like(c,dtype=np.complex128)
        for i in range(itercnt):
            mask = np.abs(z) <= bailout
            z[mask] = np.sin(z[mask]) ** param1 + c[mask]
            iters[mask] = i
        return iters,z
    if typ == 16: #apparently called the 'czzcpaczcp',but that sounds strange
        c = grid
        z = np.zeros_like(c,dtype=np.complex128)
        z = z + 1
        for i in range(itercnt):
            mask = np.abs(z) <= bailout
            z[mask] = c[mask]*(param1 * z[mask]**param2 + param4 / z[mask]**param3)
            iters[mask] = i
        return iters,z
    if typ == 17: #Sinh+mandelbrot
        c = grid
        z = np.zeros_like(c,dtype=np.complex128)
        for i in range(itercnt):
            mask = np.abs(z) <= bailout
            z[mask] = np.sinh(z[mask]) ** param1 + c[mask]
            iters[mask] = i
        return iters,z
    if typ == 18: #Julia (mandelbar)
        c = param1 + 1j*param2
        z = grid
        for i in range(itercnt):
            mask = np.abs(z) <= bailout
            z_conj = z.real - (1j*z.imag)
            z[mask] = z_conj[mask] ** param3 + c
            iters[mask] = i
        return iters,z
    if typ == 19: #Phoenix
        c = grid
        z = np.zeros_like(c, dtype=np.complex128)
        z_prev = np.zeros_like(c, dtype=np.complex128)
        p = param1
        for i in range(itercnt):
            mask = np.abs(z) <= bailout
            z_new = z[mask]**2 + c[mask] + p * z_prev[mask]
            z_prev[mask] = z[mask]
            z[mask] = z_new
            iters[mask] = i
        return iters, z
def fractal(size_w, size_h, itercnt, xp, yp, xe, ye,
            param1, param2, param3, param4, bailout, typ):
    re = np.linspace(xp, xe, size_w)
    im = np.linspace(yp, ye, size_h)
    x, y = np.meshgrid(re, im, indexing='ij')
    grid = x + 1j * y

    n = thread_count
    # below a threshold, threads cost more than they save
    if n <= 1 or size_w * size_h < 100_000:
        return _iterate_grid(grid, itercnt, param1, param2, param3, param4, bailout, typ)

    # split along axis 0 (the real axis — vertical slabs)
    bounds = []
    base = size_w // n
    extra = size_w % n
    start = 0
    for i in range(n):
        cnt = base + (1 if i < extra else 0)
        if cnt > 0:
            bounds.append((start, start + cnt))
            start += cnt

    results = [None] * len(bounds)

    def worker(i, r0, r1):
        results[i] = _iterate_grid(grid[r0:r1, :], itercnt,
                                   param1, param2, param3, param4, bailout, typ)

    threads = [threading.Thread(target=worker, args=(i, r0, r1), daemon=True)
               for i, (r0, r1) in enumerate(bounds)]
    for t in threads: t.start()
    for t in threads: t.join()

    iters = np.concatenate([r[0] for r in results], axis=0)
    z = np.concatenate([r[1] for r in results], axis=0)
    return iters, z
#Setters
def set_itercnt(v):
    global itercnt
    iv = int(float(v))
    if iv < 1: raise ValueError('invalid iteration count')
    itercnt = iv
def set_rendering(v):
    global rendering
    s = str(v).strip().lower()
    if s in ('1','true','yes','on'):
        rendering = True
    elif s in ('0','false','no','off',''):
        rendering = False
    else:
        raise ValueError
def set_bailout(v):
    global bailout
    if float(v) < 0: raise ValueError('must be positive')
    bailout = float(v)
def set_typ(v):
    global typ
    tv = int(v)
    if tv not in (-1,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19): raise ValueError('fractal type out of range')
    typ = tv
def set_param1(v):
    global param1
    param1 = float(v)
def set_param2(v):
    global param2
    param2 = float(v)
def set_param3(v):
    global param3
    param3 = float(v)
def set_param4(v):
    global param4
    param4 = float(v)
def set_mult(v):
    global mult
    if float(v) >= 2 or float(v) < 0: raise ValueError('cant exceed or be equal to 2')
    mult = float(v)
def set_size_w(v):
    global size_w
    sv = int(v)
    if sv <= 0: raise ValueError('must be positive')
    if sv > 1600: print('It is reccomended to first disable "Show image?" on page 3.')
    size_w = sv
def set_size_h(v):
    global size_h
    sv = int(v)
    if sv <= 0: raise ValueError('must be positive')
    if sv > 1600: print('It is reccomended to first disable "Show image?" on page 3.')
    size_h = sv
def set_xp(v):
    global xp
    xp = float(v)
def set_xe(v):
    global xe
    xe = float(v)
def set_yp(v):
    global yp
    yp = float(v)
def set_ye(v):
    global ye
    ye = float(v)
def set_image_path(v):
    global image_path
    if not v.strip(): raise ValueError('empty')
    image_path = v
def set_palleteLength(v):
    global palleteLength
    pv = int(v)
    if pv < 1: raise ValueError('must be positive')
    palleteLength = pv
def set_progressive(v):
    global progressive
    s = str(v).strip().lower()
    if s in ('1','true','yes','on'):
        progressive = True
    elif s in ('0','false','no','off',''):
        progressive = False
    else:
        raise ValueError
def set_smooth(v):
    global smooth
    s = str(v).strip().lower()
    if s in ('1','true','yes','on'):
        smooth = True
    elif s in ('0','false','no','off',''):
        smooth = False
    else:
        raise ValueError
def set_thread_count(v):
    global thread_count
    tv = int(v)
    if tv < 1: raise ValueError('must be >= 1')
    if tv > os.cpu_count(): raise ValueError('too many')
    thread_count = tv
def set_custom_formula(v):
    global custom_formula, custom_compiled
    s = v.strip()
    if not s:
        raise ValueError('empty')
    fn = _compile_custom(s)   # raises ValueError on any failure
    custom_formula = s
    custom_compiled = fn
def set_mouse_nav(v):
    global mouse_nav
    s = str(v).strip().lower()
    if s in ('1','true','yes','on'):
        mouse_nav = True
    elif s in ('0','false','no','off',''):
        mouse_nav = False
    else:
        raise ValueError
def set_palette_stops(v):
    global palette_stops
    s = v.strip()
    if not s or s.lower() == 'none':
        palette_stops = None
        return
    try:
        raw = eval(s, {'__builtins__': {}}, {})
    except Exception:
        raise ValueError('invalid syntax')
    if not isinstance(raw, (list, tuple)) or len(raw) < 2:
        raise ValueError('need at least 2 stops')
    parsed = []
    for item in raw:
        if not (isinstance(item, (list, tuple)) and len(item) == 2):
            raise ValueError('each stop must be [color, pos]')
        color, pos = item
        if not (isinstance(color, (list, tuple)) and len(color) == 3):
            raise ValueError('color must be (r,g,b)')
        try:
            r, g, b = int(color[0]), int(color[1]), int(color[2])
        except Exception:
            raise ValueError('color channels must be integers')
        if not all(0 <= c <= 255 for c in (r, g, b)):
            raise ValueError('channel out of 0-255')
        try:
            pos = float(pos)
        except Exception:
            raise ValueError('position must be a number')
        if not (0.0 <= pos <= 1.0):
            raise ValueError('position must be 0-1')
        parsed.append((pos, (r, g, b)))
    parsed.sort(key=lambda x: x[0])
    palette_stops = parsed
def get_palette_stops_str():
    if palette_stops is None:
        return 'None'
    parts = [f'[({r},{g},{b}),{pos:g}]' for pos, (r, g, b) in palette_stops]
    return '[' + ','.join(parts) + ']'
def sample_palette(stops, t):
    if t <= stops[0][0]:
        return stops[0][1]
    if t >= stops[-1][0]:
        return stops[-1][1]
    for i in range(len(stops) - 1):
        p0, c0 = stops[i]
        p1, c1 = stops[i+1]
        if p0 <= t <= p1:
            if p1 == p0:
                return c1
            f = (t - p0) / (p1 - p0)
            return (int(round(c0[0] + (c1[0] - c0[0]) * f)),
                    int(round(c0[1] + (c1[1] - c0[1]) * f)),
                    int(round(c0[2] + (c1[2] - c0[2]) * f)))
    return stops[-1][1]
def get_aspect_ratio():
    return (xe - xp) / (ye - yp)
def get_aspect_ratio_str():
    r = get_aspect_ratio()
    if abs(r - round(r)) < 1e-6:
        return str(int(round(r)))
    return f'{r:.4f}'
def set_aspect_ratio(v):
    global xp, xe
    n = float(v)
    if n <= 0:
        raise ValueError('must be positive')
    y_span = ye - yp
    new_x_span = n * y_span
    cx = (xp + xe) / 2
    xp = cx - new_x_span / 2
    xe = cx + new_x_span / 2
def _compile_custom(s):
    src = f"lambda z, c, p1, p2, p3, p4: ({s})"
    safe_globals = {
        'np': np,
        'math': math,
        'cmath': cmath,
        '__builtins__': {
            'abs': abs, 'complex': complex, 'float': float, 'int': int,
            'min': min, 'max': max, 'pow': pow, 'bool': bool,
            'True': True, 'False': False, 'None': None,
        },
    }
    fn = eval(src, safe_globals, {})
    # smoke test — catches formulas that compile but fail on real inputs
    test_z = np.array([0.5 + 0.5j])
    test_c = np.array([0.1 + 0.2j])
    try:
        out = fn(test_z, test_c, 1.0, 1.0, 1.0, 1.0)
    except Exception as e:
        raise ValueError(f'runtime error: {e}')
    if out is None:
        raise ValueError('formula returned None')
    if not isinstance(out, np.ndarray) and not np.isscalar(out):
        raise ValueError('formula must return a number or array')
    return fn
def _power_for_smooth():
    if typ in (0, 2):    return 2.0
    if typ in (1, 4, 6, 8, 11,13,15,17,18): return param1 if param1 > 1e-6 else 2.0
    if typ == 3:
        p = param1 * param2 * param3 * param4
        return p if p > 1e-6 else 2.0
    if typ == 5:         return param3 if param3 > 1e-6 else 2.0
    return 2.0 #7,9 are a nightmare

def colorize(iters, zfin):
    pal_arr = np.array(collist, dtype=np.uint8)
    pal_len = pal_arr.shape[0] - 1
    imask = (iters == itercnt - 1)

    if smooth:
        power = _power_for_smooth()
        log_bail = math.log(bailout) if bailout > 1.0 else math.log(2.0)
        log_pow  = math.log(power)   if power   > 1.0 else math.log(2.0)
        absz = np.abs(zfin)
        with np.errstate(divide='ignore', invalid='ignore'):
            inner = np.log(np.where(absz > 0, absz, 1.0)) / log_bail
            inner = np.where(inner > 1e-9, inner, 1e-9)
            mu = iters.astype(np.float64) + 1.0 - np.log(inner) / log_pow
        mu = np.where(np.isfinite(mu), mu, 0.0)
        pos = mu
    else:
        pos = iters.astype(np.float64)

    p = pos % pal_len
    i0 = np.floor(p).astype(np.int32)
    i1 = (i0 + 1) % pal_len
    frac = (p - i0)[..., None].astype(np.float32)
    c0 = pal_arr[i0].astype(np.float32)
    c1 = pal_arr[i1].astype(np.float32)
    img = (c0 * (1.0 - frac) + c1 * frac).astype(np.uint8)
    img[imask] = inside
    return pygame.surfarray.make_surface(img)
def screen_to_complex(px, py):
    x = xp + (px / size_w) * (xe - xp)
    y = ye - (py / size_h) * (ye - yp)   # screen y is inverted vs imaginary
    return x, y
#Input fields
class InputField:
    def __init__(self,label,x,y,w,h,getter,setter):
        self.label = label
        self.rect = pygame.Rect(x,y,w,h)
        self.getter = getter
        self.setter = setter
        try: self.text = str(getter())
        except: self.text = ''
        self.cursor = len(self.text)
        self.focused = False
        self.error = False
    def current_label(self):
        if callable(self.label):
            try: return self.label()
            except Exception: return '?'
        return self.label
    def commit(self):
        try:
            self.setter(self.text)
            self.error = False
            return True
        except:
            self.error = True
            return False
    def sync(self):
        if not self.focused and not self.error:
            try:
                self.text = str(self.getter())
                self.cursor = len(self.text)
            except Exception:
                pass
    def draw(self,surface):
        lbl = label_font.render(self.current_label(),True,(180,180,200))
        surface.blit(lbl,(self.rect.x,self.rect.y - 22))
        bg = (50,55,70) if self.focused else (25,25,32)
        pygame.draw.rect(surface,bg,self.rect)
        if self.error: border=red
        elif self.focused: border=yellow
        else: border=(90,90,110)
        pygame.draw.rect(surface,border,self.rect,2)
        txt = field_font.render(self.text,True,white)
        surface.blit(txt,(self.rect.x+8,self.rect.y+7))
        if self.focused:
            cx = self.rect.x + 8 + field_font.size(self.text[:self.cursor])[0]
            pygame.draw.line(surface,white,(cx,self.rect.y+6),(cx,self.rect.bottom-6),2)
PANEL_X,FIELD_X = 900,920
FIELD_W,FIELD_H = 660,32
page1_fields = [
    InputField(lambda: PARAM_LABELS.get(typ, ('p1','p2','p3','p4'))[0],
           FIELD_X, 160, FIELD_W, FIELD_H, lambda: param1, set_param1),
    InputField(lambda: PARAM_LABELS.get(typ, ('p1','p2','p3','p4'))[1],
           FIELD_X, 240, FIELD_W, FIELD_H, lambda: param2, set_param2),
    InputField(lambda: PARAM_LABELS.get(typ, ('p1','p2','p3','p4'))[2],
           FIELD_X, 320, FIELD_W, FIELD_H, lambda: param3, set_param3),
    InputField(lambda: PARAM_LABELS.get(typ, ('p1','p2','p3','p4'))[3],
           FIELD_X, 400, FIELD_W, FIELD_H, lambda: param4, set_param4),
    InputField('Iterations',        FIELD_X, 480, FIELD_W, FIELD_H, lambda: itercnt, set_itercnt),
    InputField('Bailout',           FIELD_X, 560, FIELD_W, FIELD_H, lambda: bailout, set_bailout),
    ]
page2_fields = [
    InputField('X min',             FIELD_X, 160, FIELD_W, FIELD_H, lambda: xp, set_xp),
    InputField('X max',             FIELD_X, 240, FIELD_W, FIELD_H, lambda: xe, set_xe),
    InputField('Y min',             FIELD_X, 320, FIELD_W, FIELD_H, lambda: yp, set_yp),
    InputField('Y max',             FIELD_X, 400, FIELD_W, FIELD_H, lambda: ye, set_ye),
    InputField('Save path',         FIELD_X, 480, FIELD_W, FIELD_H, lambda: image_path,    set_image_path),
    InputField('Palette length',    FIELD_X, 560, FIELD_W, FIELD_H, lambda: palleteLength, set_palleteLength),
]
page3_fields = [
    InputField('Type (0 to 19)',     FIELD_X, 160, FIELD_W, FIELD_H, lambda: typ,       set_typ),
    InputField('Width',             FIELD_X, 240, FIELD_W, FIELD_H, lambda: size_w,    set_size_w),
    InputField('Height',            FIELD_X, 320, FIELD_W, FIELD_H, lambda: size_h,    set_size_h),
    InputField('Show image?',       FIELD_X, 400, FIELD_W, FIELD_H, lambda: rendering, set_rendering),
    InputField('Palette stops',     FIELD_X, 480, FIELD_W, FIELD_H,
           get_palette_stops_str, set_palette_stops),
    InputField('Aspect ratio', FIELD_X, 560, FIELD_W, FIELD_H,
           get_aspect_ratio_str, set_aspect_ratio),
]
page4_fields = [
    InputField('Smooth?',              FIELD_X, 160, FIELD_W, FIELD_H, lambda: smooth,      set_smooth),
    InputField('Movement multiplier',  FIELD_X, 240, FIELD_W, FIELD_H, lambda: mult,        set_mult),
    InputField('Progressive?',         FIELD_X, 320, FIELD_W, FIELD_H, lambda: progressive, set_progressive),
    InputField('Thread count', FIELD_X, 400, FIELD_W, FIELD_H,
           lambda: thread_count, set_thread_count),
    InputField('Custom formula', FIELD_X, 480, FIELD_W, FIELD_H,
           lambda: custom_formula, set_custom_formula),
    InputField('Mouse navigation?', FIELD_X, 560, FIELD_W, FIELD_H,
           lambda: mouse_nav, set_mouse_nav),
]
pages = [page1_fields,page2_fields,page3_fields,page4_fields]
page_names = ['Parameters','Location','Rendering','Control']
current_page = 0
focused_field = None
tab_rects = [pygame.Rect(920, 70, 150, 40),
             pygame.Rect(1090, 70, 150, 40),
             pygame.Rect(1260,70,150,40),
             pygame.Rect(1430,70,150,40),]
apply_rect = pygame.Rect(920, 630, 660, 40)
def auto_iterations():
    global itercnt, outdated
    sw = max(1, size_w // 8)
    sh = max(1, size_h // 8)
    prev = None
    prev_max = None
    passes = 0
    max_passes = 500
    threshold = max(1, (sw * sh) // 10000)   # 0.01%

    while passes < max_passes:
        cur_max = itercnt - 1
        it1, _ = fractal(sw, sh, itercnt, xp, yp, xe, ye,
                         param1, param2, param3, param4, bailout, typ)
        if prev is not None:
            # pixels that stayed interior in `prev` but escaped in `it1`
            newly_escaped = np.count_nonzero((prev == prev_max) & (it1 < cur_max))
            if newly_escaped < threshold:
                break
        prev = it1
        prev_max = cur_max
        bump = max(1, int(itercnt * 0.05))
        itercnt += bump
        passes += 1

    outdated = True
    start_render()
def apply():
    global outdated
    for page in pages:
        for f in page:
            f.commit()
    build_palette()
    start_render()
    outdated = False
try:
    custom_compiled = _compile_custom(custom_formula)
except Exception as e:
    print(f'default custom formula failed: {e}')
    custom_compiled = None
start_render()
clock = pygame.time.Clock()
#Main loop
while True:
    window.fill(black)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if focused_field is not None:
            if event.type == pygame.TEXTINPUT:
                t = event.text
                f = focused_field
                f.text = f.text[:f.cursor] + t + f.text[f.cursor:]
                f.cursor += len(t)
                continue
            if event.type == pygame.KEYDOWN:
                k = event.key
                f = focused_field
                if k == pygame.K_ESCAPE:
                    f.error = False
                    f.focused = False
                    f.sync()
                    focused_field = None
                    continue
                if k in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    f.commit()
                    f.focused = False
                    focused_field = None
                    apply()
                    continue
                if k == pygame.K_TAB:
                    f.commit()
                    f.focused = False
                    f.sync()
                    fields = pages[current_page]
                    idx = fields.index(f)
                    nxt = (idx - 1) % len(fields) if (event.mod & pygame.KMOD_SHIFT) \
                          else (idx + 1) % len(fields)
                    nf = fields[nxt]
                    nf.error = False
                    try: nf.text = str(nf.getter())
                    except Exception: pass
                    nf.cursor = len(nf.text)
                    nf.focused = True
                    focused_field = nf
                    continue
                if k == pygame.K_BACKSPACE:
                    if f.cursor > 0:
                        f.text = f.text[:f.cursor-1] + f.text[f.cursor:]
                        f.cursor -= 1
                    continue
                if k == pygame.K_DELETE:
                    if f.cursor < len(f.text):
                        f.text = f.text[:f.cursor] + f.text[f.cursor+1:]
                    continue
                if k == pygame.K_LEFT:  f.cursor = max(0, f.cursor - 1); continue
                if k == pygame.K_RIGHT: f.cursor = min(len(f.text), f.cursor + 1); continue
                if k == pygame.K_HOME:  f.cursor = 0; continue
                if k == pygame.K_END:   f.cursor = len(f.text); continue
                continue
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if mouse_nav and focused_field is None and mx < size_w and my < size_h:
                if event.button == 1:   # left drag = pan
                    mouse_dragging = True
                    mouse_drag_start = (mx, my)
                    mouse_drag_bounds = (xp, yp, xe, ye)
                    continue
                if event.button == 4 or event.button == 5:   # wheel
                    factor = 0.85 if event.button == 4 else 1.0/0.85
                    fx = (xp + xe) / 2
                    fy = (yp + ye) / 2
                    new_xp = fx + (xp - fx) * factor
                    new_xe = fx + (xe - fx) * factor
                    new_yp = fy - (yp + fy) * factor
                    new_ye = fy - (ye + fy) * factor
                    xp, xe, yp, ye = new_xp, new_xe, new_yp, new_ye
                    outdated = True
                    nav_pending = True
                    last_nav_event_time = time.time()
                    continue
            if event.button == 1:
                mx, my = event.pos
                hit = None
                for f in pages[current_page]:
                    if f.rect.collidepoint(mx, my):
                        hit = f
                        break
                if hit is not None:
                    if focused_field is not None and focused_field is not hit:
                        focused_field.commit()
                        focused_field.focused = False
                        focused_field.sync()
                    if focused_field is not hit:
                        hit.error = False
                        try: hit.text = str(hit.getter())
                        except Exception: pass
                        hit.cursor = len(hit.text)
                    focused_field = hit
                    hit.focused = True
                    continue
                if focused_field is not None:
                    focused_field.commit()
                    focused_field.focused = False
                    focused_field.sync()
                    focused_field = None
                for i, tr in enumerate(tab_rects):
                    if tr.collidepoint(mx, my):
                        current_page = i
                        break
                if apply_rect.collidepoint(mx, my):
                    apply()
                continue
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            if mouse_nav and mouse_dragging:
                dx = mx - mouse_drag_start[0]
                dy = my - mouse_drag_start[1]
                oxp, oyp, oxe, oye = mouse_drag_bounds
                span_x = oxe - oxp
                span_y = oye - oyp
                xp = oxp - (dx / size_w) * span_x
                xe = oxe - (dx / size_w) * span_x
                yp = oyp - (dy / size_h) * span_y
                ye = oye - (dy / size_h) * span_y
                outdated = True
                last_nav_event_time = time.time()
                continue
        if event.type == pygame.MOUSEBUTTONUP:
            if mouse_nav and event.button == 1 and mouse_dragging:
                mouse_dragging = False
                nav_pending = True
                last_nav_event_time = time.time()
                continue
        if focused_field is None and event.type == pygame.KEYDOWN:
            shift = 0.5 if (event.mod & pygame.KMOD_SHIFT) else 1.0
            if event.key == pygame.K_r:
                outdated = False
                start_render()
                if shift == 0.5:
                    saveImage = True
            elif event.key == pygame.K_EQUALS:
                outdated = True
                progressive_idx = -1
                sx = (xe-xp) * shift * mult
                sy = (ye-yp) * shift * mult
                xp += sx/4
                xe -= sx/4
                yp += sy/4
                ye -= sy/4
            elif event.key == pygame.K_MINUS:
                outdated = True
                progressive_idx = -1
                sx = (xe-xp) * shift * mult
                sy = (ye-yp) * shift * mult
                xp -= sx/2
                xe += sx/2
                yp -= sy/2
                ye += sy/2
            elif event.key == pygame.K_LEFT:
                outdated = True
                progressive_idx = -1
                sx = (xe-xp) * shift * mult
                xp -= sx/2
                xe -= sx/2
            elif event.key == pygame.K_RIGHT:
                outdated = True
                progressive_idx = -1
                sx = (xe-xp) * shift * mult
                xp += sx/2
                xe += sx/2
            elif event.key == pygame.K_UP:
                outdated = True
                progressive_idx = -1
                sy = (ye-yp) * shift * mult
                yp -= sy/2
                ye -= sy/2
            elif event.key == pygame.K_DOWN:
                outdated = True
                progressive_idx = -1
                sy = (ye-yp) * shift * mult
                yp += sy/2
                ye += sy/2
            elif event.key == pygame.K_i:
                auto_iterations()
    if nav_pending and (time.time() - last_nav_event_time) > nav_debounce:
        nav_pending = False
        start_render()
    for f in pages[current_page]:
        f.sync()
    if saveImage:
        saveImage = False
        if sf is None or (progressive and 0 <= pending_tier_idx < len(progressive_tiers)):
            saveImage = True
        else:
            path = time.strftime(image_path)
            pygame.image.save(sf, path)
    if rendering and sf is not None:
        window.blit(sf, (0, 0))
    pygame.draw.rect(window, (15, 15, 22), pygame.Rect(PANEL_X, 0, width - PANEL_X, height))
    pygame.draw.line(window, (70, 70, 90), (PANEL_X, 0), (PANEL_X, height), 2)
    if outdated:
        warningOutdated = font.render('Image is outdated. R or apply to re-render.',True,red)
        window.blit((warningOutdated),(920,690))
    notice = font.render('Most fractals have parameters you will have to adjust.',True,(150,150,170))
    window.blit((notice),(920,720))
    name_str = FORMULA_NAMES.get(typ, f'Type {typ}')
    name_surf = tab_font.render(name_str, True, (180, 220, 255))
    window.blit(name_surf, (920, 600))
    hint = font.render(
        'Custom (type -1): z, c, p1..p4, np, math, cmath',
        True, (150, 150, 170))
    window.blit(hint, (920, 750))
    for i, tr in enumerate(tab_rects):
        active = (i == current_page)
        pygame.draw.rect(window, (55, 75, 120) if active else (30, 30, 42), tr)
        pygame.draw.rect(window, yellow if active else (90, 90, 110), tr, 2)
        lbl = tab_font.render(f'{i+1}: {page_names[i]}', True, white)
        window.blit(lbl, lbl.get_rect(center=tr.center))
    for f in pages[current_page]:
        f.draw(window)
    # --- pick up finished render ---
    if active_job is not None and active_job.done.is_set():
        if not active_job.cancelled.is_set() and active_job.result is not None:
            it, zf = active_job.result
            surface = colorize(it, zf)
            k = active_job.tier_k
            if k > 1:
                surface = pygame.transform.scale(surface, (size_w, size_h))
            sf = surface
            itercom = it
            z_final = zf
        active_job = None
        # chain to next tier if progressive and more remain
        if progressive and pending_tier_idx >= 0 \
           and pending_tier_idx < len(progressive_tiers) - 1:
            launch_tier(pending_tier_idx + 1)
        else:
            pending_tier_idx = -1
    pygame.draw.rect(window, (60, 110, 70), apply_rect)
    pygame.draw.rect(window, (130, 200, 140), apply_rect, 2)
    window.blit(tab_font.render('Apply & re-render', True, white),
                tab_font.render('Apply & re-render', True, white)
                    .get_rect(center=apply_rect.center))
    pygame.display.flip()
    clock.tick(60)
