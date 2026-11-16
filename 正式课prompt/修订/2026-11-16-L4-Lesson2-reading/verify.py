from pathlib import Path
import hashlib,json
p=Path(__file__).resolve().parent
m=json.loads((p/'manifest.json').read_text())
for x in m['files']:
 assert hashlib.sha256((p/x['path']).read_bytes()).hexdigest()==x['sha256'],x['path']
mapping=json.loads((p/'mapping.json').read_text())
assert len(mapping['segments'])==8
for x in mapping['segments']:
 assert hashlib.sha256((p/x['path']).read_bytes()).hexdigest()==x['sha256'],x['segment']
assert json.loads((p/'release.json').read_text())['readback_verified']
print('Verified',len(m['files']),'files and 8 deployed prompt bindings.')
