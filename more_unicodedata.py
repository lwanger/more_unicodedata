"""
More unicodedata:

utilities for extended unicode data. Takes off where the standard library unicodedata library leaves off

Len Wanger, 2019

TODO/Issues:
    - is_safe_identifier -- should it validate punycode strings too?
    - block names and block names of characters don't always match. e.g. block name is "Latin-1 Supplement" and
        repertoire has "Latin_1_Sup". Just use block names? Remove block from repertoire?
    - parser IdentifierType file. Type will give further restrictions: Recommended, Not_XID, Exclusion, Obsolete,  Not_NFKC, etc.
"""

from bisect import bisect_left

from intentional_map import intentional_map
from block_map import block_map
from repertoire_map import repertoire_map
from reserved_map import reserved_map
from identifier_status_map import identifier_status_map
from identifier_type_map import identifier_type_map

from more_unicodedata_types import UnicodeChar, UnicodeReserved, UnicodeBlock, UnicodeIdentifierStatus


# routines for intentional confusion
def is_intentional_confusion(s):
    """
    Check if a string contains any characters on the intentional confusion list.

    :param s: the string to check
    :return: True if the string contains any characters in the intentional_confusion list (False otherwise)
    """
    return any((ord(c) in intentional_map) for c in s)


def fix_intention_confusion(s):
    """
    :param s:
    :return: string with any intentionally confusing characters changed to the non-confusing equivalent character
    """
    return ''.join(chr(intentional_map[ord(c)][0]) if ord(c) in intentional_map else c for c in s)


def show_intentional_confusion(s):
    """
    return a list of intentionally confusing characters in the string.

    :param s: the string to check
    :return: a list of tuples, where the tuples of intentionally confusing characters. If no intentionally confusing
        characters are found an empty list ([]) is returned.

    Each tuple in the list returned has five elements.
        idx - the index of the confusing character in the string
        confusing character - the unicode character for the confusing character
        mimicked character - the unicode character the confusing character is mimicking
        confusing description - the name of the confusing character
        mimicked description - the name of the mimicked character
    """
    return [(i, c, chr(intentional_map[ord(c)][0]), intentional_map[ord(c)][1], intentional_map[ord(c)][2])
                        for i,c in enumerate(s) if ord(c) in intentional_map]


# routines for blocks
def in_block(s, block_name):
    # return True if all characters in string s are in block_name
    block = block_map[block_name]
    return all(block[0] <= ord(c) <= block[1] for c in s)

def blocks(s):
    # return set of blocks that characters of the string are in
    return {repertoire_map[ord(c)][10] for c in s}

# routine for reserved blocks

def in_reserved(s):
    # return True if any characters in string s are in a reserved block
    reserve_start_cps = tuple(reserved_map.keys())

    for c in s:
        if ord(c) < reserve_start_cps[0]:
            return False

        left = bisect_left(reserve_start_cps, ord(c))

        if ord(c) == reserve_start_cps[left]:
            continue
        else:
            reserved_left = reserve_start_cps[left-1]
            rb = reserved_map[reserved_left]
            if not (rb[2] <= ord(c) <= rb[3]):
                return False

    return True


def in_identifier_range(c):
    # return True if character c is in an identifier status block
    is_keys = tuple(identifier_status_map.keys())

    if ord(c) < is_keys[0]:
        return False

    left = bisect_left(is_keys, ord(c))

    if ord(c) == is_keys[left]:
        return True
    else:
        reserved_left = is_keys[left - 1]
        rb = identifier_status_map[reserved_left]
        if rb[1] is None:  # if equal to rb[0] would already have returned True
            return False
        if not (rb[0] <= ord(c) <= rb[1]):
            return False

    return True


def get_identifier_type(c):
    # get the identifier_type for the character. return None if not in a type block
    id_type_cps = tuple(identifier_type_map.keys())

    if ord(c) < id_type_cps[0]:
        return None

    left = bisect_left(id_type_cps, ord(c))

    if ord(c) == id_type_cps[left]:
        return identifier_type_map[id_type_cps[left]]
    else:
        idt_left = id_type_cps[left-1]
        idt = identifier_type_map[idt_left]
        if (idt[0] <= ord(c) <= idt[1]):
            return idt
        else:
            return None


def all_ascii(s, allowed_chars=None):
    # return True if all characters in the string are in the ascii code block
    return all((0 <= ord(c) <= 127) or (allowed_chars and (c in allowed_chars)) for c in s)


def all_latin(s, allowed_chars=None):
    # return True if all characters in the string are in the ascii or a Latin code block
    try:
        blocks = {repertoire_map[ord(c)][10] for c in s if (not allowed_chars) or (c not in allowed_chars)}
    except KeyError:
        return False

    return all((b=='ASCII' or b.startswith('Latin')) for b in blocks)


def all_allowed(s, allowed_chars=None):
    # return True if all characters in the string are in the ascii or a Latin code block
    try:
        # get itm for each char... check each has allowed type
        for c in s:
            if allowed_chars and (c in allowed_chars):
                continue
            itm = get_identifier_type(c)
            if itm is None or itm[2] == 0:
                return False
        # result = all((identifier_type_map[ord(c)][2]==1) for c in s if (not allowed_chars) or (c not in allowed_chars))
    except KeyError:
        return False
    return True


def is_safe_identifier(s, level='ascii', allowed_chars=None):
    """
    Return true if the string is a valid IDNA identifier as specified in: https://www.unicode.org/reports/tr46/

    :param s: the string to check
    :param level: safety level to check
    :param allowed_chars:
    :return: True if the string is a valid/safe identifier for the given safety level (otherwise False)

    supported safety levels:
      'ascii' - all ascii
      'programming' - follows core XID_START and XID_CONTINUE
      'idmod' - follows extended identifier rules (see: http://www.unicode.org/reports/tr39/tr39-17.html, section 3.1))
    """
    if level == 'ascii':
        return all_ascii(s, allowed_chars=None)
    elif level == 'programming':
        try:
            rmc = repertoire_map[ord(s[0])]
        except KeyError:
            return False

        if rmc[8] == 0 and allowed_chars and s[0] not in allowed_chars: # is not XID_START
            return False

        for c in s[1:]:
            try:
                rmc = repertoire_map[ord(c)]
            except KeyError:
                return False
            if rmc[9] == 0 and allowed_chars and c not in allowed_chars:  # is not XID_CONTINUE
                return False

        return True
    elif level == 'idmod':  # TODO - test idmod!
        for c in s:
            if in_identifier_range(c):
                continue
            elif allowed_chars and c in  allowed_chars:  # ok if in allowed_characters
                continue
            else:
                return False
    else:
        raise ValueError(f'Unsupported level ({level})')

    return True


def get_unicode_char(ord_c, repertoire_map):
    # get the value for a character from the repertoire map (c is ordinal value of the character)
    try:
        uc = UnicodeChar(*repertoire_map[ord_c])
    except KeyError:
        return None

    return uc


def is_safe_string(s, level='ascii', allowed_chars=None):
    """
    Returns True if a string passes the specified security level.

    :param s: the sring to check
    :param level: the safety level (see below for safety levels
    :param allowed_chars: additional allowable characters
    :return: True is the specified string is safe, False otherwise

     levels:
        'ascii' - only allow characters in the ascii character set
        'latin' - only allow characters in the Latin code block
        'allowed' - only allow characters allowed in the identifier_type table
        'unrestricted' - allow any character

        This is based on recommendations in: Unicode security mechanisms (http://www.unicode.org/reports/tr39/tr39-17.html)

    TODO - This still doesn't deal with a lot of safety issues. For examples (but not an exhaustive list):
        - doesn't deal with single script spoofing
        - doesn't deal with non-intentional confusions
        - doesn't deal with bidirectional script spoofing
        - doesn't deal with syntax spoofing
        - doesn't deal with numeric spoofs
        - doesn't deal with ill-formed sub-sequences
        - doesn't deal with illegal input byte sequences

    More TODO:
        - allow specifying a list of allowed languages
        - check for bidi override characters
        - check for mixing right-to-left and left-to-rigth in single string
        - allow specifying types (e.g. private data, technical, etc.) to specifically allow or disallow (even in unrestricted)?


    """
    # TODO:  check canonical equivalence (for <u, combining-diaeresis>" 1) check u is allowed and diaeresis is allowed, 2) combined (normalized) is allowed)
    #         so check non-normalized then if normalized is different check normalized chars
    # TODO: check for intentional confusion
    # TODO: check characters are allowed (vs rules)
    # TODO: check for multiple scripts (with allowd sets)
    # TODO: check for private data chars
    # identifier_type_map

    if level == 'unrestricted':
        return True
    elif level == 'ascii':
        return all_ascii(s, allowed_chars)
    elif level == 'latin':
        return all_latin(s, allowed_chars)
    elif level == 'allowed':
        return all_allowed(s, allowed_chars)
    else:
        raise ValueError(f'Unrecognized safety level ({level})')

    return True