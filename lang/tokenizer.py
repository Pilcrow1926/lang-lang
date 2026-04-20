"""
lang.tokenizer
===================
해씨(lang-lang) 소스 코드를 토큰 리스트로 변환하는 토크나이저.
 
토큰 타입:
- NUMBER, STRING, IDENTIFIER: 리터럴과 식별자
- NEWLINE: 줄바꿈 (문장 구분자)
- 각종 키워드 타입: ASSIGN, EQ, PLUS, IF, WHILE 등
"""
 
from .converter import parse_number
 
 
KEYWORDS = {
    # 타입
    '이건': 'TYPE_STRING',
    '매우': 'KW_MAEU',      # int 선언 또는 for (문맥에 따라)
    '안타까워': 'TYPE_FLOAT',
 
    # 제어문
    '난': 'PRINT',
    '엄': 'IF',
    '내꿈꿔': 'ELSE',
    '장미': 'WHILE',
    '뒷': 'IN',
    '나가': 'RANGE',
 
    # 비교 연산자 (긴 것부터 매칭)
    '캬캬': 'EQ',          # ==
    '와캬': 'NEQ',         # !=
    '준캬': 'LTE',         # <=
    '영캬': 'GTE',         # >=
    '캬': 'ASSIGN',        # =
    '준': 'LT',            # <
    '영': 'GT',            # >
 
    # 증감
    '허얼': 'INC',         # ++
    '네에': 'DEC',         # --
 
    # 산술
    '헐': 'PLUS',          # +
    '네': 'MINUS',         # -
    '겸': 'MUL',           # *
    '헉': 'DIV',           # /
 
    # 논리
    '심지어': 'AND',
    '끔찍해': 'OR',
    '죽어': 'NOT',
 
    # 괄호/중괄호
    '뭐': 'LPAREN',        # (
    '엇': 'RPAREN',        # )
    '택': 'LBRACE',        # {
    '틱': 'RBRACE',        # }
 
    # 구두점
    '호야': 'COLON',       # :
    '그래': 'COMMA',       # ,
}
 
# 길이 내림차순으로 정렬 (긴 키워드 우선 매칭)
_SORTED_KEYWORDS = sorted(KEYWORDS.items(), key=lambda x: -len(x[0]))
 
 
class TokenizeError(Exception):
    """토크나이저 에러"""
    pass
 
 
def tokenize(source):
    """해씨 소스 코드를 토큰 리스트로 변환
 
    Args:
        source: 해씨 소스 코드 문자열
 
    Returns:
        토큰 리스트. 각 토큰은 (type, value) 튜플.
 
    Raises:
        TokenizeError: 토큰화 실패 시
    """
    tokens = []
    pos = 0
    n = len(source)
    ident_buf = []
 
    def flush_ident():
        if ident_buf:
            tokens.append(('IDENTIFIER', ''.join(ident_buf)))
            ident_buf.clear()
 
    while pos < n:
        c = source[pos]
 
        # 공백/탭/캐리지 리턴 무시 (식별자 경계)
        if c in ' \t\r':
            flush_ident()
            pos += 1
            continue
 
        # 줄바꿈: '결국' 키워드 또는 일반 \n 모두 허용
        if source[pos:pos+2] == '결국':
            flush_ident()
            if not tokens or tokens[-1][0] != 'NEWLINE':
                tokens.append(('NEWLINE', None))
            pos += 2
            continue
 
        if c == '\n':
            flush_ident()
            if not tokens or tokens[-1][0] != 'NEWLINE':
                tokens.append(('NEWLINE', None))
            pos += 1
            continue
 
        # 문자열: 정...정 (이스케이프 지원)
        if c == '정':
            flush_ident()
            result = []
            pos += 1  # 여는 정 건너뜀
            closed = False
            while pos < n:
                ch = source[pos]
                if ch == '정':
                    # 닫는 정
                    pos += 1
                    closed = True
                    break
                elif ch == '빛':
                    # 단일 이스케이프: 빛 + 다음 문자를 문자 그대로
                    pos += 1
                    if pos < n:
                        result.append(source[pos])
                        pos += 1
                elif ch == '비':
                    # 이스케이프 블록: 비...잋
                    pos += 1
                    while pos < n:
                        if source[pos] == '잋':
                            pos += 1
                            break
                        elif source[pos] == '빛' and pos + 1 < n and source[pos + 1] == '잋':
                            # 빛잋 → 잋 문자 그대로
                            result.append('잋')
                            pos += 2
                        else:
                            result.append(source[pos])
                            pos += 1
                else:
                    result.append(ch)
                    pos += 1
            if not closed:
                raise TokenizeError(f"Unclosed string")
            tokens.append(('STRING', ''.join(result)))
            continue
 
        # 수 표현 감지 (느그/대+기본값/여두근훌)
        is_num = False
        if source[pos:pos + 2] == '느그':
            is_num = True
        elif c == '대' and pos + 1 < n and source[pos + 1] in '여두근훌':
            is_num = True
        elif c in '여두근훌':
            is_num = True
 
        if is_num:
            flush_ident()
            end = source.find('랑', pos)
            if end == -1:
                raise TokenizeError(f"Expected '랑' at position {pos}")
            num_text = source[pos:end + 1]
            try:
                value = parse_number(num_text)
            except ValueError as e:
                raise TokenizeError(f"Invalid number {num_text!r}: {e}")
            tokens.append(('NUMBER', value))
            pos = end + 1
            continue
 
        # 키워드 매칭 (길이 내림차순)
        matched = False
        for kw, tok_type in _SORTED_KEYWORDS:
            if source[pos:pos + len(kw)] == kw:
                flush_ident()
                tokens.append((tok_type, kw))
                pos += len(kw)
                matched = True
                break
        if matched:
            continue
 
        # 식별자 안에서 비...잋 이스케이프 블록
        if c == '비':
            pos += 1
            while pos < n:
                if source[pos] == '잋':
                    pos += 1
                    break
                elif source[pos] == '빛' and pos + 1 < n and source[pos + 1] == '잋':
                    ident_buf.append('잋')
                    pos += 2
                else:
                    ident_buf.append(source[pos])
                    pos += 1
            continue
 
        # 식별자 문자 누적 (키워드/숫자/문자열/공백/줄바꿈 어디에도 안 걸린 문자)
        ident_buf.append(c)
        pos += 1
 
    flush_ident()
    return tokens