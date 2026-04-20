"""
sunflower.cli
=============
해씨(sunflower-lang) CLI 진입점.

사용법:
    sunflower <file.sf>              파일 실행
    sunflower --version              버전 출력
    sunflower --help                 도움말 출력
    sunflower --convert <number>     숫자 → 해씨 표현 변환
"""

import sys
from . import run_file, number_to_sf, __version__
from .tokenizer import TokenizeError
from .parser import ParseError
from .interpreter import RuntimeError_

HELP = """
🌻 해씨 (sunflower-lang) 인터프리터

사용법:
  sunflower <file.sf>              .sf 파일 실행
  sunflower --convert <number>     숫자를 해씨 표현으로 변환
  sunflower --version              버전 출력
  sunflower --help                 도움말 출력

예시:
  sunflower hello.sf
  sunflower --convert 100
""".strip()


def main():
    args = sys.argv[1:]

    if not args or '--help' in args or '-h' in args:
        print(HELP)
        return

    if '--version' in args or '-v' in args:
        print(f"sunflower-lang v{__version__}")
        return

    if '--convert' in args or '-c' in args:
        try:
            idx = args.index('--convert') if '--convert' in args else args.index('-c')
            n = args[idx + 1]
            # 정수/실수 판별
            value = float(n) if '.' in n else int(n)
            print(number_to_sf(value))
        except (IndexError, ValueError):
            print("사용법: sunflower --convert <number>", file=sys.stderr)
            sys.exit(1)
        return

    # 파일 실행
    filepath = args[0]
    try:
        run_file(filepath)
    except FileNotFoundError:
        print(f"오류: 파일을 찾을 수 없습니다 - {filepath!r}", file=sys.stderr)
        sys.exit(1)
    except TokenizeError as e:
        print(f"토큰 오류: {e}", file=sys.stderr)
        sys.exit(1)
    except ParseError as e:
        print(f"파싱 오류: {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError_ as e:
        print(f"런타임 오류: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
