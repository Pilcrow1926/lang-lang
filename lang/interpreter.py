"""
lang.interpreter
=====================
AST를 직접 실행하는 트리 워킹(tree-walking) 인터프리터.
"""
 
 
class RuntimeError_(Exception):
    """런타임 에러"""
    pass
 
 
class Interpreter:
    def __init__(self):
        self.env = {}
 
    def run(self, ast):
        if ast[0] != 'Program':
            raise RuntimeError_(f"Expected Program node, got {ast[0]}")
        for stmt in ast[1]:
            self.exec_stmt(stmt)
 
    # -------- 문장 실행 --------
    def exec_stmt(self, stmt):
        t = stmt[0]
 
        if t == 'VarDecl':
            _, vt, name, expr = stmt
            v = self.eval_expr(expr)
            # 선언 타입에 따라 캐스팅
            if vt == 'int':
                v = int(v)
            elif vt == 'float':
                v = float(v)
            elif vt == 'string':
                v = str(v)
            self.env[name] = v
 
        elif t == 'Assign':
            _, name, expr = stmt
            self.env[name] = self.eval_expr(expr)
 
        elif t == 'IncDec':
            _, name, op = stmt
            if name not in self.env:
                raise RuntimeError_(f"Undefined variable: {name}")
            if op == '++':
                self.env[name] += 1
            else:
                self.env[name] -= 1
 
        elif t == 'Print':
            v = self.eval_expr(stmt[1])
            print(self._format_output(v))
 
        elif t == 'If':
            _, cond, then_b, else_b = stmt
            if self.eval_expr(cond):
                self.exec_block(then_b)
            elif else_b:
                self.exec_block(else_b)
 
        elif t == 'While':
            _, cond, body = stmt
            while self.eval_expr(cond):
                self.exec_block(body)
 
        elif t == 'For':
            _, var, args, body = stmt
            vals = [int(self.eval_expr(a)) for a in args]
            if len(vals) == 1:
                it = range(vals[0])
            elif len(vals) == 2:
                it = range(vals[0], vals[1])
            elif len(vals) == 3:
                it = range(vals[0], vals[1], vals[2])
            else:
                raise RuntimeError_(f"range takes 1-3 arguments, got {len(vals)}")
            for i in it:
                self.env[var] = i
                self.exec_block(body)
 
        else:
            raise RuntimeError_(f"Unknown statement: {t}")
 
    def exec_block(self, block):
        for s in block:
            self.exec_stmt(s)
 
    # -------- 표현식 평가 --------
    def eval_expr(self, expr):
        t = expr[0]
 
        if t == 'Number':
            return expr[1]
        if t == 'String':
            return expr[1]
        if t == 'Identifier':
            name = expr[1]
            if name not in self.env:
                raise RuntimeError_(f"Undefined variable: {name}")
            return self.env[name]
 
        if t == 'BinOp':
            _, op, l, r = expr
            lv = self.eval_expr(l)
            rv = self.eval_expr(r)
            if op == '+':
                # 문자열이 끼어있으면 문자열 결합
                if isinstance(lv, str) or isinstance(rv, str):
                    return self._format_output(lv) + self._format_output(rv)
                return lv + rv
            if op == '-': return lv - rv
            if op == '*': return lv * rv
            if op == '/': return lv / rv
 
        if t == 'Compare':
            _, op, l, r = expr
            lv = self.eval_expr(l)
            rv = self.eval_expr(r)
            return {
                '==': lv == rv, '!=': lv != rv,
                '<': lv < rv, '<=': lv <= rv,
                '>': lv > rv, '>=': lv >= rv,
            }[op]
 
        if t == 'Logical':
            _, op, l, r = expr
            lv = self.eval_expr(l)
            if op == 'and':
                return bool(lv) and bool(self.eval_expr(r))
            if op == 'or':
                return bool(lv) or bool(self.eval_expr(r))
 
        if t == 'UnaryOp':
            _, op, o = expr
            if op == 'not':
                return not self.eval_expr(o)
 
        raise RuntimeError_(f"Unknown expression: {t}")
 
    # -------- 출력 포맷팅 --------
    @staticmethod
    def _format_output(v):
        """float인데 정수값이면 정수로 출력"""
        if isinstance(v, float) and v.is_integer():
            return str(int(v))
        return str(v)
 
 
def interpret(ast):
    """AST를 실행하는 편의 함수"""
    Interpreter().run(ast)