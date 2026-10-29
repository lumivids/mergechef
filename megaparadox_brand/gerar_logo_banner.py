import math,sys
from PIL import Image,ImageDraw,ImageFilter,ImageFont
OUT=sys.argv[1]
GOLD,TEAL,BROWN=(232,169,58),(31,181,176),(156,106,51)
NAVY1,NAVY2=(9,20,36),(22,44,66)

def penrose(n=10,w=1.3):
    e2=(0.5,math.sqrt(3)/2)
    Lp=lambda a,b:(a+b*e2[0],b*e2[1])
    base=[Lp(*p) for p in [(w,0),(n,0),(n-w,w),(2*w,w),(2*w,n-4*w),(w,n-3*w)]]
    c=Lp(n/3,n/3);out=[]
    for k in range(3):
        a=k*2*math.pi/3;ca,sa=math.cos(a),math.sin(a)
        out.append([(c[0]+(x-c[0])*ca-(y-c[1])*sa, c[1]+(x-c[0])*sa+(y-c[1])*ca) for x,y in base])
    xs=[x for p in out for x,_ in p];ys=[y for p in out for _,y in p]
    # normalize to unit box, y flipped (image coords), centered on bbox
    mx,Mx,my,My=min(xs),max(xs),min(ys),max(ys);s=max(Mx-mx,My-my)
    return [[((x-mx)/s,(My-y)/s) for x,y in p] for p in out],((Mx-mx)/s,(My-my)/s)

def draw_penrose(img,cx,cy,size,shadow=True):
    polys,(bw,bh)=penrose()
    ox,oy=cx-bw*size/2,cy-bh*size/2
    pp=[[(ox+x*size,oy+y*size) for x,y in p] for p in polys]
    if shadow:
        sh=Image.new('RGBA',img.size,(0,0,0,0));d=ImageDraw.Draw(sh)
        for p in pp: d.polygon([(x+size*0.03,y+size*0.05) for x,y in p],fill=(0,0,0,150))
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(size*0.03)))
    d=ImageDraw.Draw(img)
    for p,col in zip(pp,[GOLD,TEAL,BROWN]): d.polygon(p,fill=col)
    # subtle edge highlights
    for p in pp: d.line(p+[p[0]],fill=(255,255,255,60),width=max(2,int(size*0.004)),joint='curve')

def grid(img,step,col=(31,181,176,28),width=2,box=None):
    d=ImageDraw.Draw(img);W,H=img.size
    for x in range(0,W,step): d.line([(x,0),(x,H)],fill=col,width=width)
    for y in range(0,H,step): d.line([(0,y),(W,y)],fill=col,width=width)

def vgrad(W,H,stops):
    im=Image.new('RGBA',(W,H));px=im.load()
    for y in range(H):
        t=y/(H-1)
        for i in range(len(stops)-1):
            t0,c0=stops[i];t1,c1=stops[i+1]
            if t0<=t<=t1:
                f=(t-t0)/(t1-t0);c=tuple(int(c0[j]+(c1[j]-c0[j])*f) for j in range(3));break
        ImageDraw.Draw(im).line([(0,y),(W,y)],fill=c+(255,))
    return im

def logo(path,S=2400):
    im=Image.new('RGBA',(S,S));d=ImageDraw.Draw(im)
    for r in range(int(S*0.72),0,-4):
        f=min(r/(S/2),1);c=tuple(int(NAVY2[j]*(1-f)+NAVY1[j]*f) for j in range(3))
        d.ellipse([S/2-r,S/2-r,S/2+r,S/2+r],fill=c+(255,))
    g=Image.new('RGBA',(S,S),(0,0,0,0));grid(g,S//16,col=(31,181,176,30),width=4);im.alpha_composite(g)
    draw_penrose(im,S/2,S/2+S*0.03,S*0.62)
    im.resize((800,800),Image.LANCZOS).convert('RGB').save(path)

def banner(path,W=2560,H=1440):
    im=vgrad(W,H,[(0,NAVY1),(0.45,NAVY2),(0.66,(120,70,60)),(0.78,(225,130,55)),(1,(240,170,80))])
    g=Image.new('RGBA',(W,H),(0,0,0,0));grid(g,80,col=(31,181,176,22));
    mask=vgrad(W,H,[(0,(255,0,0)),(0.6,(60,0,0)),(1,(0,0,0))]).split()[0]
    im.paste(Image.alpha_composite(im.copy(),g),(0,0),mask)
    d=ImageDraw.Draw(im)
    # sun glow
    glow=Image.new('RGBA',(W,H),(0,0,0,0));gd=ImageDraw.Draw(glow)
    gd.ellipse([W*0.80-200,H*0.80-200,W*0.80+200,H*0.80+200],fill=(255,190,100,150))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(90)))
    # dune layers
    for k,(base,amp,col) in enumerate([(0.80,40,(150,85,40)),(0.86,55,(110,60,30)),(0.93,45,(70,38,22))]):
        pts=[(x, H*base+amp*math.sin(x/(260+k*90)+k*1.7)+amp*0.5*math.sin(x/97+k)) for x in range(0,W+20,20)]
        d.polygon(pts+[(W,H),(0,H)],fill=col+(255,))
    # safe area content (1546x423 centered)
    sx,sy,sw,sh=(W-1546)//2,(H-423)//2,1546,423
    draw_penrose(im,sx+190,sy+sh/2,330)
    f1=ImageFont.truetype(sys.argv[2],150);f2=ImageFont.truetype(sys.argv[3],50)
    tx=sx+400;d=ImageDraw.Draw(im)
    d.text((tx,sy+95),"MEGA",font=f1,fill=(255,255,255))
    wm=d.textlength("MEGA",font=f1)
    d.text((tx+wm,sy+95),"PARADOX",font=f1,fill=GOLD)
    d.text((tx+6,sy+275),"Megaprojects that shouldn't exist.",font=f2,fill=(230,215,190))
    d.line([(tx+6,sy+262),(tx+440,sy+262)],fill=TEAL,width=6)
    im.convert('RGB').save(path)

logo(OUT+'/megaparadox_logo_800.png')
banner(OUT+'/megaparadox_banner_2560x1440.png')
