"""Offline integrity check; no network or deployment."""
from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parent
m=json.loads((root/'manifest.json').read_text())
assert m['status']=='candidate_not_deployed' and m['accepted'] is False and m['deployed_to_forge'] is False
seen={};ids=set();segments=0;bindings={}
for ref in m['mapping_files']:
 p=(root/ref['path']).resolve();assert p.is_relative_to(root)
 assert hashlib.sha256(p.read_bytes()).hexdigest()==ref['sha256']
 row=json.loads(p.read_text());assert row['instance_id']==ref['instance_id'] and row['instance_id'] not in ids;ids.add(row['instance_id'])
 for s in row['segments']:
  q=(root/s['candidate_path']).resolve();assert q.is_relative_to(root)
  b=q.read_bytes();assert len(b)==s['bytes'] and hashlib.sha256(b).hexdigest()==s['candidate_sha256']
  assert s['candidate_forge_prompt_id'] is None
  if s['slot']=='step' and s.get('type')=='frame' and row['template_code']=='sentence_frame_teach':assert s['isLastStep'] is False
  if s['slot']!='common':
   key=(row['lesson_id'],s['source_prompt_id']);assert key not in bindings or bindings[key]==s['candidate_sha256'];bindings[key]=s['candidate_sha256']
  seen[s['candidate_path']]=s['candidate_sha256'];segments+=1
assert len(ids)==m['counts']['instances'] and segments==m['counts']['segments'] and len(seen)==m['counts']['distinct_prompt_files']
# When checked inside a repository, confirm the original live snapshot bytes are still intact.
base=root.parent.parent
if (base/'manifest.json').exists():
 bm=json.loads((base/'manifest.json').read_text());refs={r['path']:r for row in bm['instances'] for r in [row.get('common'),row.get('template')]+[s.get('prompt') for s in row['steps']] if r}
 for mr in m['mapping_files']:
  for s in json.loads((root/mr['path']).read_text())['segments']:
   r=refs[s['baseline_path']];assert r['source_sha256']==s['baseline_source_sha256'];assert hashlib.sha256((base/r['path']).read_bytes()).hexdigest()==r['sha256']
print('PASS',len(ids),'instances,',segments,'segments,',len(seen),'raw prompt files; frozen export verified. See publication receipt for current deployment status.')

for ref in m["evidence_artifacts"]:
    p=(root/ref["path"]).resolve();assert p.is_relative_to(root)
    assert hashlib.sha256(p.read_bytes()).hexdigest()==ref["sha256"]
