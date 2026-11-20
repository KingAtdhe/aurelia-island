pg.evaluate("localStorage.setItem('aurelia_qual','2')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=180000)
pg.click('button[data-mode="free"]'); time.sleep(3)
print('shade', pg.evaluate("document.querySelector('canvas') ? 1 : 0"))
