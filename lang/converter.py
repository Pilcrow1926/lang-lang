"""
lang.converter
===================
랑(lang-lang)의 수 표현과 파이썬 숫자 간의 변환을 담당하는 모듈.

수 표현 규칙:
- 기본값: 여(0), 두(1), 근(3), 훌(5)
- '대' 접두사: +1 (한 번만 사용 가능, 소수점 제외)
- '느그' 접두사: 음수
- '끔': 소수점
- '랑': 수 표현의 끝

알고리즘:
  어떤 양의 정수 n에 대해:
  1) n이 짝수면 '대' 접두사를 붙이고 n-1로 변환 (홀수로)
  2) 홀수 n을 6으로 나눈 몫 + 1 = 기본값 반복 횟수
  3) 나머지가 1이면 '두', 3이면 '근', 5면 '훌'
  0은 특수 케이스로 '여랑'
"""

BASE_VALUES = {'여': 0, '두': 1, '근': 3, '훌': 5}
VALUE_TO_BASE = {1: '두', 3: '근', 5: '훌'}


# ============================================================
# 파싱: 해씨 표현 -> 숫자
# ============================================================

def _parse_single_number(text):
    """'대근근근' 같은 단일 수 표현(랑 제외)을 정수로 변환"""
    has_dae = False
    if text.startswith('대'):
        has_dae = True
        text = text[1:]

    if not text:
        raise ValueError("Empty number expression")

    base_char = text[0]
    if base_char not in BASE_VALUES:
        raise ValueError(f"Invalid base character: {base_char!r}")

    if not all(c == base_char for c in text):
        raise ValueError(f"Mixed base characters: {text!r}")

    base = BASE_VALUES[base_char]
    repeat_count = len(text)
    value = base + (repeat_count - 1) * 6
    if has_dae:
        value += 1
    return value


def _parse_decimal_digits(text):
    """소수부 문자열을 각 자릿수 리스트로 변환 (예: '대근훌대훌' -> [4,5,6])"""
    digits = []
    i = 0
    n = len(text)
    while i < n:
        has_dae = False
        if text[i] == '대':
            has_dae = True
            i += 1
        if i >= n:
            break

        base_char = text[i]
        if base_char not in BASE_VALUES:
            raise ValueError(f"Invalid base in decimal: {base_char!r}")

        count = 0
        while i < n and text[i] == base_char:
            count += 1
            i += 1

        digit = BASE_VALUES[base_char] + (count - 1) * 6
        if has_dae:
            digit += 1
        digits.append(digit)
    return digits


def parse_number(text):
    """해씨 수 표현을 파이썬 숫자로 변환

    Args:
        text: 해씨 수 표현 문자열 (예: '대훌훌훌랑', '느그두끔훌랑')

    Returns:
        int 또는 float
    """
    negative = False
    if text.startswith('느그'):
        negative = True
        text = text[2:]

    if not text.endswith('랑'):
        raise ValueError(f"Number must end with '랑': {text!r}")
    text = text[:-1]  # 랑 제거

    if '끔' in text:
        int_str, dec_str = text.split('끔', 1)
        int_val = _parse_single_number(int_str)
        dec_digits = _parse_decimal_digits(dec_str)
        dec_str_joined = ''.join(str(d) for d in dec_digits)
        value = float(f"{int_val}.{dec_str_joined}")
    else:
        value = _parse_single_number(text)

    return -value if negative else value


# ============================================================
# 변환: 숫자 -> 해씨 표현
# ============================================================

def _int_to_body(n):
    """양의 정수를 '랑' 없는 수 표현 몸통으로 변환 (0부터 가능)"""
    if n == 0:
        return '여'
    # 짝수면 대 붙이고 -1 (홀수로 변환)
    has_dae = (n % 2 == 0)
    if has_dae:
        n -= 1
    # 이제 n은 홀수
    # n = base + (repeat-1)*6, base는 1/3/5 중 하나
    repeat = (n - 1) // 6 + 1
    remainder = n - (repeat - 1) * 6
    if remainder not in VALUE_TO_BASE:
        raise ValueError(f"Cannot convert {n}")
    base_char = VALUE_TO_BASE[remainder]
    return ('대' if has_dae else '') + base_char * repeat


def number_to_sf(n):
    """일반 숫자를 해씨 수 표현으로 변환

    Args:
        n: 변환할 숫자 (int 또는 float)

    Returns:
        해씨 수 표현 문자열
    """
    if isinstance(n, float):
        if n.is_integer():
            return number_to_sf(int(n))
        negative = n < 0
        n = abs(n)
        int_part = int(n)
        # 소수 부분 문자열 (파이썬 repr 사용)
        dec_str = repr(n).split('.')[1]
        int_rang = _int_to_body(int_part)
        dec_rang = ''.join(_int_to_body(int(d)) for d in dec_str)
        result = f"{int_rang}끔{dec_rang}랑"
        return ('느그' if negative else '') + result

    negative = n < 0
    n = abs(n)
    body = _int_to_body(n)
    return ('느그' if negative else '') + body + '랑'


# 하위호환용 별칭 (기존 코드가 쓰던 이름)
parse_rang_number = parse_number
number_to_rang = number_to_sf
