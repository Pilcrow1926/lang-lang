"""
sunflower.parser
================
토큰 리스트를 AST(추상 구문 트리)로 변환하는 재귀 하강 파서.

AST 노드는 튜플로 표현됩니다:
  ('Program', [stmts])
  ('VarDecl', type, name, expr)
  ('Assign', name, expr)
  ('IncDec', name, '++' or '--')
  ('Print', expr)
  ('If', cond_expr, then_block, else_block)
  ('While', cond_expr, body)
  ('For', var, [range_args], body)
  ('BinOp', op, left, right)
  ('Compare', op, left, right)
  ('Logical', op, left, right)
  ('UnaryOp', op, operand)
  ('Number', value)
  ('String', value)
  ('Identifier', name)
"""


class ParseError(Exception):
    """파서 에러"""
    pass


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # -------- 유틸리티 --------
    def current(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def peek(self, offset=0):
        p = self.pos + offset
        return self.tokens[p] if p < len(self.tokens) else None

    def advance(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, tok_type):
        if self.current() and self.current()[0] == tok_type:
            return self.advance()
        raise ParseError(f"Expected {tok_type}, got {self.current()}")

    def skip_newlines(self):
        while self.current() and self.current()[0] == 'NEWLINE':
            self.advance()

    # -------- 프로그램/문장 --------
    def parse_program(self):
        stmts = []
        self.skip_newlines()
        while self.current():
            stmt = self.parse_statement()
            if stmt:
                stmts.append(stmt)
            self.skip_newlines()
        return ('Program', stmts)

    def parse_statement(self):
        tok = self.current()
        if not tok:
            return None
        t = tok[0]

        if t in ('TYPE_STRING', 'TYPE_FLOAT'):
            return self.parse_var_decl()

        if t == 'KW_MAEU':
            # 매우 [IDENT] 캬 ... → int 선언
            # 매우 [IDENT] 뒷 ... → for 반복문
            if (self.peek(1) and self.peek(1)[0] == 'IDENTIFIER'
                    and self.peek(2) and self.peek(2)[0] == 'IN'):
                return self.parse_for()
            return self.parse_var_decl()

        if t == 'PRINT':
            return self.parse_print()
        if t == 'IF':
            return self.parse_if()
        if t == 'WHILE':
            return self.parse_while()

        if t == 'IDENTIFIER':
            if self.peek(1) and self.peek(1)[0] == 'ASSIGN':
                return self.parse_assign()
            if self.peek(1) and self.peek(1)[0] in ('INC', 'DEC'):
                return self.parse_incdec()

        raise ParseError(f"Unexpected token: {tok}")

    # -------- 개별 문장 파서 --------
    def parse_var_decl(self):
        type_tok = self.advance()
        type_map = {'TYPE_STRING': 'string', 'TYPE_FLOAT': 'float', 'KW_MAEU': 'int'}
        var_type = type_map[type_tok[0]]
        name = self.expect('IDENTIFIER')[1]
        self.expect('ASSIGN')
        value = self.parse_expression()
        return ('VarDecl', var_type, name, value)

    def parse_assign(self):
        name = self.expect('IDENTIFIER')[1]
        self.expect('ASSIGN')
        value = self.parse_expression()
        return ('Assign', name, value)

    def parse_incdec(self):
        name = self.expect('IDENTIFIER')[1]
        op_tok = self.advance()
        op = '++' if op_tok[0] == 'INC' else '--'
        return ('IncDec', name, op)

    def parse_print(self):
        self.expect('PRINT')
        self.expect('LPAREN')
        value = self.parse_expression()
        self.expect('RPAREN')
        return ('Print', value)

    def parse_if(self):
        self.expect('IF')
        self.expect('LPAREN')
        cond = self.parse_expression()
        self.expect('RPAREN')
        self.expect('COLON')
        self.expect('LBRACE')
        then_block = self.parse_block()

        else_block = None
        save = self.pos
        self.skip_newlines()
        if self.current() and self.current()[0] == 'ELSE':
            self.advance()
            if self.current() and self.current()[0] == 'IF':
                # else if
                else_block = [self.parse_if()]
            else:
                self.expect('COLON')
                self.expect('LBRACE')
                else_block = self.parse_block()
        else:
            self.pos = save

        return ('If', cond, then_block, else_block)

    def parse_while(self):
        self.expect('WHILE')
        self.expect('LPAREN')
        cond = self.parse_expression()
        self.expect('RPAREN')
        self.expect('COLON')
        self.expect('LBRACE')
        body = self.parse_block()
        return ('While', cond, body)

    def parse_for(self):
        self.expect('KW_MAEU')
        var = self.expect('IDENTIFIER')[1]
        self.expect('IN')
        self.expect('RANGE')
        self.expect('LPAREN')
        args = [self.parse_expression()]
        while self.current() and self.current()[0] == 'COMMA':
            self.advance()
            args.append(self.parse_expression())
        self.expect('RPAREN')
        self.expect('COLON')
        self.expect('LBRACE')
        body = self.parse_block()
        return ('For', var, args, body)

    def parse_block(self):
        stmts = []
        self.skip_newlines()
        while self.current() and self.current()[0] != 'RBRACE':
            stmt = self.parse_statement()
            if stmt:
                stmts.append(stmt)
            self.skip_newlines()
        self.expect('RBRACE')
        return stmts

    # -------- 표현식 (우선순위 순서대로) --------
    def parse_expression(self):
        return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.current() and self.current()[0] == 'OR':
            self.advance()
            right = self.parse_and()
            left = ('Logical', 'or', left, right)
        return left

    def parse_and(self):
        left = self.parse_not()
        while self.current() and self.current()[0] == 'AND':
            self.advance()
            right = self.parse_not()
            left = ('Logical', 'and', left, right)
        return left

    def parse_not(self):
        if self.current() and self.current()[0] == 'NOT':
            self.advance()
            return ('UnaryOp', 'not', self.parse_not())
        return self.parse_comparison()

    def parse_comparison(self):
        left = self.parse_addsub()
        OP_MAP = {'EQ': '==', 'NEQ': '!=', 'LT': '<', 'LTE': '<=', 'GT': '>', 'GTE': '>='}
        while self.current() and self.current()[0] in OP_MAP:
            op_tok = self.advance()
            right = self.parse_addsub()
            left = ('Compare', OP_MAP[op_tok[0]], left, right)
        return left

    def parse_addsub(self):
        left = self.parse_muldiv()
        while self.current() and self.current()[0] in ('PLUS', 'MINUS'):
            op_tok = self.advance()
            op = '+' if op_tok[0] == 'PLUS' else '-'
            right = self.parse_muldiv()
            left = ('BinOp', op, left, right)
        return left

    def parse_muldiv(self):
        left = self.parse_primary()
        while self.current() and self.current()[0] in ('MUL', 'DIV'):
            op_tok = self.advance()
            op = '*' if op_tok[0] == 'MUL' else '/'
            right = self.parse_primary()
            left = ('BinOp', op, left, right)
        return left

    def parse_primary(self):
        tok = self.current()
        if not tok:
            raise ParseError("Unexpected end of input")
        if tok[0] == 'NUMBER':
            self.advance()
            return ('Number', tok[1])
        if tok[0] == 'STRING':
            self.advance()
            return ('String', tok[1])
        if tok[0] == 'IDENTIFIER':
            self.advance()
            return ('Identifier', tok[1])
        if tok[0] == 'LPAREN':
            self.advance()
            expr = self.parse_expression()
            self.expect('RPAREN')
            return expr
        raise ParseError(f"Unexpected token in expression: {tok}")


def parse(tokens):
    """토큰 리스트를 AST로 변환하는 편의 함수"""
    return Parser(tokens).parse_program()
