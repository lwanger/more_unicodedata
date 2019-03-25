"""
Read Unicode.org data files and create python importable data  from them

files read:

    - intention.txt - intentionally confusiong characters

TODO
    - test...
    - parse other unicode.org files...
    - add emoji to repertoire map and emoji_map.... read @missing?
        https://www.unicode.org/reports/tr51/index.html / https://www.unicode.org/Public/emoji/11.0/
        - presentation_modifier? (variation sequences - emoji followed by presentation selector or text presentation selector)
        - Emoji properties (Annex A: https://www.unicode.org/reports/tr51/index.html#Identification)emoji, emoji_presentation, enoji-modifier, emoji-modifier-base, emohi-component, extended_pictograph
        - text-default, emoji-default
        - CLDR - Unicode Common Locale Data Repository (http://cldr.unicode.org/). Emoji ordering chart?
    - continue on TR39 - block restricted characters - look at IdeentifierType (NOT_XID and XID_RESTRICTED, Limited_Use, Technical, Obsolete, etc.?)
    - identify confusables (confusable detection)
    - rate string for spoofing level (ascii only, one script, unrestricted, etc.)

    - write tests - identifiers, danger levels, etc.

"""

from pathlib import Path
import sys
from typing import Dict
from xml.etree import ElementTree as ET

from more_unicodedata_types import UnicodeChar
from more_unicodedata_types import UnicodeReserved
from more_unicodedata_types import UnicodeBlock
from more_unicodedata_types import UnicodeIdentifierStatus
from more_unicodedata_types import UnicodeIdentifierType


def make_intentional_map() -> Dict:
    # create the dictionary for the intention map -- reading from intentional.txt
    filename = Path('./import/intentional.txt').resolve()
    char_map = {}

    with open(filename, 'r', encoding='utf8') as f:
        _ = f.readline()          # burn first line

        for l in f:
            if l[0] in {'#', '\n'}: # comment or blank line
                continue

            # parse the line - for example - 0021; 01 C3  # * ( ! ~ Çƒ ) EXCLAMATION MARK ~ LATIN LETTER RETROFLEX CLICK
            semicolon_idx = l.find(';')
            code_point = l[0:semicolon_idx].strip()
            fields = l[semicolon_idx+1:]

            ampersand_idx = fields.find('#')
            close_paren_idx = fields.find(')')
            tilde_idx = fields.rfind('~')
            key_char = fields[0:ampersand_idx].strip()
            key_char_comment = fields[tilde_idx + 1:].strip()
            intended_char_comment = fields[close_paren_idx + 1:tilde_idx].strip()

            chr_char = chr(int('0x'+key_char, 0))
            chr_intended_char = chr(int('0x' + code_point, 0))
            char_map[chr_char] = (chr_intended_char, key_char_comment, intended_char_comment)

    return char_map


def write_intentional_map_file(intentional_map, f):
    # write intentional map to a file
    f.write('# dictionary to map unicode characters to canonical characters\n')
    f.write('# entries are tuples of -- key: code_point, name1, name2\n')
    f.write('# where: key - code point of the confusing char, code_point - code point of the character that it confuses,\n')
    f.write('#    name1 - the name of the confusing char, name2 - the name of the char that it confuses\n')
    f.write('#\n')
    f.write('# This dictionary can be used to reduce confusion by mapping to the canonical (non-confusing) letter\n')
    f.write('intentional_map = {\n')
    for k,v in intentional_map.items():
        f.write(f'    0x{ord(k):04x}: ( 0x{ord(v[0]):04X}, "{v[1]}", "{v[2]}" ),\n')
    f.write('}\n')


def make_unicode_char(node):
    a = node.attrib
    if 'first-cp' in a:
        uc = UnicodeChar(name=a['na'], is_range=True, code_point=a['first-cp'], last_code_point=a['last-cp'], block=a['blk'], alpha=a['Alpha'],
                         math=a['Math'], non_char=a['NChar'], deprecated=a['Dep'], xid_start=a['XIDS'], xid_continue=a['XIDC'])
    else:
        uc = UnicodeChar(name=a['na'], is_range=False, code_point=a['cp'], last_code_point=None, block=a['blk'],
                         alpha=a['Alpha'], math=a['Math'], non_char=a['NChar'], deprecated=a['Dep'],
                         xid_start=a['XIDS'],xid_continue=a['XIDC'])
    return uc


def make_unicode_reserved(tag_type, node):
    a = node.attrib

    if 'first-cp' in a:
        fcp, lcp = a['first-cp'], a['last-cp']
    else:
        fcp, lcp = a['cp'], a['cp']

    ur = UnicodeReserved(name=a['na'], type=tag_type, first_code_point=fcp, last_code_point=lcp, block=a['blk'],
                         alpha=a['Alpha'], math=a['Math'], non_char=a['NChar'], deprecated=a['Dep'],
                         xid_start=a['XIDS'],xid_continue=a['XIDC'])
    return ur


def make_unicode_block(node):
    a = node.attrib
    ub = UnicodeBlock(name=a['name'], first_code_point=a['first-cp'], last_code_point=a['last-cp'])
    return ub


def make_ucd_map():
    """
    read in UCD data (nonunihan version). Create repertoire and block maps.

    UCD data is in XML. The childrn are as follows:

        children[0].tag is 'repertoire' [chars]
        children[1].tag is 'blocks'
        children[2].tag is 'named-sequences'
        children[3].tag is 'named-sequence'
        children[4].tag is 'normalization-corrections'
        children[5].tag is '}standardized-variants'
        children[6].tag is 'cjk-radicals'
        children[7].tag is 'emoji-sources'

    Note: currently just the repertroire (characters with attributes) and blocks are read in.

    Note: for the repertoire (chars) a subset of the attributes are kept. The full set (as of V11.0) is:

    Repertoire chars: ['cp', 'age', 'na', 'JSN', 'gc', 'ccc', 'dt', 'dm', 'nt', 'nv', 'bc', 'bpt', 'bpb',
            'Bidi_M', 'bmg', 'suc', 'slc', 'stc', 'uc', 'lc', 'tc', 'scf', 'cf', 'jt', 'jg', 'ea', 'lb', 'sc', 'scx',
            'Dash', 'WSpace', 'Hyphen', 'QMark', 'Radical', 'Ideo', 'UIdeo', 'IDSB', 'IDST', 'hst', 'DI', 'ODI',
            'Alpha', 'OAlpha', 'Upper', 'OUpper', 'Lower', 'OLower', 'Math', 'OMath', 'Hex', 'AHex', 'NChar', 'VS',
            'Bidi_C', 'Join_C', 'Gr_Base', 'Gr_Ext', 'OGr_Ext', 'Gr_Link', 'STerm', 'Ext', 'Term', 'Dia', 'Dep',
            'IDS', 'OIDS', 'XIDS', 'IDC', 'OIDC', 'XIDC', 'SD', 'LOE', 'Pat_WS', 'Pat_Syn', 'GCB', 'WB', 'SB', 'CE',
            'Comp_Ex', 'NFC_QC', 'NFD_QC', 'NFKC_QC', 'NFKD_QC', 'XO_NFC', 'XO_NFD', 'XO_NFKC', 'XO_NFKD', 'FC_NFKC',
            'CI', 'Cased', 'CWCF', 'CWCM', 'CWKCF', 'CWL', 'CWT', 'CWU', 'NFKC_CF', 'InSC', 'InPC', 'PCM', 'vo', 'RI',
            'blk', 'isc', 'na1'])


    Blocks: first-cp, last-cp, name - e.g. 0000-007F, 'Basic Latin'

    Named-sequences: name, cps - e.g. 'ARABIC SEQUENCE NOON WITH KEHEH; ;0646 06A9'

    Standardized variants: cps desc when - e.g. '0030 FE00' 'short diagonal stroke form' ''

    Standardized variant: number radical ideograph

    Emoji sources [use emoji-data.txt instead]: unicode docomo kddi softbank - e.g. '0023 20E3' 'F985' 'F489' 'F7B0'
        emoji-test.txt has subgroups of emojis
        emoji-sequences has categories


    :return: repertroire, reserved ranges and block map (dicts)
    """
    # FILENAME = 'xml/ucd.nounihan.flat.xml'
    filename = Path('./import/xml/ucd.nounihan.flat.xml').resolve()


    try:
        dom = ET.parse(open(filename, "r"))
        root = dom.getroot()
    except:
        print("Unable to open and parse input definition file: " + filename)
        sys.exit(1)

    unicode_chars = {}
    unicode_reserved = {}
    unicode_blocks = {}

    for node in root[1]:
        tag_type = node.tag.split('}')[1]

        if tag_type == 'char':
            uc = make_unicode_char(node)
            unicode_chars[uc.code_point] = uc
        elif tag_type in {'reserved', 'surrogate', 'noncharacter'} :
            ur = make_unicode_reserved(tag_type, node)
            unicode_reserved[ur.first_code_point] = ur
        else:
            print(f'unknown type={tag_type}')

    for node in root[2]:
        ub = make_unicode_block(node)
        unicode_blocks[node.attrib['name']] = ub

    return unicode_chars, unicode_reserved, unicode_blocks


def write_unicode_char(k, v, f):
    # v is a UnicodeChar = namedtuple('UnicodeChar', 'name is_range code_point last_code_point alpha math non_char deprecated xid_start xid_continue block')
    alpha = 1 if v.alpha == 'Y' else 0
    math = 1 if v.math == 'Y' else 0
    non_char = 1 if v.non_char == 'Y' else 0
    deprecated = 1 if v.deprecated == 'Y' else 0
    xid_start = 1 if v.xid_start == 'Y' else 0
    xid_continue = 1 if v.xid_continue == 'Y' else 0
    last = 'None' if v.last_code_point is None else f'0x{v.last_code_point}'

    # f.write(f' 0x{k}: {{ ')
    # f.write(f' "n": "{v.name}", "r": {v.is_range}, "c": 0x{v.code_point}, ')
    # f.write(f'"l": {last}, "a": {alpha}, "m": {math}, "nc": {non_char}, ')
    # f.write(f'"d":{deprecated}, "xs": {xid_start}, "xc": {xid_continue}, "b": "{v.block}"')
    # f.write(f' }},\n')
    f.write(f' 0x{k}: ("{v.name}", {v.is_range}, 0x{v.code_point}, {last}, {alpha}, {math}, {non_char}, ')
    f.write(f'{deprecated}, {xid_start}, {xid_continue}, "{v.block}"),\n')


def write_repertoire_map(repertoire_map, f):
    f.write('\n# dictionary of nonunihan Unicode character (repertoire) data\n')
    # f.write('# fields are: n - name, r - is_range, c - code_point, l - last_code_point (for ranges or None)\n')
    # f.write('#     a - alpha, m - math, nc - non_char, d - deprecated, xs - XID_start, xc - XID_Continue, b - block\n')
    f.write('# fields are: name, is_range, code_point, last_code_point (for ranges or None),\n')
    f.write('#     alpha, math, non_char, deprecated, XID_start, XID_Continue, block\n')
    f.write('repertoire_map = {\n')
    for k, v in repertoire_map.items():
        write_unicode_char(k, v, f)
    f.write('}\n')


def write_unicode_reserved(k, v, f):
    # v is a UnicodeChar = namedtuple('UnicodeChar', 'name is_range code_point last_code_point alpha math non_char deprecated xid_start xid_continue block')
    alpha = 1 if v.alpha == 'Y' else 0
    math = 1 if v.math == 'Y' else 0
    non_char = 1 if v.non_char == 'Y' else 0
    deprecated = 1 if v.deprecated == 'Y' else 0
    xid_start = 1 if v.xid_start == 'Y' else 0
    xid_continue = 1 if v.xid_continue == 'Y' else 0

    # f.write(f' 0x{k}: {{ ')
    # f.write(f' "n": "{v.name}", "t": {v.type}, "c": {v.first_code_point}, ')
    # f.write(f'"l": {v.last_code_point}, "a": {alpha}, "m": {math}, "nc": {non_char}')
    # f.write(f'"d":{deprecated}, "xs": {xid_start}, "xc": {xid_continue}, "b": "{v.block}"')
    # f.write(f' }}\n')
    f.write(f' 0x{k}: ("{v.name}", "{v.type}", 0x{v.first_code_point}, ')
    f.write(f'0x{v.last_code_point}, {alpha}, {math}, {non_char}')
    f.write(f'{deprecated}, {xid_start}, {xid_continue}, "{v.block}"),\n')


def write_reserved_map(reserved_map, f):
    f.write('\n\n# dictionary of reserved Unicode character blocks (reserved)\n')
    f.write('# fields are: n - name, t - type,  c - code_point, l - last_code_point (for ranges or None)\n')
    f.write('#     a - alpha, m - math, nc - non_char, d - deprecated, xs - XID_start, xc - XID_Continue, b - block\n')
    f.write('reserved_map = {\n')
    for k, v in reserved_map.items():
        write_unicode_reserved(k, v, f)
    f.write('}\n')


def write_block_map(block_map, f):
    f.write('\n\n# dictionary of Unicode blocks\n')
    f.write('# entries are: key: (f, l), where\n')
    f.write('#     key - the name of the block, f - the first code point of the block, l - the last code point of the block.\n')
    f.write('block_map = {\n')
    for k, v in block_map.items():
        f.write(f' "{k}": (0x{v.first_code_point}, 0x{v.last_code_point}),\n')
    f.write('}\n')


def make_identifier_status_map():
    # make dictionary of identifier status blocks
    # line is either:
    # 0027          ; Allowed    # 1.1        APOSTROPHE
    # 002D..002E    ; Allowed    # 1.1    [2] HYPHEN-MINUS..FULL STOP
    filename = Path('./import/IdentifierStatus.txt').resolve()
    isl = []

    with open(filename, 'r', encoding='utf8') as f:
        for l in f:
            if l[0] in {'\uFEFF', '#', '\n'}:  # comment or blank line
                continue

            # parse the line - TODO - parse comment
            semicolon_idx = l.find(';')
            hash_idx = l.find('#')

            code_points = l[0:semicolon_idx].strip()
            status = l[semicolon_idx+1: hash_idx].strip()
            comment = l[hash_idx+13:].strip()

            dots_idx = code_points.find('..')
            if dots_idx == -1: # only a single code point
                first_code_point = int(code_points, 16)
                last_code_point = None
            else:
                first_code_point = int(code_points[:dots_idx], 16)
                last_code_point = int(code_points[dots_idx+2:], 16)

            ub = UnicodeIdentifierStatus(first_code_point, last_code_point, status)
            isl.append( (ub, comment))

    return isl


def write_identifier_status_map(ism, f):
    f.write('\n\n# dictionary of Unicode identifier statuses\n')
    f.write('# entries are: key: (f, l, s), where\n')
    f.write('#     key - the first code point in the block, f - the first code point of the block, l - the last code point of the block.\n')
    f.write('#     status - the identifier status for the block.\n')
    f.write('identifier_status_map = {\n')

    for v in ism:
        ub, comment = v
        fcp_str = f'0x{ub.first_code_point:04x}'

        if ub.last_code_point is None:
            lcp_str = 'None'
        else:
            lcp_str = f'0x{ub.last_code_point:04x}'

        f.write(f' {fcp_str}: ({fcp_str}, {lcp_str}, "{ub.status}"), #  {comment}\n')

    f.write('}\n')


def make_identifier_type_map():
    """
    read in IdentifierType.txt data. Create emoji map.

    :return: identifier type map (list)
    """
    filename = Path('./import/IdentifierType.txt').resolve()
    isl = []

    with open(filename, 'r', encoding='utf8') as f:
        for l in f:
            if l[0] in {'\uFEFF', '#', '\n'}:  # comment or blank line
                continue

            # parse the line - TODO - parse comment
            semicolon_idx = l.find(';')
            hash_idx = l.find('#')

            code_points = l[0:semicolon_idx].strip()
            type_str = l[semicolon_idx+1: hash_idx].strip()
            types = type_str.split()
            comment = l[hash_idx+12:].strip()

            # set tags
            deprecated = technical = obsolete = inclusion = exclusion = limited_use = \
                uncommon_use = not_NFKC = not_XID = recommended = default_Ignorable = 0

            for t in types:
                if t == 'Not_XID':  # 816
                    not_XID = 1
                elif t == 'Recommended': # 509
                    recommended = 1
                elif t == 'Exclusion': # 387
                    exclusion = 1
                elif t == 'Not_NFKC': # 384
                    not_NFKC = 1
                elif t == 'Technical': # 277
                    technical = 1
                elif t == 'Obsolete': # 196
                    obsolete = 1
                elif t == 'Limited_Use': # 165
                    limited_use = 1
                elif t == 'Uncommon_Use': # 109
                    uncommon_use = 1
                elif t == 'Inclusion': # 18
                    inclusion = 1
                elif t == 'Default_Ignorable':  # 32
                    default_Ignorable = 1
                elif t == 'Deprecated': # 12
                    deprecated = 1

            allowed = inclusion or recommended

            dots_idx = code_points.find('..')
            if dots_idx == -1: # only a single code point
                first_code_point = int(code_points, 16)
                last_code_point = None
            else:
                first_code_point = int(code_points[:dots_idx], 16)
                last_code_point = int(code_points[dots_idx+2:], 16)

            ub = UnicodeIdentifierType(first_code_point, last_code_point, allowed, deprecated, technical, obsolete,
                                       inclusion, exclusion, limited_use, uncommon_use, not_NFKC, not_XID,
                                       recommended, default_Ignorable)
            isl.append( (ub, comment))

    return isl


def write_identifier_type_map(itm, f):
    f.write('\n\n# dictionary of Unicode identifier types\n')
    f.write('# entries are: key: (f, l, types), where\n')
    f.write('#     key - the first code point in the block, f - the first code point of the block, l - the last code point of the block.\n')
    f.write('#     types - types is a list of ints, with 0 for False and 1 for True for the following types for the identifier.\n')
    f.write('#        allowed, deprecated, technical, obsolete, inclusion, exclusion, limited_use, uncommon_use, not_NFKC, not_XID, recommended, default_Ignorable\n')

    f.write('identifier_type_map = {\n')

    for v in itm:
        ub, comment = v
        fcp_str = f'0x{ub.first_code_point:04x}'

        if ub.last_code_point is None:
            lcp_str = 'None'
        else:
            lcp_str = f'0x{ub.last_code_point:04x}'

        tag_vector = f'{ub.allowed},{ub.deprecated},{ub.technical},{ub.obsolete},{ub.inclusion},{ub.exclusion},' \
            f'{ub.limited_use},{ub.uncommon_use},{ub.not_NFKC},{ub.not_XID},{ub.recommended},{ub.default_Ignorable}'

        f.write(f' {fcp_str}: ({fcp_str}, {lcp_str}, {tag_vector}), #  {comment}\n')

    f.write('}\n')


def make_emoji_map():
    """
    read in emoji-data.txt data. Create emoji map.

    :return: emoji map (dict
    """
    #TODO
    pass
    # FILENAME = 'xml/ucd.nounihan.flat.xml'


def write_emoji_map(emoji_map, f):
    # TODO
    pass


if __name__ == '__main__':
    # intentional_map = make_intentional_map()
    # with open('intentional_map.py', 'w') as f:
    #     write_intentional_map_file(intentional_map, f)
    #
    # # ucd.nonunihan.flat.xml
    # rep_map, reserved_map, block_map = make_ucd_map()
    #
    # with open('repertoire_map.py', 'w') as f:
    #     write_repertoire_map(rep_map, f)
    #
    # with open('reserved_map.py', 'w') as f:
    #     write_reserved_map(reserved_map, f)
    #
    # with open('block_map.py', 'w') as f:
    #     write_block_map(block_map, f)
    #
    # id_status_map = make_identifier_status_map()
    #
    # with open('identifier_status_map.py', 'w') as f:
    #     write_identifier_status_map(id_status_map, f)

    id_type_map = make_identifier_type_map()

    with open('identifier_type_map.py', 'w') as f:
        write_identifier_type_map(id_type_map, f)

    # emoji_map = make_emoji_map()
    #
    # with open('emoji_map.py', 'w') as f:
    #     write_emoji_map(emoji_map, f)

