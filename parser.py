from typing import Dict


class ParseError(Exception):
    def __init__(self, pos: int, line: int, msg: str, *args):
        self.pos = pos
        self.line = line
        self.msg = msg
        self.args = args

    def __str__(self):
        return '%s at line %s position %s' % (self.msg % self.args, self.line, self.pos)


class Parser:
    text: str
    pos: int
    line: int
    len: int

    def __init__(self):
        self.cache = {}

    def parse(self, text):
        self.text = text
        self.pos = -1
        self.line = 0
        self.len = len(text) - 1

        rv = self.start()

        self.assert_end()
        return rv

    def assert_end(self):
        if self.pos < self.len:
            raise ParseError(
                self.pos + 1,
                self.line,
                'Expected end of string but got %s',
                self.text[self.pos + 1]
            )

    def eat_whitespace(self, check_indentation: bool):
        char = self.text[self.pos + 1]
        while self.pos < self.len and char in " \f\v\r\t\n":
            self.pos += 1
            if char == '\n':
                self.line += 1

    def split_char_ranges(self, chars):
        try:
            return self.cache[chars]
        except KeyError:
            pass

        rv = []
        index = 0
        length = len(chars)

        while index < length:
            if index + 2 < length and chars[index + 1] == '-':
                if chars[index] >= chars[index + 2]:
                    raise ValueError('Bad character range')

                rv.append(chars[index:index + 3])
                index += 3
            else:
                rv.append(chars[index])
                index += 1

        self.cache[chars] = rv
        return rv

    def char(self, chars=None) -> str:
        if self.pos >= self.len:
            raise ParseError(
                self.pos + 1,
                self.line,
                'Expected %s but got end of string',
                'character' if chars is None else '[%s]' % chars
            )

        next_char = self.text[self.pos + 1]
        if chars is None:
            self.pos += 1
            return next_char

        for char_range in self.split_char_ranges(chars):
            if len(char_range) == 1:
                if next_char == char_range:
                    self.pos += 1
                    return next_char
            elif char_range[0] <= next_char <= char_range[2]:
                self.pos += 1
                return next_char

        raise ParseError(
            self.pos + 1,
            self.line,
            'Expected %s but got %s',
            'character' if chars is None else '[%s]' % chars,
            next_char
        )

    def keyword(self, *keywords, eat_after: bool = True):
        # self.eat_whitespace(check_indentation=True)
        if self.pos >= self.len:
            raise ParseError(
                self.pos + 1,
                self.line,
                'Expected %s but got end of string',
                ','.join(keywords)
            )

        for keyword in keywords:
            low = self.pos + 1
            high = low + len(keyword)

            print(f'Low -> {low} | high -> {high} | self.text[low:high] -> {self.text[low:high]} | keyword -> {keyword} | Match -> {self.text[low:high] == keyword} ')
            if self.text[low:high] == keyword:
                self.pos += len(keyword)
                # Does not need to check indentation as it could consider separators between ':' and a value as
                # indentation levels
                # if eat_after:
                #     self.eat_whitespace(check_indentation=False)
                return keyword

        raise ParseError(
            self.pos + 1,
            self.line,
            'Expected %s but got %s',
            ','.join(keywords),
            self.text[self.pos + 1],
        )

    def match(self, *rules, eat_whitespace: bool = True, check_indentation_after = True):
        # if eat_whitespace:
        #     self.eat_whitespace(check_indentation=True)
        last_error_pos = -1
        last_exception = None
        last_error_rules = []

        for rule in rules:
            initial_pos = self.pos
            try:
                print(f'Probando {rule}')
                rv = getattr(self, rule)()
                # if eat_whitespace:
                #     self.eat_whitespace(check_indentation=False)
                print(f'{rule} exitosa!')
                return rv
            except ParseError as e:
                print(f'{rule} no matchea')
                self.pos = initial_pos

                if e.pos > last_error_pos:
                    last_exception = e
                    last_error_pos = e.pos
                    last_error_rules.clear()
                    last_error_rules.append(rule)
                elif e.pos == last_error_pos:
                    last_error_rules.append(rule)

        if len(last_error_rules) == 1:
            raise last_exception
        else:
            raise ParseError(
                last_error_pos,
                self.line,
                'Expected %s but got %s',
                ','.join(last_error_rules),
                self.text[last_error_pos]
            )

    # def match_with_only_spaces_before(self, *rules):
    #     self.eat_whitespace_only()
    #     last_error_pos = -1
    #     last_exception = None
    #     last_error_rules = []
    #
    #     for rule in rules:
    #         initial_pos = self.pos
    #         try:
    #             rv = getattr(self, rule)()
    #             self.eat_whitespace_only()
    #             return rv
    #         except ParseError as e:
    #             self.pos = initial_pos
    #
    #             if e.pos > last_error_pos:
    #                 last_exception = e
    #                 last_error_pos = e.pos
    #                 last_error_rules.clear()
    #                 last_error_rules.append(rule)
    #             elif e.pos == last_error_pos:
    #                 last_error_rules.append(rule)
    #
    #     if len(last_error_rules) == 1:
    #         raise last_exception
    #     else:
    #         raise ParseError(
    #             last_error_pos,
    #             self.line,
    #             'Expected %s but got %s',
    #             ','.join(last_error_rules),
    #             self.text[last_error_pos]
    #         )

    def maybe_char(self, chars=None):
        try:
            return self.char(chars)
        except ParseError:
            return None

    def maybe_match(self, *rules, eat_whitespace: bool = True):
        try:
            return self.match(*rules, eat_whitespace=eat_whitespace)
        except ParseError:
            return None

    def maybe_keyword(self, *keywords):
        try:
            return self.keyword(*keywords)
        except ParseError:
            return None


class Gura(Parser):
    def start(self):
        return self.expression()

    def loads(self, content: str) -> Dict:
        return None

    def dumps(self, content: Dict) -> str:
        return None
