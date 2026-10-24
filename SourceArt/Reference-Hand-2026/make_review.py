from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
root=Path('E:/Meijia/BlenderSource/Reference-Hand-2026')
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',27)
small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',22)
canvas=Image.new('RGB',(2240,1125),'#eee9e3')
d=ImageDraw.Draw(canvas)
d.text((30,22),'指间诗 · 手型与甲床建模优化',(70,55,52),font=font)
paths=[('优化前 · 手背',Path('E:/Meijia/BlenderSource/ReferenceRebuild/CG-Feminine/Renders/cg-dorsal.png')),('优化后 · 手背',root/'after-dorsal.png'),('优化后 · 手掌',root/'after-palmar.png'),('优化后 · 侧面',root/'after-radial.png')]
for i,(label,path) in enumerate(paths):
    d.text((i*560+25,72),label,(100,82,75),font=small)
    im=Image.open(path).convert('RGB');im.thumbnail((550,965))
    canvas.paste(im,(i*560+(560-im.width)//2,113))
d.text((30,1084),'同一游戏手型的参考图优化：指间展开、指尖收细、掌部体积、加长贴合甲床。',(100,82,75),font=small)
canvas.save(root/'手部建模优化对比.png')
canvas.save(Path(__file__).resolve().parents[2]/'Verification/reference-hand-comparison.png')
