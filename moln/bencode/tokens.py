import re
import logging
import typing

from funcparserlib import parser as p

from moln.lexer import Token, get_new_position, Lexer, LexerError

_log = logging.getLogger(__name__)


def decode_tokens(s: typing.List[Token]):
    def _to_int(token):
        _log.debug('_to_int: %r', token)
        return int(token)

    str_strip_re = re.compile(rb'^\d+:')

    def _to_string(s):
        _log.debug('_to_string: %r', s)
        return str_strip_re.sub(b'', s)

    def _to_list(_tokens):
        _log.debug('_to_list: %r', _tokens)

        return _tokens

    def _to_dict(n):
        _log.debug('_to_dict: %r', n)
        return dict(_to_list(n))

    def token_value(x):
        return x.value

    def token_type(t):
        return p.some(lambda x: x.name == t) >> token_value

    def type_decl(type_name):
        return p.a(
            Token('Type', type_name)
        ).named('Type({})'.format(type_name))

    value = p.forward_decl().named('Value')

    integer = token_type('Number')

    end = p.a(Token('End', b'e'))

    # String is special, has no type
    str_decl = (
        token_type('String') >> _to_string
    ).named('String')

    dict_decl = (
        p.skip(type_decl(b'd')) +
        p.many(value + value) +
        p.skip(end) >> _to_dict
    ).named('Dict')

    list_decl = (
        p.skip(type_decl(b'l')) +
        p.many(value) +
        p.skip(end) >> _to_list
    ).named('List')

    integer_decl = (
        p.skip(type_decl(b'i')) +
        integer +
        p.skip(end) >> _to_int
    ).named('Integer')

    value.define(
        integer_decl |
        dict_decl |
        list_decl |
        str_decl
    )

    bencode_decl = (
        value +
        p.skip(p.finished)
    ).named('Bencode')

    return bencode_decl.parse(s)


def tokenize(_bytes: bytes):
    lexer = Lexer(
        StringToken('String', is_spec=True),
        Token('Number', regex=rb'0|[1-9][0-9]*'),
        Token('Type', regex=rb'[ild]'),
        Token('End', regex=rb'e'),
    )

    return lexer(_bytes)


class StringToken(Token):

    preamble_re = re.compile(rb'([1-9][0-9]*):')

    def __init__(self, name, is_spec=None, **kwargs):
        super(StringToken, self).__init__(name, **kwargs)
        self.is_spec = is_spec

    def __str__(self):
        if self.is_spec:
            return '<{} (spec)>'.format(self.__class__.__name__)

        return super(StringToken, self).__str__()

    def __repr__(self):
        if self.is_spec:
            return '<{} (spec)>'.format(self.__class__.__name__)

        return super(StringToken, self).__repr__()

    def match_spec(self, source: bytes, start_index,
                   start_position: typing.Tuple[int, int]) \
            -> typing.Union['Token', None]:
        """
        Will return a new Token instance in "Token Mode".

        :param source: Text to match against
        :param start_index: The index in ``source`` at which to start matching.
        :param start_position: The current position in the source file,
        as line and character index on that line.
        :return: A new Token instance "Token Mode".
        """
        if not self.is_spec:
            raise LexerError('{0!r} is not a "Spec Mode" instance'.format(self))

        match = self.preamble_re.match(source, start_index)

        if match is not None:

            str_length = int(match.group(1))

            preamble_length = len(match.group(0))

            str_last = start_index + preamble_length + str_length

            value = source[start_index:str_last]

            _log.debug('StringToken: (spec) MATCH %s matched %r', self, value)

            return StringToken(self.name,
                               value=value,
                               start=start_position,
                               end=get_new_position(value,
                                                    start_position))
