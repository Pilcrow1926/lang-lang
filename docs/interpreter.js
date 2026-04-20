/**
 * 해씨 (sunflower-lang) JavaScript 인터프리터
 * Tokenizer → Parser → Interpreter
 */

const SunflowerInterpreter = (() => {

  // ============================================================
  // 1. 수 변환 (Converter)
  // ============================================================

  const BASE_VALUES = { '여': 0, '두': 1, '근': 3, '훌': 5 };

  function parseSingleNumber(text) {
    let hasDae = false;
    if (text.startsWith('대')) {
      hasDae = true;
      text = text.slice(1);
    }
    if (!text) throw new Error(`빈 수 표현`);
    const baseChar = text[0];
    if (!(baseChar in BASE_VALUES)) throw new Error(`잘못된 기본값: ${baseChar}`);
    if ([...text].some(c => c !== baseChar)) throw new Error(`혼합된 기본값: ${text}`);
    const base = BASE_VALUES[baseChar];
    const repeat = text.length;
    return base + (repeat - 1) * 6 + (hasDae ? 1 : 0);
  }

  function parseDecimalDigits(text) {
    const digits = [];
    let i = 0;
    while (i < text.length) {
      let hasDae = false;
      if (text[i] === '대') { hasDae = true; i++; }
      if (i >= text.length) break;
      const baseChar = text[i];
      if (!(baseChar in BASE_VALUES)) throw new Error(`잘못된 소수 기본값: ${baseChar}`);
      let count = 0;
      while (i < text.length && text[i] === baseChar) { count++; i++; }
      digits.push(BASE_VALUES[baseChar] + (count - 1) * 6 + (hasDae ? 1 : 0));
    }
    return digits;
  }

  function parseNumber(text) {
    let negative = false;
    if (text.startsWith('느그')) { negative = true; text = text.slice(2); }
    if (!text.endsWith('랑')) throw new Error(`'랑'으로 끝나야 합니다: ${text}`);
    text = text.slice(0, -1);

    let value;
    if (text.includes('끔')) {
      const [intStr, decStr] = text.split('끔');
      const intVal = parseSingleNumber(intStr);
      const decDigits = parseDecimalDigits(decStr);
      value = parseFloat(`${intVal}.${decDigits.join('')}`);
    } else {
      value = parseSingleNumber(text);
    }
    return negative ? -value : value;
  }

  // ============================================================
  // 2. 토크나이저 (Tokenizer)
  // ============================================================

  const KEYWORDS = {
    '이건': 'TYPE_STRING',
    '매우': 'KW_MAEU',
    '안타까워': 'TYPE_FLOAT',
    '난': 'PRINT',
    '엄': 'IF',
    '내꿈꿔': 'ELSE',
    '장미': 'WHILE',
    '뒷': 'IN',
    '나가': 'RANGE',
    '캬캬': 'EQ',
    '와캬': 'NEQ',
    '준캬': 'LTE',
    '영캬': 'GTE',
    '캬': 'ASSIGN',
    '준': 'LT',
    '영': 'GT',
    '허얼': 'INC',
    '네에': 'DEC',
    '헐': 'PLUS',
    '네': 'MINUS',
    '겸': 'MUL',
    '헉': 'DIV',
    '심지어': 'AND',
    '끔찍해': 'OR',
    '죽어': 'NOT',
    '뭐': 'LPAREN',
    '엇': 'RPAREN',
    '택': 'LBRACE',
    '틱': 'RBRACE',
    '호야': 'COLON',
    '그래': 'COMMA',
  };

  const SORTED_KEYWORDS = Object.entries(KEYWORDS).sort((a, b) => b[0].length - a[0].length);

  function tokenize(source) {
    const tokens = [];
    let pos = 0;
    let identBuf = [];

    const flushIdent = () => {
      if (identBuf.length) {
        tokens.push(['IDENTIFIER', identBuf.join('')]);
        identBuf = [];
      }
    };

    while (pos < source.length) {
      const c = source[pos];

      // 공백/탭/캐리지리턴
      if (c === ' ' || c === '\t' || c === '\r') {
        flushIdent();
        pos++;
        continue;
      }

      // 줄바꿈
      if (c === '\n') {
        flushIdent();
        if (!tokens.length || tokens[tokens.length - 1][0] !== 'NEWLINE') {
          tokens.push(['NEWLINE', null]);
        }
        pos++;
        continue;
      }

      // 문자열: 정...정 (이스케이프 지원)
      if (c === '정') {
        flushIdent();
        pos++;
        const result = [];
        let closed = false;
        while (pos < source.length) {
          const ch = source[pos];
          if (ch === '정') {
            pos++;
            closed = true;
            break;
          } else if (ch === '빛') {
            pos++;
            if (pos < source.length) { result.push(source[pos]); pos++; }
          } else if (ch === '비') {
            pos++;
            while (pos < source.length) {
              if (source[pos] === '잋') { pos++; break; }
              else if (source[pos] === '빛' && pos + 1 < source.length && source[pos + 1] === '잋') {
                result.push('잋'); pos += 2;
              } else { result.push(source[pos]); pos++; }
            }
          } else {
            result.push(ch);
            pos++;
          }
        }
        if (!closed) throw new Error('닫히지 않은 문자열');
        tokens.push(['STRING', result.join('')]);
        continue;
      }

      // 수 표현 감지
      const isNum = source.slice(pos, pos + 2) === '느그' ||
        (c === '대' && pos + 1 < source.length && '여두근훌'.includes(source[pos + 1])) ||
        '여두근훌'.includes(c);

      if (isNum) {
        flushIdent();
        const end = source.indexOf('랑', pos);
        if (end === -1) throw new Error(`'랑'이 없습니다 (pos ${pos})`);
        const numText = source.slice(pos, end + 1);
        tokens.push(['NUMBER', parseNumber(numText)]);
        pos = end + 1;
        continue;
      }

      // 키워드 매칭
      let matched = false;
      for (const [kw, type] of SORTED_KEYWORDS) {
        if (source.slice(pos, pos + kw.length) === kw) {
          flushIdent();
          tokens.push([type, kw]);
          pos += kw.length;
          matched = true;
          break;
        }
      }
      if (matched) continue;

      // 식별자 안에서 비...잋 이스케이프 블록
      if (c === '비') {
        pos++;
        while (pos < source.length) {
          if (source[pos] === '잋') { pos++; break; }
          else if (source[pos] === '빛' && pos + 1 < source.length && source[pos + 1] === '잋') {
            identBuf.push('잋'); pos += 2;
          } else { identBuf.push(source[pos]); pos++; }
        }
        continue;
      }

      identBuf.push(c);
      pos++;
    }

    flushIdent();
    return tokens;
  }

  // ============================================================
  // 3. 파서 (Parser)
  // ============================================================

  class Parser {
    constructor(tokens) {
      this.tokens = tokens;
      this.pos = 0;
    }

    current() { return this.tokens[this.pos] || null; }
    peek(offset = 0) { return this.tokens[this.pos + offset] || null; }
    advance() { return this.tokens[this.pos++]; }

    expect(type) {
      if (this.current() && this.current()[0] === type) return this.advance();
      throw new Error(`'${type}' 예상, '${this.current()?.[0]}' 발견`);
    }

    skipNewlines() {
      while (this.current() && this.current()[0] === 'NEWLINE') this.advance();
    }

    parseProgram() {
      const stmts = [];
      this.skipNewlines();
      while (this.current()) {
        stmts.push(this.parseStatement());
        this.skipNewlines();
      }
      return ['Program', stmts];
    }

    parseStatement() {
      const tok = this.current();
      if (!tok) return null;
      const t = tok[0];

      if (t === 'TYPE_STRING' || t === 'TYPE_FLOAT') return this.parseVarDecl();

      if (t === 'KW_MAEU') {
        if (this.peek(1)?.[0] === 'IDENTIFIER' && this.peek(2)?.[0] === 'IN')
          return this.parseFor();
        return this.parseVarDecl();
      }

      if (t === 'PRINT') return this.parsePrint();
      if (t === 'IF') return this.parseIf();
      if (t === 'WHILE') return this.parseWhile();

      if (t === 'IDENTIFIER') {
        if (this.peek(1)?.[0] === 'ASSIGN') return this.parseAssign();
        if (this.peek(1)?.[0] === 'INC' || this.peek(1)?.[0] === 'DEC') return this.parseIncDec();
      }

      throw new Error(`예상치 못한 토큰: ${tok}`);
    }

    parseVarDecl() {
      const typeTok = this.advance();
      const typeMap = { 'TYPE_STRING': 'string', 'TYPE_FLOAT': 'float', 'KW_MAEU': 'int' };
      const varType = typeMap[typeTok[0]];
      const name = this.expect('IDENTIFIER')[1];
      this.expect('ASSIGN');
      const value = this.parseExpression();
      return ['VarDecl', varType, name, value];
    }

    parseAssign() {
      const name = this.expect('IDENTIFIER')[1];
      this.expect('ASSIGN');
      return ['Assign', name, this.parseExpression()];
    }

    parseIncDec() {
      const name = this.expect('IDENTIFIER')[1];
      const op = this.advance()[0] === 'INC' ? '++' : '--';
      return ['IncDec', name, op];
    }

    parsePrint() {
      this.expect('PRINT');
      this.expect('LPAREN');
      const val = this.parseExpression();
      this.expect('RPAREN');
      return ['Print', val];
    }

    parseIf() {
      this.expect('IF');
      this.expect('LPAREN');
      const cond = this.parseExpression();
      this.expect('RPAREN');
      this.expect('COLON');
      this.expect('LBRACE');
      const thenBlock = this.parseBlock();

      let elseBlock = null;
      const save = this.pos;
      this.skipNewlines();
      if (this.current()?.[0] === 'ELSE') {
        this.advance();
        if (this.current()?.[0] === 'IF') {
          elseBlock = [this.parseIf()];
        } else {
          this.expect('COLON');
          this.expect('LBRACE');
          elseBlock = this.parseBlock();
        }
      } else {
        this.pos = save;
      }

      return ['If', cond, thenBlock, elseBlock];
    }

    parseWhile() {
      this.expect('WHILE');
      this.expect('LPAREN');
      const cond = this.parseExpression();
      this.expect('RPAREN');
      this.expect('COLON');
      this.expect('LBRACE');
      return ['While', cond, this.parseBlock()];
    }

    parseFor() {
      this.expect('KW_MAEU');
      const varName = this.expect('IDENTIFIER')[1];
      this.expect('IN');
      this.expect('RANGE');
      this.expect('LPAREN');
      const args = [this.parseExpression()];
      while (this.current()?.[0] === 'COMMA') {
        this.advance();
        args.push(this.parseExpression());
      }
      this.expect('RPAREN');
      this.expect('COLON');
      this.expect('LBRACE');
      return ['For', varName, args, this.parseBlock()];
    }

    parseBlock() {
      const stmts = [];
      this.skipNewlines();
      while (this.current() && this.current()[0] !== 'RBRACE') {
        stmts.push(this.parseStatement());
        this.skipNewlines();
      }
      this.expect('RBRACE');
      return stmts;
    }

    parseExpression() { return this.parseOr(); }

    parseOr() {
      let left = this.parseAnd();
      while (this.current()?.[0] === 'OR') {
        this.advance();
        left = ['Logical', 'or', left, this.parseAnd()];
      }
      return left;
    }

    parseAnd() {
      let left = this.parseNot();
      while (this.current()?.[0] === 'AND') {
        this.advance();
        left = ['Logical', 'and', left, this.parseNot()];
      }
      return left;
    }

    parseNot() {
      if (this.current()?.[0] === 'NOT') {
        this.advance();
        return ['UnaryOp', 'not', this.parseNot()];
      }
      return this.parseComparison();
    }

    parseComparison() {
      const OPS = { 'EQ': '==', 'NEQ': '!=', 'LT': '<', 'LTE': '<=', 'GT': '>', 'GTE': '>=' };
      let left = this.parseAddSub();
      while (this.current() && this.current()[0] in OPS) {
        const op = OPS[this.advance()[0]];
        left = ['Compare', op, left, this.parseAddSub()];
      }
      return left;
    }

    parseAddSub() {
      let left = this.parseMulDiv();
      while (this.current() && (this.current()[0] === 'PLUS' || this.current()[0] === 'MINUS')) {
        const op = this.advance()[0] === 'PLUS' ? '+' : '-';
        left = ['BinOp', op, left, this.parseMulDiv()];
      }
      return left;
    }

    parseMulDiv() {
      let left = this.parsePrimary();
      while (this.current() && (this.current()[0] === 'MUL' || this.current()[0] === 'DIV')) {
        const op = this.advance()[0] === 'MUL' ? '*' : '/';
        left = ['BinOp', op, left, this.parsePrimary()];
      }
      return left;
    }

    parsePrimary() {
      const tok = this.current();
      if (!tok) throw new Error('예상치 못한 입력 끝');
      if (tok[0] === 'NUMBER') { this.advance(); return ['Number', tok[1]]; }
      if (tok[0] === 'STRING') { this.advance(); return ['String', tok[1]]; }
      if (tok[0] === 'IDENTIFIER') { this.advance(); return ['Identifier', tok[1]]; }
      if (tok[0] === 'LPAREN') {
        this.advance();
        const expr = this.parseExpression();
        this.expect('RPAREN');
        return expr;
      }
      throw new Error(`표현식에서 예상치 못한 토큰: ${tok}`);
    }
  }

  // ============================================================
  // 4. 인터프리터 (Interpreter)
  // ============================================================

  function fmt(v) {
    if (typeof v === 'number' && Number.isInteger(v)) return String(v);
    if (typeof v === 'number') return String(v);
    return String(v);
  }

  class Interpreter {
    constructor(outputCallback) {
      this.env = {};
      this.output = outputCallback;
    }

    run(ast) {
      for (const stmt of ast[1]) this.execStmt(stmt);
    }

    execStmt(stmt) {
      const t = stmt[0];

      if (t === 'VarDecl') {
        const [, vt, name, expr] = stmt;
        let v = this.evalExpr(expr);
        if (vt === 'int') v = Math.trunc(Number(v));
        else if (vt === 'float') v = Number(v);
        else if (vt === 'string') v = String(v);
        this.env[name] = v;
      }

      else if (t === 'Assign') {
        this.env[stmt[1]] = this.evalExpr(stmt[2]);
      }

      else if (t === 'IncDec') {
        const [, name, op] = stmt;
        if (!(name in this.env)) throw new Error(`정의되지 않은 변수: ${name}`);
        this.env[name] += op === '++' ? 1 : -1;
      }

      else if (t === 'Print') {
        this.output(fmt(this.evalExpr(stmt[1])));
      }

      else if (t === 'If') {
        const [, cond, thenB, elseB] = stmt;
        if (this.evalExpr(cond)) this.execBlock(thenB);
        else if (elseB) this.execBlock(elseB);
      }

      else if (t === 'While') {
        const [, cond, body] = stmt;
        let limit = 100000;
        while (this.evalExpr(cond)) {
          if (--limit < 0) throw new Error('무한 루프 감지 (100000회 초과)');
          this.execBlock(body);
        }
      }

      else if (t === 'For') {
        const [, varName, args, body] = stmt;
        const vals = args.map(a => Math.trunc(this.evalExpr(a)));
        const [start, end, step] = vals.length === 1 ? [0, vals[0], 1]
          : vals.length === 2 ? [vals[0], vals[1], 1]
          : vals;
        let limit = 100000;
        for (let i = start; step > 0 ? i < end : i > end; i += step) {
          if (--limit < 0) throw new Error('무한 루프 감지 (100000회 초과)');
          this.env[varName] = i;
          this.execBlock(body);
        }
      }

      else throw new Error(`알 수 없는 문장: ${t}`);
    }

    execBlock(block) {
      for (const s of block) this.execStmt(s);
    }

    evalExpr(expr) {
      const t = expr[0];

      if (t === 'Number') return expr[1];
      if (t === 'String') return expr[1];
      if (t === 'Identifier') {
        if (!(expr[1] in this.env)) throw new Error(`정의되지 않은 변수: ${expr[1]}`);
        return this.env[expr[1]];
      }

      if (t === 'BinOp') {
        const [, op, l, r] = expr;
        const lv = this.evalExpr(l), rv = this.evalExpr(r);
        if (op === '+') {
          if (typeof lv === 'string' || typeof rv === 'string') return fmt(lv) + fmt(rv);
          return lv + rv;
        }
        if (op === '-') return lv - rv;
        if (op === '*') return lv * rv;
        if (op === '/') return lv / rv;
      }

      if (t === 'Compare') {
        const [, op, l, r] = expr;
        const lv = this.evalExpr(l), rv = this.evalExpr(r);
        return { '==': lv == rv, '!=': lv != rv, '<': lv < rv, '<=': lv <= rv, '>': lv > rv, '>=': lv >= rv }[op];
      }

      if (t === 'Logical') {
        const [, op, l, r] = expr;
        if (op === 'and') return this.evalExpr(l) && this.evalExpr(r);
        if (op === 'or') return this.evalExpr(l) || this.evalExpr(r);
      }

      if (t === 'UnaryOp') {
        return !this.evalExpr(expr[2]);
      }

      throw new Error(`알 수 없는 표현식: ${t}`);
    }
  }

  // ============================================================
  // 5. 공개 API
  // ============================================================

  function run(source) {
    const outputLines = [];
    let error = null;

    try {
      const tokens = tokenize(source);
      const ast = new Parser(tokens).parseProgram();
      const interp = new Interpreter(line => outputLines.push(line));
      interp.run(ast);
    } catch (e) {
      error = e.message;
    }

    return { output: outputLines, error };
  }

  return { run, tokenize, parseNumber };

})();
