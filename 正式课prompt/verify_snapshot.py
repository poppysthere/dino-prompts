"""Offline integrity check. No network, credentials or Forge mutations."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'manifest.json').read_text())
seen={};scopes=set();ids=set()
for item in manifest['instances']:
    assert item['instance_id'] not in ids
    ids.add(item['instance_id'])
    scopes.add((item['level'],item['unit'],item['lesson']))
    mappings=list(ROOT.glob(f"L{item['level']}/U1/Lesson{item['lesson']}/**/instance-{item['instance_id']}/mapping.json"))
    assert len(mappings)==1 and json.loads(mappings[0].read_text())==item
    slots=[item['common'],item['template']]+[s['prompt'] for s in item['steps']]
    for slot in filter(None,slots):
        path=(ROOT/slot['path']).resolve()
        assert path.is_relative_to(ROOT),'path escapes snapshot'
        data=path.read_bytes()
        assert hashlib.sha256(data).hexdigest()==slot['sha256'],slot['path']
        assert len(data)==slot['bytes'],slot['path']
        original=data[:-1] if slot['terminal_newline_added'] else data
        assert hashlib.sha256(original).hexdigest()==slot['source_sha256'],slot['path']
        seen[slot['path']]=slot['source_sha256']
    if item['template_code']=='phonics_pattern_word_teach':
        template=(ROOT/item['template']['path']).read_text()
        assert '[WORD_EVALUATION]' not in template
        assert '[STUDENT_TALK]' in template and '[TEMPLATE_FINISH]' in template
    if item['template_code'].startswith('ip_call'):
        assert [s['stepCode'] for s in item['steps']]==['intro','ipcall']
assert len(scopes)==18 and len(ids)==manifest['counts']['instances']
assert len(manifest['unexported_contexts'])==12
print(f'PASS: {len(scopes)} lessons, {len(ids)} instances, {len(seen)} exact-source prompt files; mappings and hashes match.')
print('Only a recorded terminal newline may differ from the original Forge bytes. This is not an LLM, TTS or student-end evaluation.')
