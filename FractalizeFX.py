import pygame
import sys
import math
import time
import numpy as np
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
size = 900
xp = -2.1
yp = -1.75
xe = 1.4
ye = 1.75
rendering = True
image_path = 'location.png'
palleteLength = 16
#palleteLength = itercnt
outdated = False
saveImage = False
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
pallete = None
#pallete = [(0,0,0),(255,255,255)] #Example pallete
st = time.time()
def build_palette():
    global collist,palleteLength
    if pallete is not None:
        collist = list(pallete) + [inside]
        palleteLength = len(pallete)
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
def fractal(size,itercnt,xp,yp,xe,ye,param1,param2,param3,param4,bailout,typ):
    iters = np.zeros((size,size),dtype=np.int32)
    re = np.linspace(xp,xe,size)
    im = np.linspace(yp,ye,size)
    x,y = np.meshgrid(re,im,indexing='ij')
    grid = x + 1j * y
    if typ == 0: #Mandelbrot
        c = grid
        z = np.zeros_like(c,dtype=np.complex128)
        for i in range(itercnt):
            mask = np.abs(z) <= bailout
            z[mask] = z[mask] ** 2 + c[mask] #NumPy ** square
            iters[mask] = i
        return iters
    if typ == 1: #Mandelbrot (generalized)
        c = grid
        z = np.zeros_like(c,dtype=np.complex128)
        for i in range(itercnt):
            mask = np.abs(z) <= bailout
            z[mask] = z[mask] ** param1 + c[mask]
            iters[mask] = i
        return iters
    if typ == 2: #Mandelbrot with mutation
        c = grid
        z = np.zeros_like(c,dtype=np.complex128)
        for i in range(itercnt):
            mask = np.abs(z) <= bailout
            z[mask] = (z[mask] ** 2 + c[mask]) + c[mask]**param1
            iters[mask] = i
        return iters
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
        return iters
    if typ == 4: #Burning ship
        c = grid
        z = np.zeros_like(c,dtype=np.complex128)
        for i in range(itercnt):
            mask = np.abs(z) <= bailout
            z[mask] = z[mask] ** 2 + c[mask]
            iters[mask] = i
        return iters
#Setters
def set_itercnt(v):
    global itercnt
    iv = int(float(v))
    if iv < 1: raise ValueError('invalid iteration count')
    itercnt = iv
def set_rendering(v):
    global rendering
    rendering = bool(int(v))
def set_bailout(v):
    global bailout
    if float(v) < 0: raise ValueError('must be positive')
    bailout = float(v)
def set_typ(v):
    global typ
    tv = int(v)
    if tv not in (0,1,2,3,4): raise ValueError('fractal type out of range')
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
def set_size(v):
    global size
    sv = int(v)
    if sv <= 0: raise ValueError('must be positive')
    if sv > 1600: print('It is reccomended to first enable "Disable rendering" on page 3.')
    size = sv
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
        lbl = label_font.render(self.label,True,(180,180,200))
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
    InputField('Param 1',           FIELD_X, 160, FIELD_W, FIELD_H, lambda: param1,  set_param1),
    InputField('Param 2',           FIELD_X, 240, FIELD_W, FIELD_H, lambda: param2,  set_param2),
    InputField('Param 3',           FIELD_X, 320, FIELD_W, FIELD_H, lambda: param3,  set_param3),
    InputField('Param 4',           FIELD_X, 400, FIELD_W, FIELD_H, lambda: param4,  set_param4),
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
    InputField('Type (0 to 4)',     FIELD_X, 160, FIELD_W, FIELD_H, lambda: typ,     set_typ),
    InputField('Resolution',        FIELD_X, 240, FIELD_W, FIELD_H, lambda: size,    set_size),
    InputField('Show image?',       FIELD_X, 320, FIELD_W, FIELD_H, lambda: rendering, set_rendering),
]
pages = [page1_fields,page2_fields,page3_fields]
page_names = ['Parameters','Location','Rendering']
current_page = 0
focused_field = None
tab_rects = [pygame.Rect(920, 70, 200, 40),
             pygame.Rect(1140, 70, 200, 40),
             pygame.Rect(1360,70,200,40)]
apply_rect = pygame.Rect(920, 630, 660, 40)
def apply():
    global itercom,outdated
    for f in pages[current_page]:
        f.commit()
    build_palette()
    itercom = fractal(size, itercnt, xp, yp, xe, ye,
                      param1, param2, param3, param4, bailout, typ)
    outdated = False
itercom = fractal(size, itercnt, xp, yp, xe, ye,
                  param1, param2, param3, param4, bailout, typ)
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
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
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
        if focused_field is None and event.type == pygame.KEYDOWN:
            shift = 0.5 if (event.mod & pygame.KMOD_SHIFT) else 1.0
            if event.key == pygame.K_r:
                outdated = False
                itercom = fractal(size, itercnt, xp, yp, xe, ye,
                                  param1, param2, param3, param4, bailout, typ)
                if shift == 0.5:
                    saveImage = True
            elif event.key == pygame.K_EQUALS:
                outdated = True
                sx = (xe-xp) * shift
                sy = (ye-yp) * shift
                xp += sx/4
                xe -= sx/4
                yp += sy/4
                ye -= sy/4
            elif event.key == pygame.K_MINUS:
                outdated = True
                sx = (xe-xp) * shift
                sy = (ye-yp) * shift
                xp -= sx/2
                xe += sx/2
                yp -= sy/2
                ye += sy/2
            elif event.key == pygame.K_UP:
                outdated = True
                sx = (xe-xp) * shift
                xp -= sx/2
                xe -= sx/2
            elif event.key == pygame.K_DOWN:
                outdated = True
                sx = (xe-xp) * shift
                xp += sx/2
                xe += sx/2
            elif event.key == pygame.K_LEFT:
                outdated = True
                sy = (ye-yp) * shift
                yp -= sy/2
                ye -= sy/2
            elif event.key == pygame.K_RIGHT:
                outdated = True
                sy = (ye-yp) * shift
                yp += sy/2
                ye += sy/2
    if outdated:
        warningOutdated = font.render('Image is outdated. R or apply to re-render.',False,red)
        window.blit((warningOutdated),(920,690))
    for f in pages[current_page]:
        f.sync()
    imask = (itercom == itercnt-1)
    pallete = np.array(collist,dtype = np.uint8)
    map = itercom % (pallete.shape[0]-1)
    map[imask] = pallete.shape[0]-1
    img = pallete[map]
    sf = pygame.surfarray.make_surface(img.swapaxes(0,1))
    if saveImage:
        saveImage = False
        pygame.image.save(sf,image_path)
    if rendering:
        window.blit(sf,(0,0))
    pygame.draw.rect(window, (15, 15, 22), pygame.Rect(PANEL_X, 0, width - PANEL_X, height))
    pygame.draw.line(window, (70, 70, 90), (PANEL_X, 0), (PANEL_X, height), 2)
    for i, tr in enumerate(tab_rects):
        active = (i == current_page)
        pygame.draw.rect(window, (55, 75, 120) if active else (30, 30, 42), tr)
        pygame.draw.rect(window, yellow if active else (90, 90, 110), tr, 2)
        lbl = tab_font.render(f'{i+1}: {page_names[i]}', True, white)
        window.blit(lbl, lbl.get_rect(center=tr.center))
    for f in pages[current_page]:
        f.draw(window)
    pygame.draw.rect(window, (60, 110, 70), apply_rect)
    pygame.draw.rect(window, (130, 200, 140), apply_rect, 2)
    window.blit(tab_font.render('Apply & re-render', True, white),
                tab_font.render('Apply & re-render', True, white)
                    .get_rect(center=apply_rect.center))
    pygame.display.flip()
    clock.tick(60)
