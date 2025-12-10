"""
Compilador - Programa Principal
Integra o analisador léxico e sintático
"""

import sys
from lexer import Lexer
from parser import Parser


def compilar(arquivo_fonte):
    """Compila um arquivo de código fonte"""
    
    print("=" * 80)
    print(f"COMPILADOR - Análise Léxica e Sintática")
    print(f"Arquivo: {arquivo_fonte}")
    print("=" * 80)
    print()
    
    # Ler o arquivo fonte
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
    print("-" * 80)
    print(codigo)
    print("-" * 80)
    print()
    
    # ANÁLISE LÉXICA
    print("ANÁLISE LÉXICA")
    print("-" * 80)
    
    lexer = Lexer(codigo)
    tokens, erros_lexicos = lexer.tokenizar()
    
    if erros_lexicos:
        print("ERROS LÉXICOS ENCONTRADOS:")
        for erro in erros_lexicos:
            print(f"  {erro}")
        print()
        return False
    
    print("Tokens encontrados:")
    print()
    for i, token in enumerate(tokens):
        if token.tipo.name != 'EOF':
            print(f"  {i+1:3d}. {token}")
    
    print()
    print(f"Total de tokens: {len(tokens) - 1} (excluindo EOF)")
    print("Análise léxica concluída sem erros")
    print()
    
    
    # ANÁLISE SINTÁTICA 
    print("ANÁLISE SINTÁTICA")
    print("-" * 80)
    
    parser = Parser(tokens)
    sucesso, erros_sintaticos = parser.analisar()
    
    if erros_sintaticos:
        print("ERROS SINTÁTICOS ENCONTRADOS:")
        for erro in erros_sintaticos:
            print(f"{erro}")
        print()
        return False
    
    if sucesso:
        print("Análise sintática concluída sem erros")
        print()
        print("=" * 80)
        print("COMPILAÇÃO BEM-SUCEDIDA!")
        print("  O programa está sintaticamente correto.")
        print("=" * 80)
        return True
    else:
        print()
        print("=" * 80)
        print("COMPILAÇÃO FALHOU")
        print("=" * 80)
        return False


def main():
    """Função principal"""
    
    if len(sys.argv) != 2:
        print("Uso: python main.py <arquivo_fonte>")
        print()
        print("Exemplo:")
        print("  python main.py programa.txt")
        sys.exit(1)
    
    arquivo_fonte = sys.argv[1]
    sucesso = compilar(arquivo_fonte)
    
    sys.exit(0 if sucesso else 1)


if __name__ == "__main__":
    main()
