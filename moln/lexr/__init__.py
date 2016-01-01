import re
import logging

from typing import List, Iterable, Tuple, Union

_log = logging.getLogger(__name__)


class LexrError(Exception):
    pass


class LexrSyntaxError(LexrError):
    def __init__(self, position: Tuple[int, int], message):
        self.position = position
        self.message = message

    def __str__(self):
        return 'Invalid syntax: {0}: "%s"'.format(':'.join(self.position),
                                                  self.message)


class Token:
    """
    This class plays a dual role as both Spec and Token.

    "Spec Mode" instances of Token are created by specifying ``regex`` in
    __init__.

    "Token Mode" instances should instead include the

    - value
    - start
    - end

    parameters in the call to __init__.
    """
    def __init__(self, name, start=None, end=None, value=None, regex=None):
        self.name = name
        self.value = value
        self.start = start
        self.end = end

        self.is_spec = False

        # If regex is net,
        if regex is not None:
            self.is_spec = True
            self.regex = re.compile(regex)

    def __str__(self):
        if self.is_spec:
            return '<{0} (spec) regex={1!r}>'.format(self.name, self.regex)

        return '<{0} {1!r}>'.format(self.name, self.value)

    def __repr__(self):
        if self.is_spec:
            return '{0}({1!r}, regex={2!r})'.format(self.__class__.__name__,
                                                    self.name,
                                                    self.value)

        return '{0}({1!r}, {2!r})'.format(self.__class__.__name__,
                                          self.name,
                                          self.value)

    def __eq__(self, other):
        if self.is_spec:
            _log.warn('%r "Spec Mode" Token instance is compared to '
                      'another object %r', self, other)
            return super().__eq__(other)

        return self.name == other.name and self.value == other.value

    def match_spec(self, source, start_index,
                   start_position: Tuple[int, int])\
            -> Union['Token', None]:
        """
        Will return a new Token instance in "Token Mode".

        :param source: Text to match against
        :param start_index: The index in ``source`` at which to start matching.
        :param start_position: The current position in the source file,
        as line and character index on that line.
        :return: A new Token instance "Token Mode".
        """
        if not self.is_spec or self.regex is None:
            raise LexrError('Token with name {0!r} is not a spec '
                             'instance of Token'.format(self.name))

        start_line, start_character = start_position

        match = self.regex.match(source, start_index)

        if match is not None:
            _log.debug('%s matched %r', self, match.groups())

            value = match.group()

            new_lines = value.count('\n')

            end_line = start_line + new_lines

            end_character = start_character + len(value)
            if new_lines > 0:
                end_character = len(value) - value.rfind('\n') - 1

            return self.__class__(self.name,
                                  value=value,
                                  start=start_position,
                                  end=(end_line, end_character))


class Tokenizer:
    def __init__(self, *specs: List[Token]):
        self.specs = specs

    def __call__(self, source):
        current_index = 0
        current_position = (0, 0)

        while current_index < len(source):
            for spec in self.specs:
                _log.debug('Tokenizer: Trying spec %r', spec)

                token = spec.match_spec(source,
                                        start_index=current_index,
                                        start_position=current_position)

                current_position = token.end
                current_index += len(token.value)

                yield token
            else:
                raise LexrSyntaxError(current_position,
                                      'Unexpected input: {}'.format(
                                              source[current_index]))


if __name__ == '__main__':
    tokenizer = Tokenizer(
        Token('Ignored', regex=r'\s'),
        Token('String', regex=r'\w'),
        Token('Operator', regex=r'[+\-/*%=]'),
        Token('Number', regex=r'[1-9][0-9]*'),
    )

    source = '''
    a = 1
    b = a + 1
    '''

    print(repr(tokenizer(source)))