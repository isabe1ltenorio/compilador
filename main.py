"""
Compilador - Programa Principal
Integra análise léxica, sintática e semântica
"""

import sys
from lexer import Lexer
from parser import Parser


def compilar(arquivo_fonte: str) -> bool:
    SEP  = "=" * 80
    DASH = "-" * 80

    print(SEP)
    print(f"COMPILADOR — Léxico + Sintático + Semântico")
    print(f"Arquivo: {arquivo_fonte}")
    print(SEP)
    print()

    # ── Leitura do arquivo ────────────────────────────────────────────────
    try:
        with open(arquivo_fonte, 'r', encoding='utf-8') as f:
            codigo = f.read()
    except FileNotFoundError:
        print(f"ERRO: Arquivo '{arquivo_fonte}' não encontrado.")
        return False
    except Exception as e:
        print(f"ERRO ao ler arquivo: {e}")
        return False

    print("CÓDIGO FONTE:")
    print(DASH)
    print(codigo)
    print(DASH)
    print()

    # ── Fase 1: Análise Léxica ────────────────────────────────────────────
    print("FASE 1 — ANÁLISE LÉXICA")
    print(DASH)

    lexer = Lexer(codigo)
    tokens, erros_lexicos = lexer.tokenizar()

    if erros_lexicos:
        print("ERROS LÉXICOS:")
        for e in erros_lexicos:
            print(f"  {e}")
        print()
        _imprimir_falha()
        return False

    print("Tokens encontrados:\n")
    for i, token in enumerate(tokens):
        if token.tipo.name != 'EOF':
            print(f"  {i+1:4d}. {token}")
    print()
    print(f"Total: {len(tokens) - 1} tokens (sem EOF)")
    print("✓ Análise léxica sem erros")
    print()

    # ── Fase 2 + 3: Análise Sintática e Semântica ─────────────────────────
    print("FASE 2 — ANÁLISE SINTÁTICA")
    print(DASH)

    parser = Parser(tokens)
    sucesso, erros_sintaticos, erros_semanticos = parser.analisar()

    if erros_sintaticos:
        print("ERROS SINTÁTICOS:")
        for e in erros_sintaticos:
            print(f"  {e}")
        print()
        _imprimir_falha()
        return False

    print("✓ Análise sintática sem erros")
    print()

    print("FASE 3 — ANÁLISE SEMÂNTICA")
    print(DASH)

    if erros_semanticos:
        print("ERROS SEMÂNTICOS:")
        for e in erros_semanticos:
            print(f"  {e}")
        print()
        _imprimir_falha()
        return False

    print("✓ Análise semântica sem erros")
    print()

    # ── Tabela de símbolos ────────────────────────────────────────────────
    print("TABELA DE SÍMBOLOS")
    print(DASH)
    historico = parser.tabela.listar_historico()
    if historico:
        for entrada in historico:
            print(f"  {entrada}")
    else:
        print("  (vazia)")
    print()

    _imprimir_sucesso()
    return True


def _imprimir_sucesso():
    print("=" * 80)
    print("COMPILAÇÃO BEM-SUCEDIDA!")
    print("  Léxico ✓  Sintático ✓  Semântico ✓")
    print("=" * 80)


def _imprimir_falha():
    print("=" * 80)
    print("COMPILAÇÃO FALHOU")
    print("=" * 80)


def main():
    if len(sys.argv) != 2:
        print("Uso: python main.py <arquivo_fonte>")
        print("Exemplo: python main.py programa.txt")
        sys.exit(1)
    sucesso = compilar(sys.argv[1])
    sys.exit(0 if sucesso else 1)


if __name__ == "__main__":
    main()
