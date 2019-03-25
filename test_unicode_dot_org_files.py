"""
Read Unicode UCD format

Test files created by parse_unicode_dot_org_files.


TODO
    - test repertoire_map - non_char, math, etc.
    - how to get which reserved block a character is in?

"""

from repertoire_map import repertoire_map
from intentional_map import intentional_map
from block_map import block_map
from identifier_status_map import identifier_status_map

from more_unicodedata import is_intentional_confusion, fix_intention_confusion, show_intentional_confusion
from more_unicodedata import in_block, blocks
# from more_unicodedata import get_unicode_char
from more_unicodedata import in_reserved, is_safe_identifier, in_identifier_range, is_safe_string

PAULO_STRING = b'S\xe30 Paulo'.decode('cp1252')
MONTREAL_STRING = b'Montr\xe9al'.decode('cp1252')
INTENTIONAL_FACEBOOK_STR = 'f\u0430\u0441\u0435bo\u03bfk'
INTENTIONAL_BIGBIRD_STR = '\u1d2e\u1d35\u1d33\u1d2e\u1d35\u1d3f\u1d30'
RESERVED_STRING = '\u03A2\u0530\u05EB\u05EC\u05EE'
PROG_NOT_IDMOD_STRING_1 = '\u00aa\u00b5\u0133'
PROG_NOT_IDMOD_STRING_2 = 'h\u00aa\u00b5\u0133'
ALLOWED_STRING = '\u00c0\u00c1\u00d6'
NOT_ALLOWED_STRING = '\u00c0\u00c1\u00d6\u00aa'
OUT_OF_RANGE_STRING_1 = '\u7465\u12354'
OUT_OF_RANGE_STRING_2 = '\u2CEB1'


def test_is_intentional_confusion():
    assert(is_intentional_confusion('\u0430') is True)
    assert(is_intentional_confusion('f') is False)
    assert(is_intentional_confusion('\xe9') is False)
    assert(is_intentional_confusion('facebook') is False)
    assert(is_intentional_confusion(INTENTIONAL_FACEBOOK_STR) is True)
    assert(is_intentional_confusion(INTENTIONAL_BIGBIRD_STR) is False)  # it's not safe but not in the list!
    assert(is_intentional_confusion(RESERVED_STRING) is False)
    assert(is_intentional_confusion(OUT_OF_RANGE_STRING_1) is False)
    assert(is_intentional_confusion(OUT_OF_RANGE_STRING_2) is False)


def test_fix_intentional_confusion():
    ds = fix_intention_confusion('\u0430')
    assert (ds == 'a')

    ds = fix_intention_confusion('\xe9')
    assert (ds == '\xe9')

    ds = fix_intention_confusion('f')
    assert (ds == 'f')

    bad_str_1 = '\u0391\u0392\u0421\u0430\u01c3'  # ABCa!
    good_str = fix_intention_confusion(bad_str_1)
    assert (good_str == 'ABCa!')

    str_2 = b'S\xe30 Paulo'.decode('cp1252')
    good_str = fix_intention_confusion(PAULO_STRING)
    assert (good_str == PAULO_STRING)

    str_3 = b'Montr\xe9al'.decode('cp1252')
    good_str = fix_intention_confusion(MONTREAL_STRING)
    assert (good_str == MONTREAL_STRING)

    good_str = fix_intention_confusion(INTENTIONAL_FACEBOOK_STR)
    assert (good_str == 'facebook')

    good_str = fix_intention_confusion(INTENTIONAL_BIGBIRD_STR)
    assert (good_str != 'BIGBIRD')  # fails -- MODIFIER LETTER CAPITAL B not in intention.txt - get caugjt with NOT_XID in indentifyertype?


def test_show_intentional_confusion():
    a = show_intentional_confusion('\u0430')
    assert (len(a)==1)

    a = show_intentional_confusion('f')
    assert (len(a)==0)

    a = show_intentional_confusion(INTENTIONAL_FACEBOOK_STR)
    assert (len(a) == 4)

    a = show_intentional_confusion(INTENTIONAL_BIGBIRD_STR) # confusing but no chars in intentional list
    assert (len(a) == 0)


def test_block_map(block_map):
    assert(in_block('facebook', "Basic Latin")==True)
    assert(in_block(INTENTIONAL_FACEBOOK_STR[1:3], "Cyrillic")==True)
    assert(in_block(INTENTIONAL_BIGBIRD_STR, "Phonetic Extensions")==True)
    assert(in_block('\xe9', "Latin-1 Supplement")==True)
    assert(in_block('\xe9', "Basic Latin")==False)

    bs = blocks('facebook')
    assert(bs=={'ASCII'})

    bs = blocks(INTENTIONAL_FACEBOOK_STR)
    assert (bs == {'Cyrillic', 'ASCII', 'Greek'})

    bs = blocks(INTENTIONAL_BIGBIRD_STR)
    assert (bs == {'Phonetic_Ext'})

    bs = blocks('\xe9')
    assert (bs == {'Latin_1_Sup'})


def test_reserved_block():
    assert(in_reserved('facebook')==False)
    assert(in_reserved(RESERVED_STRING)==True)
    assert(in_reserved('\u0378')==True)

def test_identifiers():
    result = is_safe_identifier('facebook', level='ascii', allowed_chars=None)
    assert(result)

    result = is_safe_identifier(INTENTIONAL_FACEBOOK_STR, level='ascii', allowed_chars=None) is True
    assert (result is False)

    assert(is_safe_identifier('\xe9', level='ascii', allowed_chars=None) is True)
    assert(is_safe_identifier('\xe9\xe9', level='programming', allowed_chars=None) is True)
    # assert(is_identifier('\xe9\u00F1', level='programming', allowed_chars=None) is False)

    assert(is_safe_identifier('\xe9\u0300', level='ascii', allowed_chars=None) is False)
    assert(is_safe_identifier('\xe9\u0300', level='programming', allowed_chars=None) is True)

    assert(is_safe_identifier(OUT_OF_RANGE_STRING_1, level='ascii', allowed_chars=None) is False)
    assert(is_safe_identifier(OUT_OF_RANGE_STRING_1, level='programming', allowed_chars=None) is False)
    assert(is_safe_identifier(OUT_OF_RANGE_STRING_1, level='idmod', allowed_chars=None) is True)
    assert(is_safe_identifier(OUT_OF_RANGE_STRING_2, level='idmod', allowed_chars=None) is False)

    assert(is_safe_identifier('\u0100', level='ascii', allowed_chars=None) is False)
    assert(is_safe_identifier('\u0100', level='ascii', allowed_chars=['\u0100']) is True)
    assert(is_safe_identifier('\u0100', level='programming', allowed_chars=None) is True)
    assert(is_safe_identifier(PROG_NOT_IDMOD_STRING_1, level='programming', allowed_chars=None) is True)
    assert(is_safe_identifier(PROG_NOT_IDMOD_STRING_2, level='programming', allowed_chars=None) is True)
    assert(is_safe_identifier(PROG_NOT_IDMOD_STRING_1, level='idmod', allowed_chars=None) is False)
    assert(is_safe_identifier(PROG_NOT_IDMOD_STRING_2, level='idmod', allowed_chars=None) is False)
    assert(is_safe_identifier(PROG_NOT_IDMOD_STRING_2, level='idmod', allowed_chars=['\u00aa', '\u00b5', '\u0133']) is True)

def test_safe_strings():
    assert(is_safe_string('facebook', level='ascii', allowed_chars=None) is True)

    assert(is_safe_string(PAULO_STRING, level='ascii', allowed_chars=None) is False)
    assert(is_safe_string(PAULO_STRING, level='latin', allowed_chars=None) is True)

    assert (is_safe_string(MONTREAL_STRING, level='ascii', allowed_chars=None) is False)
    assert (is_safe_string(MONTREAL_STRING, level='latin', allowed_chars=None) is True)

    assert(is_safe_string(INTENTIONAL_FACEBOOK_STR, level='ascii', allowed_chars=None) is False)
    assert(is_safe_string(INTENTIONAL_FACEBOOK_STR, level='unrestricted', allowed_chars=None) is True)

    assert (is_safe_string('\xe9', level='ascii', allowed_chars=None) is False)
    assert (is_safe_string('\xe9', level='latin', allowed_chars=None) is True)

    assert (is_safe_string('\xe9\u0300', level='latin', allowed_chars=None) is False) # \u0300 in Diacriticals
    assert (is_safe_string('\xe9\u0300', level='latin', allowed_chars=['\u0300']) is True)

    assert (is_safe_string(OUT_OF_RANGE_STRING_1, level='ascii', allowed_chars=None) is False)
    assert (is_safe_string(OUT_OF_RANGE_STRING_1, level='latin', allowed_chars=None) is False)
    assert (is_safe_string(OUT_OF_RANGE_STRING_1, level='allowed', allowed_chars=None) is False)
    assert (is_safe_string(OUT_OF_RANGE_STRING_1, level='unrestricted', allowed_chars=None) is True)

    assert (is_safe_string(PROG_NOT_IDMOD_STRING_1, level='ascii', allowed_chars=None) is False)
    assert (is_safe_string(PROG_NOT_IDMOD_STRING_1, level='latin', allowed_chars=None) is True)
    assert (is_safe_string(PROG_NOT_IDMOD_STRING_1, level='allowed', allowed_chars=None) is False)
    assert (is_safe_string(PROG_NOT_IDMOD_STRING_1, level='unrestricted', allowed_chars=None) is True)

    assert (is_safe_string(ALLOWED_STRING, level='allowed', allowed_chars=None) is True)
    assert (is_safe_string(NOT_ALLOWED_STRING, level='allowed', allowed_chars=None) is False)
    assert (is_safe_string(NOT_ALLOWED_STRING, level='allowed', allowed_chars=['\u00AA']) is True)


# def find_prog_not_idmod():
#     # utility function to find characters that are valid in programming IDs (XID_Start or XID_Continue) but not
#     #   for idmod (i.e. not in an allowed indentifier_status block
#     exceptions = []
#     for c in repertoire_map.keys():
#         uc = get_unicode_char(c, repertoire_map)
#         in_idr = in_identifier_range(chr(c))
#         if uc.xid_continue == 1 and not in_idr:
#             exceptions.append(c)
#     return exceptions


if __name__ == '__main__':
    test_is_intentional_confusion()
    test_fix_intentional_confusion()
    test_show_intentional_confusion()
    test_block_map(block_map)
    test_reserved_block()
    test_identifiers()
    test_safe_strings()