"""Check spoken punctuation without normalizing or moving tags/approved IPA."""
import re
import string
import unicodedata

ALLOWED = set(".,!?'")
TAGS = re.compile(r'\[(?:TEACHER_[A-Z_]+|STUDENT_TALK|NEXT_STEP|TEMPLATE_FINISH|WORD_EVALUATION)\]')


def punctuation_issues(text, ipa_units=()):
    body = TAGS.sub('', text)
    for unit in sorted(ipa_units, key=len, reverse=True):
        body = body.replace('/' + unit + '/', '')
    bad = sorted({ch for ch in body if ch not in ALLOWED and (
        ch in string.punctuation or unicodedata.category(ch).startswith(('P', 'S'))
        or (ch.isspace() and not ch.isascii()))})
    issues = ['Disallowed spoken punctuation: ' + ', '.join(f'U+{ord(ch):04X}' for ch in bad)] if bad else []
    if re.search(r'\.\s*\.\s*\.', body):
        issues.append('Spoken ellipsis')
    return issues


def self_test():
    valid = ["I'm here. Don't worry. Let's try Tom's word! Ready?",
             "Listen. /æp/ /əl/ apple.[TEACHER_LISTEN][STUDENT_TALK]",
             "Juice. /dʒ/ /uː/ /s/ juice.[TEACHER_APPLAUD][TEMPLATE_FINISH]"]
    units = {'æp', 'əl', 'dʒ', 'uː', 's'}
    assert all(not punctuation_issues(text, units) for text in valid)
    for invalid in ["Let’s say apple.", "I‘m here.", "Tom’s apple.", '“Apple.”',
                    'Ｉ＇ｍ here．', 'Apple， bread！', 'Ready？', 'Listen： apple；',
                    'Listen: apple;', 'Uh-oh!', 'Apple—bread.', 'Apple–bread.',
                    'Apple…', 'Apple...', 'Apple. . .', '"Apple."', '(Apple)',
                    'Apple/bread.', 'Apple　bread.', '[UNKNOWN_TAG]Apple.']:
        assert punctuation_issues(invalid, units), repr(invalid)


if __name__ == '__main__':
    self_test()
    print('TTS punctuation fixtures: PASS')
