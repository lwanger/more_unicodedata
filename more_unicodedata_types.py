"""
Type definitions for more_unicode data

Len Wanger, 2019
"""

from collections import namedtuple

# Used for repertoire characters
UnicodeChar = namedtuple('UnicodeChar', 'name is_range code_point last_code_point alpha math non_char deprecated xid_start xid_continue block')

# used for: reserved, surrogate, and noncharacter.
UnicodeReserved = namedtuple('UnicodeReserved', 'name type first_code_point last_code_point alpha math non_char deprecated xid_start xid_continue block')

# used for UCD blocks
UnicodeBlock = namedtuple('UnicodeBlock', 'name first_code_point last_code_point')

# used for IdentifierStatus
UnicodeIdentifierStatus = namedtuple('IidentifierStatus', 'first_code_point last_code_point status')

# used for IdentifierType
# UnicodeIdentifierType = namedtuple('IidentifierType', 'first_code_point last_code_point types')
it_fields = 'first_code_point last_code_point allowed deprecated technical obsolete inclusion exclusion limited_use ' \
            'uncommon_use not_NFKC not_XID recommended default_Ignorable'
UnicodeIdentifierType = namedtuple('IidentifierType', it_fields)
