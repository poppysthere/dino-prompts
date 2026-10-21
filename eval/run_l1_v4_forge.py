#!/usr/bin/env python3
"""L1 V4 regression eval against the pinned main L1 source (not L1 V2).

--offline checks source scope and the checker with synthetic fixtures only.
The default runs real conversations through Forge; it never deploys prompts.
"""
import argparse
import datetime as dt
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.request

from backends import ForgeBackend

ROOT = Path(__file__).resolve().parent.parent
PROMPTS = ROOT / 'prompts/l1-v4'
SOURCE = '829e768bb58a7302ed6987867a36ccc9431419b3'
MODEL = 'gpt5.6LunaChatModel'
PHONEMES = {'apple': 'a...p...uh...l', 'bread': 'b...r...e...d', 'juice': 'j...oo...s'}
FILES = {
    'warmup': 'warmup_teaching_rules_l1l2.md',
    'intro': 'sentence_teaching_rules_l1l2_pre_video.md',
    'like': 'sentence_teaching_rules_l1l2_i_like_bread.md',
    'dislike': 'sentence_teaching_rules_l1l2_i_dont_like_apples.md',
    'wrapup': 'wrapup_teaching_rules_l1l2.md',
    **{word: f'word_teaching_rules_l1l2_{word}.md' for word in PHONEMES},
}
SKIPPED = ['leadin_teaching_rules_l1_step_pre_video.md',
           'leadin_teaching_rules_l1_step_post_video.md']
NOISE = re.compile(r'\b(?:ha[\s-]*ha(?:ha)*|he[\s-]*he|hee[\s-]*hee|teehee|yay|woo[\s-]*hoo)\b', re.I)
CONTROL = re.compile(r'\[(?:STUDENT_TALK|NEXT_STEP|TEMPLATE_FINISH|WORD_EVALUATION)\]')
SILENCE = 'The student has been silent for 7 seconds. Give one short encouraging nudge and continue.'


def cases():
    result = []
    for word in PHONEMES:
        for name, turns in [
            ('normal', ['yes', word]),
            ('instant', [word]),
            ('slower', ['Please say it slowly.', word]),
            ('confused', ["I don't understand.", word]),
            ('noise', ['haha yay woohoo', word]),
            ('silent', [SILENCE] * 3),
        ]:
            result.append({'id': f'{word}-{name}', 'family': word, 'turns': turns,
                           'phoneme_reply': None if name == 'instant' else 2})
    for name, turns, require in [
        ('bread', ['bread'], r'^(?:you like bread|bread for you|bread)'),
        ('juice', ['I like juice'], r'^(?:you like juice|juice for you|juice)'),
        ('other-food', ['I like cake'], r'^[^.!?]*cake'),
        ('own-language', ['我喜欢面包'], r'^[^.!?]*bread'),
        ('noise', ['haha yay'], None),
        ('silent', [SILENCE], None),
    ]:
        result.append({'id': f'wrapup-{name}', 'family': 'wrapup', 'turns': turns,
                       'reaction': require})
    result.extend([
        {'id': 'warmup-happy', 'family': 'warmup', 'turns': ['Mia', 'happy']},
        {'id': 'warmup-silent', 'family': 'warmup', 'turns': [SILENCE] * 3},
        {'id': 'sentence-intro', 'family': 'intro', 'turns': []},
        {'id': 'sentence-like', 'family': 'like', 'turns': ['yes', 'I like bread']},
        {'id': 'sentence-dislike', 'family': 'dislike', 'turns': ['yes', "I don't like apples"]},
    ])
    return result


def fill(text):
    values = {'roleDescription': 'You are Kim, a warm, patient English teacher.',
              'teacherName': 'Kim', 'name': 'Mia', 'studentProfile': 'No additional information.',
              'renderContent': 'Chef Boo has apples, juice, and bread. Follow the current stage template.'}
    for key, value in values.items():
        text = text.replace('{{' + key + '}}', value)
    return text


def spoken(text):
    return re.sub(r'\[[A-Z_]+\]', '', text).strip()


def check(case, messages):
    family = case['family']
    replies = [m['text'] for m in messages if m['role'] == 'assistant']
    issues = []
    expected_finish = '[NEXT_STEP]' if family in ('intro', 'like', 'wrapup') else '[TEMPLATE_FINISH]'
    if not replies:
        return ['No model replies']
    maximum = 1 if family == 'intro' else 2 if family == 'wrapup' else 4
    if len(replies) > maximum:
        issues.append(f'Turn limit exceeded: {len(replies)} > {maximum}')
    for i, reply in enumerate(replies, 1):
        tags = CONTROL.findall(reply)
        if len(tags) != 1 or not reply.rstrip().endswith(tags[0]):
            issues.append(f'Reply {i}: invalid control tag placement')
        elif tags[0] != ('[STUDENT_TALK]' if i < len(replies) else expected_finish):
            issues.append(f'Reply {i}: wrong control tag {tags[0]}')
        if '[STUDENT_TALK]' in reply and family != 'warmup' and not reply.rstrip().endswith('[TEACHER_LISTEN][STUDENT_TALK]'):
            issues.append(f'Reply {i}: missing listening action')
        body = spoken(reply)
        if NOISE.search(body):
            issues.append(f'Reply {i}: written laughter or cheering noise')
        remainder = body.lower().replace(PHONEMES.get(family, '__no_sound_model__'), '')
        if '...' in remainder or '…' in remainder:
            issues.append(f'Reply {i}: ellipsis outside the approved sound model')
        if family in PHONEMES and PHONEMES[family] in body.lower():
            model = re.escape(PHONEMES[family])
            if not re.search(r'\b' + family + r'[.! ,]*' + model + r'[.! ,]*' + family + r'\b', body, re.I):
                issues.append(f'Reply {i}: missing whole word before/after sounds')
        if re.search(r'[\u4e00-\u9fff]', body):
            issues.append(f'Reply {i}: non-English speech')
    index = case.get('phoneme_reply')
    if index and (len(replies) < index or PHONEMES[family] not in spoken(replies[index-1]).lower()):
        issues.append(f'Reply {index}: missing sound model')
    if family in PHONEMES:
        template = (PROMPTS / FILES[family]).read_text()
        opening = re.search(r'Say exactly this, nothing more:\n([^\n]+)', template).group(1)
        if spoken(replies[0]).lower() != spoken(fill(opening)).lower():
            issues.append('Inherited word opener changed')
        finish = re.search(r'(?:HANDOVER|FINISH) LINE[^\n]*: "([^"]+)"', template).group(1)
        if spoken(finish).lower() not in spoken(replies[-1]).lower():
            issues.append('Inherited word handoff missing')
        if case['id'].endswith('-instant') and len(replies) != 2:
            issues.append('Instant word try did not finish on reply 2')
    if family == 'wrapup':
        if not spoken(replies[0]).endswith('So, what do you like?'):
            issues.append('Missing simple preference question')
        if spoken(replies[0]).count('?') != 1:
            issues.append('Wrap-up must ask one question')
        if len(replies) == 2:
            if '?' in spoken(replies[1]):
                issues.append('Wrap-up asked a second question')
            if case.get('reaction') and not re.search(case['reaction'], spoken(replies[1]), re.I):
                issues.append('Wrap-up did not acknowledge the actual food first')
            if '[TEACHER_POINT_TO_SCREEN][NEXT_STEP]' not in replies[1]:
                issues.append('Missing song handoff action')
    return issues


def offline():
    errors, changes = [], {}
    names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', SOURCE, 'prompts/l1'], cwd=ROOT, text=True).splitlines()
    for original in names:
        name = Path(original).name
        before = subprocess.check_output(['git', 'show', f'{SOURCE}:{original}'], cwd=ROOT, text=True)
        after = (PROMPTS / name).read_text()
        if before != after:
            changes[name] = list(difflib.unified_diff(before.splitlines(), after.splitlines(), fromfile=original, tofile=f'prompts/l1-v4/{name}', lineterm=''))
        if name != 'common_teaching_simple_rules.md' and NOISE.search(after):
            errors.append(f'{name}: laughter/cheer example remains')
        if name in SKIPPED or name == FILES['intro']:
            if before != after:
                errors.append(f'{name}: unrelated source change')
        if set(re.findall(r'\[[A-Z_]+\]', before)) != set(re.findall(r'\[[A-Z_]+\]', after)):
            errors.append(f'{name}: original tag vocabulary changed')
    for word, model in PHONEMES.items():
        text = (PROMPTS / FILES[word]).read_text()
        if model not in text or 'Whole words only, for the voice engine:' in text:
            errors.append(f'{word}: sound model missing or contradicted')
    sample = [
        {'role': 'assistant', 'text': 'So, what do you like?[TEACHER_LISTEN][STUDENT_TALK]'},
        {'role': 'user', 'text': 'bread'},
        {'role': 'assistant', 'text': "You like bread. Let's sing.[TEACHER_POINT_TO_SCREEN][NEXT_STEP]"},
    ]
    case = {'id': 'fixture', 'family': 'wrapup', 'reaction': r'^You like bread'}
    if check(case, sample):
        errors.append('Checker rejected a valid synthetic fixture')
    for replacement in ['Yay. You like bread.[TEACHER_POINT_TO_SCREEN][NEXT_STEP]',
                        'You like bread... Now sing.[TEACHER_POINT_TO_SCREEN][NEXT_STEP]',
                        'You like bread.[TEMPLATE_FINISH]']:
        bad = sample[:-1] + [{'role': 'assistant', 'text': replacement}]
        if not check(case, bad):
            errors.append('Checker missed an injected defect')
    for word, model in PHONEMES.items():
        template = (PROMPTS / FILES[word]).read_text()
        opening = re.search(r'Say exactly this, nothing more:\n([^\n]+)', template).group(1)
        finish = re.search(r'(?:HANDOVER|FINISH) LINE[^\n]*: "([^"]+)"', template).group(1)
        fixture = [
            {'role': 'assistant', 'text': fill(opening)},
            {'role': 'user', 'text': 'Please say it slowly.'},
            {'role': 'assistant', 'text': f'Listen. {word}. {model}. {word}. Your turn. {word}.[TEACHER_LISTEN][STUDENT_TALK]'},
            {'role': 'user', 'text': word},
            {'role': 'assistant', 'text': f'You said {word}! {finish}[TEMPLATE_FINISH]'},
        ]
        sample_case = {'id': f'{word}-fixture', 'family': word, 'phoneme_reply': 2}
        if check(sample_case, fixture):
            errors.append(f'{word}: checker rejected approved phoneme notation')
        broken = [dict(m) for m in fixture]
        broken[2]['text'] = broken[2]['text'].replace(model, 'x...y...z')
        if not check(sample_case, broken):
            errors.append(f'{word}: checker accepted incorrect sound segmentation')
    return {'source_commit': SOURCE, 'offline_passed': not errors, 'issues': errors,
            'changes': changes, 'skipped_source_placeholders': SKIPPED,
            'live_status': 'not_run', 'tts_audio_status': 'not_tested'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--plan', action='store_true')
    parser.add_argument('--only', action='append')
    args = parser.parse_args()
    selected = [c for c in cases() if not args.only or c['id'] in args.only]
    if not selected:
        parser.error('No matching cases')
    if args.plan:
        print(json.dumps({'model': MODEL, 'cases': [c['id'] for c in selected], 'skipped': SKIPPED}, indent=2))
        return 0
    report = offline()
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output = ROOT / 'eval/runs' / f'l1_v4_{stamp}'
    output.mkdir(parents=True)
    report['prompt_sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in PROMPTS.glob('*.md')}
    report['model'] = MODEL
    report['cases'] = {}
    def save():
        (output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    if args.offline or report['issues']:
        save()
        print(f"Offline checks: {'PASS' if report['offline_passed'] else 'FAIL'}; no model calls.")
        print(f'Report: {output / "report.json"}')
        return 0 if report['offline_passed'] else 1
    os.environ.setdefault('FORGE_BASE_URL', 'http://dino-test-alb-2087276790.ap-southeast-1.elb.amazonaws.com/cms/api')
    os.environ.setdefault('FORGE_PROVIDER', 'Azure OpenAI')
    os.environ['FORGE_MODEL'] = MODEL
    try:
        backend = ForgeBackend()
        req = urllib.request.Request(backend.base + '/classroom-debug/models', headers={'Authorization': backend.token})
        with urllib.request.urlopen(req, timeout=20) as response:
            catalog = json.load(response)
        if catalog.get('code') != 200 or 'gpt-5.6-luna' not in json.dumps(catalog.get('data')):
            raise RuntimeError('Forge model preflight failed')
    except Exception as exc:
        report['live_status'] = 'blocked'
        report['error'] = f'{type(exc).__name__}; HTTP status {getattr(exc, "code", "unavailable")}'
        save()
        print(f'Forge preflight blocked: {report["error"]}. Report: {output / "report.json"}')
        return 2
    common = fill((PROMPTS / 'common_teaching_simple_rules.md').read_text())
    for case in selected:
        print(f'Running {case["id"]} ...', flush=True)
        system = common + '\n\n' + fill((PROMPTS / FILES[case['family']]).read_text())
        history = [{'role': 'user', 'content': 'The UI is ready. Start the current stage.'}]
        messages = []
        try:
            for turn in range(5):
                reply = backend.chat(system, history)
                messages.append({'role': 'assistant', 'text': reply})
                history.append({'role': 'assistant', 'content': reply})
                if '[NEXT_STEP]' in reply or '[TEMPLATE_FINISH]' in reply:
                    break
                child = case['turns'][turn] if turn < len(case['turns']) else SILENCE
                messages.append({'role': 'user', 'text': child})
                history.append({'role': 'user', 'content': child})
            issues = check(case, messages)
        except Exception as exc:
            issues = [f'Backend error: {type(exc).__name__}']
        report['cases'][case['id']] = {'passed': not issues, 'issues': issues}
        (output / (case['id'] + '.json')).write_text(json.dumps({'case': case, 'messages': messages, 'issues': issues}, ensure_ascii=False, indent=2))
        print(('FAIL ' if issues else 'PASS ') + case['id'] + (': ' + '; '.join(issues) if issues else ''), flush=True)
        save()
    report['live_status'] = 'completed'
    report['passed'] = sum(c['passed'] for c in report['cases'].values())
    save()
    print(f'{report["passed"]}/{len(selected)} passed. Report: {output / "report.json"}')
    return 0 if report['passed'] == len(selected) else 1


if __name__ == '__main__':
    sys.exit(main())
