import re
import logging
import typing


from moln.lexer import Token, LexerError

from moln.bencode.tokens import tokenize, decode_tokens

_log = logging.getLogger(__name__)


class BencodeError(Exception):
    pass


class DecodeError(BencodeError):
    pass


class EncodeError(BencodeError):
    pass


def decode_bytes(_bytes: bytes) -> typing.Any:
    try:
        return decode_tokens(list(tokenize(_bytes)))
    except LexerError as exc:
        raise DecodeError('Failed to decode bencoded stream') from exc


def encode_bytes(x: typing.Union[bytes,
                                 str,
                                 int,
                                 dict,
                                 list,
                                 None]) -> bytes:
    if isinstance(x, bytes):
        return str(len(x)).encode() + b':' + x
    elif isinstance(x, str):
        _bytes = x.encode('utf8')
        return str(len(_bytes)).encode() + b':' + _bytes
    elif isinstance(x, int):
        return b'i' + bytes(x) + b'e'
    elif isinstance(x, list):
        return b'l' + b''.join(encode_bytes(i) for i in x) + b'e'
    elif isinstance(x, dict):
        return b'd' + b''.join(encode_bytes(k) + encode_bytes(v)
                               for k, v in x.items()) + b'e'
    else:
        raise EncodeError('Can\'t encode object of type {0} to bencode: {'
                          '1!r}'.format(type(x), x))

