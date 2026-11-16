from pathlib import Path
import hashlib,json
p=Path(__file__).resolve().parent
for x in json.loads((p/'manifest.json').read_text())['files']:
 assert hashlib.sha256((p/x['path']).read_bytes()).hexdigest()==x['sha256'],x['path']
m=json.loads((p/'mapping.json').read_text())
assert hashlib.sha256((p/m['path']).read_bytes()).hexdigest()==m['sha256']
assert json.loads((p/'release.json').read_text())['readback_verified']
print('Verified Wrap Up template, release receipt and evaluation bundle.')
