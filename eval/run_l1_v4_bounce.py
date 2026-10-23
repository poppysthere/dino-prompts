#!/usr/bin/env python3
"""Scoped first-sound/chunk regression; no audio scoring or Forge deployment.

Supersedes the pronunciation expectations in run_l1_v4_forge.py, which
describe the earlier full-decomposition policy. Uses its shared prompt filler.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.request

from backends import ForgeBackend
from run_l1_v4_forge import fill, spoken, SILENCE, NOISE
from tts_punctuation import punctuation_issues

ROOT = Path(__file__).resolve().parent.parent
PROMPTS = ROOT / 'prompts/l1-v4'
BASELINE = 'dbf2ad0'
MODEL = 'gpt5.6LunaChatModel'
UNITS = {'apple': {'æ', 'p', 'ə', 'l', 'æp', 'əl'},
         'bread': {'b', 'r', 'ɛ', 'd', 'br', 'ɛd'},
         'juice': {'dʒ', 'uː', 's', 'dʒuː'}}
FIRST = {'apple': 'æ', 'bread': 'b', 'juice': 'dʒ'}
CHUNKS = {'apple': {'æp', 'əl'}, 'bread': {'br', 'ɛd'}, 'juice': {'dʒuː'}}
IPA = re.compile(r'/([^/\s]+)/')
CONTROL = re.compile(r'\[(?:STUDENT_TALK|NEXT_STEP|TEMPLATE_FINISH)\]')


def template(word):
    return (PROMPTS / f'word_teaching_rules_l1l2_{word}.md').read_text()


def cases():
    result = []
    for word in UNITS:
        unit = {'apple': 'l', 'bread': 'r', 'juice': 's'}[word]
        request = f'The {unit} sound is hard. Help me say {word}.'
        for name, turns, extra in [
            ('instant', [word], {'no_drill': True}),
            ('meaningful', [f'I like {word}.'], {'no_drill': True}),
            ('approximation', [{'apple': 'appo', 'bread': 'bred', 'juice': 'joos'}[word]], {'no_drill': True}),
            ('slower', ['Please say it slowly.', word], {'chunk_reply': 2}),
            ('specific-sound', [request, word], {'unit_reply': 2, 'unit': unit}),
            ('help-after-attempt', ['yes', f'{word}. But {request}', word], {'unit_reply': 3, 'unit': unit}),
            ('unclear', ['[unclear speech]', word], {'neutral_reply': 2}),
            ('ambiguous-asr', [{'apple': 'able', 'bread': 'bed', 'juice': 'jute'}[word], word], {'asr_help': True}),
            ('silence', [SILENCE] * 3, {}),
            ('instruction', ['What do I do?', word], {'instruction_reply': 2}),
            ('name', ["Teacher, what's your name?", word], {'name_reply': 2}),
            ('terminal-help', ['yes', 'I do not know.', 'Please say it slowly.'], {'terminal_help': True}),
        ]:
            result.append({'id': f'{word}-{name}', 'word': word, 'turns': turns, **extra})
        for name, turns, extra in [
            ('partial', [{'apple': 'app', 'bread': 'bre', 'juice': 'jew'}[word], word], {'partial_help': True}),
            ('real-short-comment', ['my dog black', word], {'topic_reply': 2, 'topic': r'black.*dog|dog.*black'}),
            ('real-question', [f'Do you like {word}?', word], {'answer_reply': 2}),
            ('real-need', ['I need water.', word], {'topic_reply': 2, 'topic': r'water'}),
        ]:
            result.append({'id': f'{word}-{name}', 'word': word, 'turns': turns, **extra})
    result.extend([
        {'id': 'bread-bed-black-brad', 'word': 'bread', 'turns': ['bed', 'black', 'brad'],
         'asr_help': True, 'neutral_reply': 3, 'no_colour_reply': 3},
        {'id': 'bread-topic-correction', 'word': 'bread', 'turns': ['bed', 'No, I mean my bed.', 'bread'],
         'asr_help': True, 'topic_reply': 3, 'topic': r'bed'},
        {'id': 'juice-unseen-partial', 'word': 'juice', 'turns': ['ju', 'juice'], 'partial_help': True},
        {'id': 'bread-one-word-real-answer', 'word': 'bread', 'turns': ['I have a dog.', 'black', 'bread'],
         'scripted_teacher': {'2': 'What color is your dog?[TEACHER_LISTEN][STUDENT_TALK]'},
         'topic_reply': 3, 'topic': r'black'},
    ])
    return result


def check_reply(word, text, repetition=False):
    issues = punctuation_issues(text, UNITS[word])
    body = spoken(text)
    first_tag = re.search(r'\[[A-Z_]+\]', text)
    if first_tag and spoken(text[first_tag.start():]):
        issues.append('Speech follows an action/control tag')
    if re.search(r'\b(?:crunch|glug|munch|so brave|big thumbs up|you said|you tried so hard)\b', body, re.I):
        issues.append('Scripted victory speech or action noise')
    tags = CONTROL.findall(text)
    if len(tags) != 1 or not text.endswith(tags[0]):
        issues.append('Invalid terminal control tag')
    if '[STUDENT_TALK]' in text and not text.endswith('[TEACHER_LISTEN][STUDENT_TALK]'):
        issues.append('Missing listening suffix')
    units = IPA.findall(body)
    if any(u not in UNITS[word] for u in units):
        issues.append('Unapproved IPA unit')
    if NOISE.search(body):
        issues.append('Written laughter/cheering')
    if re.search(r'can you say\b', body, re.I):
        issues.append('Question-form repetition instruction')
    if re.search(r"(?:I(?:'ll| will)|let me|let's)\s+(?:say|speak|go|read|do).{0,35}slow|I(?:'ll| will) slow|more slowly", body, re.I):
        issues.append('Unsupported speed promise')
    if re.search(r"you (?:missed|forgot|dropped|left out|pronounced)|your .{0,25}(?:wrong|incorrect)", body, re.I):
        issues.append('Unsupported pronunciation diagnosis')
    if repetition and not re.search(r'\b' + word + r'[.!]\s*$', body, re.I):
        issues.append('Target word is not last in repetition speech')
    if repetition and not re.search(r'\b(?:your turn|try|say)\b', body, re.I):
        issues.append('No clear repetition instruction')
    if units and not re.search(r'\b' + word + r'\b', body[body.rfind('/') + 1:], re.I):
        issues.append('No whole word after support unit')
    return issues


def check(case, messages):
    word = case['word']
    replies = [m['text'] for m in messages if m['role'] == 'assistant']
    errors = []
    for i, reply in enumerate(replies, 1):
        repetition = '[STUDENT_TALK]' in reply and str(i) not in case.get('scripted_teacher', {})
        errors.extend(f'Reply {i}: {e}' for e in check_reply(word, reply, repetition))
    if not 2 <= len(replies) <= 4 or not replies[-1].endswith('[TEMPLATE_FINISH]'):
        errors.append('Wrong finish/turn budget')
    opening = re.search(r'Say exactly this, nothing more:\n([^\n]+)', template(word)).group(1)
    if replies[0] != opening:
        errors.append('Opening differs from approved bounce model')
    finish = re.search(r'(?:HANDOVER|FINISH) LINE[^\n]*: "([^"]+)"', template(word)).group(1)
    if finish not in replies[-1]:
        errors.append('Inherited handoff missing')
    if word == 'juice' and not replies[-1].endswith('[TEACHER_DRINK_JUICE][TEMPLATE_FINISH]'):
        errors.append('Missing final drinking action suffix')
    if case.get('no_drill') and (len(replies) != 2 or IPA.search(replies[-1])):
        errors.append('Unnecessary drill after understandable attempt')
    if case.get('partial_help'):
        if len(replies) < 3 or '[TEMPLATE_FINISH]' in replies[1]:
            errors.append('Partial attempt treated as immediate whole-word success')
        if not IPA.search(replies[1]):
            errors.append('Partial attempt received no focused model')
    if case.get('topic_reply'):
        index = case['topic_reply'] - 1
        if index >= len(replies) or not re.search(case['topic'], spoken(replies[index]), re.I):
            errors.append('Real conversational meaning not acknowledged')
        elif IPA.search(replies[index]):
            errors.append('Genuine conversation treated as a pronunciation error')
    if case.get('answer_reply'):
        index = case['answer_reply'] - 1
        if index >= len(replies) or not re.search(r"\b(?:yes|I like|I love|I do|I don't|I cannot|I can't)\b", spoken(replies[index]), re.I):
            errors.append('Preference question not answered')
    if case.get('no_colour_reply'):
        index = case['no_colour_reply'] - 1
        if index < len(replies) and re.search(r'black|colou?r', spoken(replies[index]), re.I):
            errors.append('Ambiguous repetition interpreted as a colour topic')
    if case.get('asr_help'):
        if len(replies) < 3 or not IPA.search(replies[1]) or '[TEMPLATE_FINISH]' in replies[1]:
            errors.append('Ambiguous ASR skipped tentative support')
        if re.search(r'you said\s+' + word, spoken(replies[1]), re.I):
            errors.append('Claimed ambiguous ASR as confirmed whole-word success')
        if re.search(r'\b' + re.escape(case['turns'][0]) + r'\b', spoken(replies[1]), re.I):
            errors.append('Echoed ambiguous near-target ASR as a new topic')
    for key in ('chunk_reply', 'unit_reply', 'neutral_reply', 'instruction_reply', 'name_reply'):
        if key not in case:
            continue
        index = case[key] - 1
        if index >= len(replies):
            errors.append(f'{key}: missing response')
            continue
        body = spoken(replies[index])
        units = set(IPA.findall(body))
        if key == 'chunk_reply' and not (units & CHUNKS[word]):
            errors.append('Slow request did not receive a useful chunk')
        if key == 'unit_reply' and units != {case['unit']}:
            errors.append('Requested sound was not modelled selectively')
        if key == 'neutral_reply' and units:
            errors.append('Unclear ASR received a speculative sound correction')
        if key == 'instruction_reply' and not re.search(r'listen|say|try', body, re.I):
            errors.append('Instruction question not answered')
        if key == 'name_reply' and not re.search(r"(?:I am|I'm|my name is) Kim", body, re.I):
            errors.append('Name question not answered')
    if case.get('terminal_help') and not (set(IPA.findall(replies[-1])) & CHUNKS[word]):
        errors.append('Final-turn slower request ignored')
    return errors


def offline():
    allowed = {'common_teaching_simple_rules.md', *(f'word_teaching_rules_l1l2_{w}.md' for w in UNITS), 'README.md'}
    paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASELINE, 'prompts/l1-v4'], cwd=ROOT, text=True).splitlines()
    for path in paths:
        old = subprocess.check_output(['git', 'show', f'{BASELINE}:{path}'], cwd=ROOT, text=True)
        new = (ROOT / path).read_text()
        if Path(path).name not in allowed:
            assert new == old, f'Unrelated prompt changed: {path}'
        assert set(re.findall(r'\[[A-Z_]+\]', old)) == set(re.findall(r'\[[A-Z_]+\]', new)), path
        if Path(path).name.startswith('word_'):
            assert 'maximum of four teacher replies' in new, path
            destination = 'play with A' if 'apple.md' in path else 'play with B' if 'bread.md' in path else 'drink like Boo'
            assert destination in new, path
    for word, sound in FIRST.items():
        good = f'Listen. /{sound}/ /{sound}/ {word}. Your turn. {word.capitalize()}.[TEACHER_LISTEN][STUDENT_TALK]'
        assert not check_reply(word, good, True)
        for bad in [good.replace(f'Your turn. {word.capitalize()}.', 'Your turn.'),
                    good.replace(f'Your turn. {word.capitalize()}.', f'Can you say {word}?'),
                    good.replace('Listen.', 'You forgot a sound.'),
                    good.replace('Listen.', "I'll speak slowly."),
                    good.replace(f'/{sound}/', '/x/'),
                    good.replace('Listen.', 'Let’s try.'),
                    good.replace('Listen.', 'CRUNCH.'),
                    good.replace('Listen.', '[TEACHER_APPLAUD]Listen.'),
                    good + '[NEXT_STEP]']:
            assert check_reply(word, bad, True)
        assert not check_reply(word, f'Listen. /{next(iter(CHUNKS[word]))}/. Your turn. {word}.[TEACHER_LISTEN][STUDENT_TALK]', True)
    print('Scope, handoff, tag vocabulary, punctuation and checker fixtures: PASS')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--only', action='append')
    args = parser.parse_args()
    offline()
    if not args.live:
        return 0
    os.environ.setdefault('FORGE_BASE_URL', 'http://dino-test-alb-2087276790.ap-southeast-1.elb.amazonaws.com/cms/api')
    os.environ.setdefault('FORGE_PROVIDER', 'Azure OpenAI')
    os.environ['FORGE_MODEL'] = MODEL
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    output = ROOT / 'eval/runs' / f'l1_v4_bounce_{stamp}'
    output.mkdir(parents=True)
    report = {'model': MODEL, 'baseline': BASELINE, 'tts_audio': 'not tested',
              'prompt_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in PROMPTS.glob('*.md')},
              'cases': {}}
    try:
        backend = ForgeBackend()
        req = urllib.request.Request(backend.base + '/classroom-debug/models', headers={'Authorization': backend.token})
        with urllib.request.urlopen(req, timeout=20) as response:
            catalog = json.load(response)
        if catalog.get('code') != 200 or 'gpt-5.6-luna' not in json.dumps(catalog.get('data')):
            raise RuntimeError('Model catalog preflight failed')
    except Exception as exc:
        report['blocked'] = f'{type(exc).__name__}; HTTP status {getattr(exc, "code", "unavailable")}'
        (output / 'report.json').write_text(json.dumps(report, indent=2))
        print('Forge preflight blocked: ' + report['blocked'])
        print(output / 'report.json')
        return 2
    common = fill((PROMPTS / 'common_teaching_simple_rules.md').read_text())
    def run(case):
        messages = []
        history = [{'role': 'user', 'content': 'The UI is ready. Start the current stage.'}]
        system = common + '\n\n' + fill(template(case['word']))
        try:
            for turn in range(4):
                reply = case.get('scripted_teacher', {}).get(str(turn + 1))
                if reply is None:
                    reply = backend.chat(system, history)
                messages.append({'role': 'assistant', 'text': reply})
                history.append({'role': 'assistant', 'content': reply})
                if '[TEMPLATE_FINISH]' in reply or '[NEXT_STEP]' in reply:
                    break
                child = case['turns'][turn] if turn < len(case['turns']) else SILENCE
                messages.append({'role': 'user', 'text': child})
                history.append({'role': 'user', 'content': child})
            issues = check(case, messages)
        except Exception as exc:
            issues = [f'Backend error: {type(exc).__name__}']
        result = {'case': case, 'messages': messages, 'issues': issues}
        (output / (case['id'] + '.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2))
        return case['id'], issues
    selected = [c for c in cases() if not args.only or c['id'] in args.only]
    if not selected:
        parser.error('No matching cases')
    with ThreadPoolExecutor(max_workers=3) as pool:
        for future in as_completed([pool.submit(run, c) for c in selected]):
            name, issues = future.result()
            report['cases'][name] = {'passed': not issues, 'issues': issues}
            print(('FAIL ' if issues else 'PASS ') + name + (': ' + '; '.join(issues) if issues else ''), flush=True)
            (output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    passed = sum(c['passed'] for c in report['cases'].values())
    print(f'{passed}/{len(selected)} passed. Report: {output / "report.json"}')
    return 0 if passed == len(selected) else 1


if __name__ == '__main__':
    raise SystemExit(main())
