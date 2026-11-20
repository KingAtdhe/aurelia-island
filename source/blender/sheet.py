import sys
from PIL import Image
out=sys.argv[1]; names=sys.argv[2:]
ims=[Image.open('out/view_%s.jpg'%n) for n in names]
w,h=ims[0].size; cols=2; rows=(len(ims)+1)//2
S=Image.new('RGB',(w*cols,h*rows))
for i,im in enumerate(ims): S.paste(im,((i%cols)*w,(i//cols)*h))
S.save(out,quality=85)
