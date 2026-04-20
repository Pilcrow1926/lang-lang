"""
lang-lang (해씨)
=====================
한글 의성어/의태어로 이루어진 난해한 프로그래밍 언어.

사용 예:
    >>> from lang import run
    >>> run('난뭐정안녕정엇')
    안녕

    >>> from lang import number_to_sf, parse_number
    >>> number_to_sf(100)
    '대근근근근근근근근근근근근근근근근근랑'
    >>> parse_number('대훌훌훌랑')
    18
"""

__version__ = '0.1.0'

from .tokenizer import tokenize, TokenizeError
from .parser import parse, Parser, ParseError
from .interpreter import interpret, Interpreter, RuntimeError_
from .converter import (
    parse_number,
    number_to_sf,
    # 하위호환용 별칭
    parse_rang_number,
    number_to_rang,
)


def run(source):
    """해씨 소스 코드를 실행하는 최상위 함수

    Args:
        source: 해씨 소스 코드 문자열

    Returns:
        None (stdout에 출력)
    """
    tokens = tokenize(source)
    ast = parse(tokens)
    interpret(ast)


def run_file(path):
    """해씨 파일(.sf)을 읽어 실행

    Args:
        path: 파일 경로 (일반적으로 .sf 확장자)
    """
    with open(path, 'r', encoding='utf-8') as f:
        source = f.read()
    run(source)


__all__ = [
    '__version__',
    'run',
    'run_file',
    'tokenize',
    'parse',
    'interpret',
    'Parser',
    'Interpreter',
    'parse_number',
    'number_to_sf',
    'parse_rang_number',
    'number_to_rang',
    'TokenizeError',
    'ParseError',
    'RuntimeError_',
]
