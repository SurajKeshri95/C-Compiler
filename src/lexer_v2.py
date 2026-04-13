class Token:
    def __init__(self, type, value, line, column, raw=""):
        self.type = type
        self.value = value
        self.line = line
        self.column = column
        self.raw = raw
        
    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, line={self.line}, col={self.column})"

KEYWORDS = {
    "int": "INT",
    "float": "FLOAT",
    "char": "CHAR",
    "void": "VOID",
    "if": "IF",
    "else": "ELSE",
    "while": "WHILE",
    "for": "FOR",
    "do": "DO",
    "return": "RETURN",
    "struct": "STRUCT",
    "sizeof": "SIZEOF",
    "break": "BREAK",
    "continue": "CONTINUE",
    "static": "STATIC",
    "const": "CONST",
    "main": "MAIN",
}

class LexerError(Exception):
    def __init__(self, message, line, column, source_line=""):
        self.message = message
        self.line = line
        self.column = column
        self.source_line = source_line
        super().__init__(f"Lexer Error at line {line}:{column}: {message}")

class Lexer:
    def __init__(self, source):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.line_start = 0
        self.tokens = []

    def current(self):
        return self.source[self.pos] if self.pos < len(self.source) else None

    def peek(self, offset=1):
        idx = self.pos + offset
        return self.source[idx] if idx < len(self.source) else None

    def advance(self):
        ch = self.source[self.pos] if self.pos < len(self.source) else None
        if ch:
            self.pos += 1
            if ch == '\n':
                self.line += 1
                self.column = 1
                self.line_start = self.pos
            else:
                self.column += 1
        return ch

    def get_source_line(self):
        """Get the current line of source code"""
        end = self.source.find('\n', self.line_start)
        if end == -1:
            end = len(self.source)
        return self.source[self.line_start:end]

    def skip_whitespace(self):
        while self.current() and self.current() in ' \t\r\n':
            self.advance()

    def skip_line_comment(self):
        while self.current() and self.current() != '\n':
            self.advance()

    def skip_block_comment(self):
        """Skip /* ... */ comments"""
        self.advance()  # skip /
        self.advance()  # skip *
        while self.pos < len(self.source) - 1:
            if self.current() == '*' and self.peek() == '/':
                self.advance()  # skip *
                self.advance()  # skip /
                return
            self.advance()
        raise LexerError("Unterminated block comment", self.line, self.column, self.get_source_line())

    def read_number(self):
        line, col = self.line, self.column
        start = self.pos
        
        while self.current() and self.current().isdigit():
            self.advance()
        
        if self.current() == '.' and self.peek() and self.peek().isdigit():
            self.advance()
            while self.current() and self.current().isdigit():
                self.advance()
            val = float(self.source[start:self.pos])
            return Token("FLOAT_NUM", val, line, col, self.source[start:self.pos])
        
        val = int(self.source[start:self.pos])
        return Token("NUMBER", val, line, col, self.source[start:self.pos])

    def read_identifier(self):
        line, col = self.line, self.column
        start = self.pos
        
        while self.current() and (self.current().isalnum() or self.current() == '_'):
            self.advance()
        
        word = self.source[start:self.pos]
        ttype = KEYWORDS.get(word, "ID")
        return Token(ttype, word, line, col, word)

    def read_string(self):
        line, col = self.line, self.column
        self.advance()  # skip opening quote
        start = self.pos
        escaped = False
        
        while self.current():
            if escaped:
                escaped = False
                self.advance()
                continue
            if self.current() == '\\':
                escaped = True
                self.advance()
                continue
            if self.current() == '"':
                val = self.source[start:self.pos]
                self.advance()  # skip closing quote
                return Token("STRING", val, line, col, f'"{val}"')
            self.advance()
        
        raise LexerError("Unterminated string", line, col, self.get_source_line())

    def read_char(self):
        line, col = self.line, self.column
        self.advance()  # skip opening quote
        start = self.pos
        escaped = False
        
        if self.current() == '\\':
            escaped = True
            self.advance()
        
        if not self.current():
            raise LexerError("Unterminated character literal", line, col, self.get_source_line())
        
        self.advance()
        
        if self.current() != "'":
            raise LexerError("Character literal must contain exactly one character", line, col, self.get_source_line())
        
        val = self.source[start:self.pos]
        self.advance()  # skip closing quote
        return Token("CHAR_LIT", val, line, col, f"'{val}'")

    def tokenize(self):
        while self.pos < len(self.source):
            self.skip_whitespace()
            
            if self.pos >= len(self.source):
                break
            
            ch = self.current()
            
            # Comments
            if ch == '/' and self.peek() == '/':
                self.skip_line_comment()
                continue
            
            if ch == '/' and self.peek() == '*':
                self.skip_block_comment()
                continue
            
            # String literals
            if ch == '"':
                self.tokens.append(self.read_string())
                continue
            
            # Character literals
            if ch == "'":
                self.tokens.append(self.read_char())
                continue
            
            # Numbers
            if ch.isdigit():
                self.tokens.append(self.read_number())
                continue
            
            # Identifiers and keywords
            if ch.isalpha() or ch == '_':
                self.tokens.append(self.read_identifier())
                continue
            
            line, col = self.line, self.column
            
            # Three-character operators
            if ch == '.' and self.peek() == '.' and self.peek(2) == '.':
                self.advance(); self.advance(); self.advance()
                self.tokens.append(Token("ELLIPSIS", "...", line, col, "..."))
            
            # Two-character operators
            elif ch == '=' and self.peek() == '=':
                self.advance(); self.advance()
                self.tokens.append(Token("EQ", "==", line, col, "=="))
            elif ch == '!' and self.peek() == '=':
                self.advance(); self.advance()
                self.tokens.append(Token("NEQ", "!=", line, col, "!="))
            elif ch == '<' and self.peek() == '=':
                self.advance(); self.advance()
                self.tokens.append(Token("LE", "<=", line, col, "<="))
            elif ch == '>' and self.peek() == '=':
                self.advance(); self.advance()
                self.tokens.append(Token("GE", ">=", line, col, ">="))
            elif ch == '&' and self.peek() == '&':
                self.advance(); self.advance()
                self.tokens.append(Token("AND", "&&", line, col, "&&"))
            elif ch == '|' and self.peek() == '|':
                self.advance(); self.advance()
                self.tokens.append(Token("OR", "||", line, col, "||"))
            elif ch == '+' and self.peek() == '+':
                self.advance(); self.advance()
                self.tokens.append(Token("INC", "++", line, col, "++"))
            elif ch == '-' and self.peek() == '-':
                self.advance(); self.advance()
                self.tokens.append(Token("DEC", "--", line, col, "--"))
            elif ch == '+' and self.peek() == '=':
                self.advance(); self.advance()
                self.tokens.append(Token("PLUS_ASSIGN", "+=", line, col, "+="))
            elif ch == '-' and self.peek() == '=':
                self.advance(); self.advance()
                self.tokens.append(Token("MINUS_ASSIGN", "-=", line, col, "-="))
            elif ch == '*' and self.peek() == '=':
                self.advance(); self.advance()
                self.tokens.append(Token("MUL_ASSIGN", "*=", line, col, "*="))
            elif ch == '/' and self.peek() == '=':
                self.advance(); self.advance()
                self.tokens.append(Token("DIV_ASSIGN", "/=", line, col, "/="))
            elif ch == '-' and self.peek() == '>':
                self.advance(); self.advance()
                self.tokens.append(Token("ARROW", "->", line, col, "->"))
            elif ch == '&' and self.peek() != '&':
                self.advance()
                self.tokens.append(Token("AMP", "&", line, col, "&"))
            elif ch == '*' and self.peek() != '=':
                self.advance()
                self.tokens.append(Token("MUL", "*", line, col, "*"))
            
            # Single-character operators
            elif ch == '+': self.advance(); self.tokens.append(Token("PLUS", "+", line, col, "+"))
            elif ch == '-': self.advance(); self.tokens.append(Token("MINUS", "-", line, col, "-"))
            elif ch == '/': self.advance(); self.tokens.append(Token("DIV", "/", line, col, "/"))
            elif ch == '%': self.advance(); self.tokens.append(Token("MOD", "%", line, col, "%"))
            elif ch == '=': self.advance(); self.tokens.append(Token("ASSIGN", "=", line, col, "="))
            elif ch == '<': self.advance(); self.tokens.append(Token("LT", "<", line, col, "<"))
            elif ch == '>': self.advance(); self.tokens.append(Token("GT", ">", line, col, ">"))
            elif ch == '!': self.advance(); self.tokens.append(Token("NOT", "!", line, col, "!"))
            elif ch == ';': self.advance(); self.tokens.append(Token("SEMI", ";", line, col, ";"))
            elif ch == ',': self.advance(); self.tokens.append(Token("COMMA", ",", line, col, ","))
            elif ch == '.': self.advance(); self.tokens.append(Token("DOT", ".", line, col, "."))
            elif ch == '(': self.advance(); self.tokens.append(Token("LPAREN", "(", line, col, "("))
            elif ch == ')': self.advance(); self.tokens.append(Token("RPAREN", ")", line, col, ")"))
            elif ch == '{': self.advance(); self.tokens.append(Token("LBRACE", "{", line, col, "{"))
            elif ch == '}': self.advance(); self.tokens.append(Token("RBRACE", "}", line, col, "}"))
            elif ch == '[': self.advance(); self.tokens.append(Token("LBRACKET", "[", line, col, "["))
            elif ch == ']': self.advance(); self.tokens.append(Token("RBRACKET", "]", line, col, "]"))
            elif ch == '?': self.advance(); self.tokens.append(Token("QUESTION", "?", line, col, "?"))
            elif ch == ':': self.advance(); self.tokens.append(Token("COLON", ":", line, col, ":"))
            
            else:
                raise LexerError(f"Unexpected character '{ch}'", line, col, self.get_source_line())
        
        self.tokens.append(Token("EOF", None, self.line, self.column, ""))
        return self.tokens
