import pygame
import sys
import math
import time
import numpy as np
pygame.init()
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
size = 800
array = []
array2 = []
palleteLength = 16
#palleteLength = iter
collist = [None] * palleteLength
xp = -2.1
yp = -1.75
xe = 1.4
ye = 1.75
rs = 0
gs = 0
bs = 100
maxmode = 1
inside = (0,0,0)
r = 1
g = 1
b = 0
st = time.time()
for col,colo in enumerate(collist):
	colos = (int((col*r*(256/palleteLength) + rs*256) / (1+rs)),int((col*g*(256/palleteLength) + gs*256) / (1+gs)),int((col*b*(256/palleteLength) + bs*256) / (1+bs)))
	collist[col] = colos
if maxmode == 1:
	collist.append(inside)
else:
	collist.append((int((inside*r + rs*256) / (1+rs)),int((inside*g + gs*256) / (1+gs)),int((inside*b + bs*256) / (1+bs))))
for i in range(size):
	array2.append(False)
for i in range(size):
	array.append(array2.copy())
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
itercom = fractal(size,itercnt,xp,yp,xe,ye,np.float64(0.5),0,0,0,8,0) # Keep the parameter slots empty
while True:
        for event in pygame.event.get():
                if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                        itercom = fractal(size,itercnt,xp,yp,xe,ye,np.float64(0.5),0,0,0,8,0) # Keep the parameter slots empty
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_EQUALS:
                        sx = xe-xp
                        sy = ye-yp
                        xp += sx/4
                        xe -= sx/4
                        yp += sy/4
                        ye -= sy/4
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_MINUS:
                        sx = xe-xp
                        sy = ye-yp
                        xp -= sx/2
                        xe += sx/2
                        yp -= sy/2
                        ye += sy/2
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_UP:
                        sx = xe-xp
                        xp -= sx/2
                        xe -= sx/2
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN:
                        sx = xe-xp
                        xp += sx/2
                        xe += sx/2
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT:
                        sy = ye-yp
                        yp -= sy/2
                        ye -= sy/2
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
                        sy = ye-yp
                        yp += sy/2
                        ye += sy/2
        imask = (itercom == itercnt-1)
        pallete = np.array(collist,dtype = np.uint8)
        map = itercom % (pallete.shape[0]-1)
        map[imask] = pallete.shape[0]-1
        img = pallete[map]
        sf = pygame.surfarray.make_surface(img.swapaxes(0,1))
        window.blit(sf,(0,0))
        pygame.display.flip()
