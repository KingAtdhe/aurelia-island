import sys, time, json, subprocess, os
from playwright.sync_api import sync_playwright
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8765', '--directory', os.environ.get('SITE_DIR', 'site')], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.0); logs = []
script = sys.argv[1] if len(sys.argv) > 1 else 'basic'
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl'])
        pg = b.new_page(viewport={'width': 844, 'height': 390}, device_scale_factor=1)
        pg.on('console', lambda m: logs.append(m.type + ': ' + m.text[:300])); pg.on('pageerror', lambda e: logs.append('PAGEERROR: ' + str(e)[:400] + ' @ ' + str(getattr(e, 'stack', ''))[:600]))
        pg.goto('http://localhost:8765/index.html'); pg.wait_for_function('window.__game !== undefined', timeout=120000)
        def st(): return pg.evaluate('(()=>{const c=__game.car;return {x:+c.x.toFixed(1),y:+c.y.toFixed(2),z:+c.z.toFixed(1),h:+c.h.toFixed(2),kmh:Math.round(c.speed*3.6),surf:c.surf,air:c.air}})()')
        def shot(n): pg.screenshot(path='shots/%s.png' % n)
        os.makedirs('shots', exist_ok=True); shot('menu')
        exec(open('tests/%s.py' % script).read())
        b.close()
finally:
    srv.terminate()
print('\n'.join(logs[-25:]))
