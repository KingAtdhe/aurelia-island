import sys, base64, subprocess, time
from playwright.sync_api import sync_playwright
glb, out = sys.argv[1], sys.argv[2]; views = sys.argv[3].split(',') if len(sys.argv) > 3 else ['f34', 'r34', 'side', 'front']; q = sys.argv[4] if len(sys.argv) > 4 else ''
import shutil; shutil.copy(glb, '/home/claude/traffic/view/m.glb')
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8799', '--directory', '/home/claude/traffic/view'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(0.8)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']); pg = b.new_page(viewport={'width': 1200, 'height': 700})
        pg.on('console', lambda m: print(m.text[:200]) if m.type == 'error' else None)
        pg.goto('http://localhost:8799/index.html?' + q + '#m.glb'); pg.wait_for_function('window.ready', timeout=60000); time.sleep(0.5)
        from PIL import Image; import io
        ims = [Image.open(io.BytesIO(base64.b64decode(pg.evaluate(f"shot('{v}')").split(',')[1]))) for v in views]
        W, H = 1200, 700; cols = 2 if len(ims) > 1 else 1; rows = (len(ims) + 1) // 2
        o = Image.new('RGB', (W * cols, H * rows))
        for i, im in enumerate(ims): o.paste(im, ((i % cols) * W, (i // cols) * H))
        o.save(out); b.close()
finally: srv.terminate()
