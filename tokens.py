"""
Definições de tokens para o compilador
"""

from enum import Enum, auto

class TokenType(Enum):
    # Palavras reservadas
    PROGRAMA = auto()
    VAR = auto()
    INTEIRO = auto()
    BOOLEANO = auto()
    PROCEDIMENTO = auto()
    FUNCAO = auto()
    RETORNA = auto()
    INICIO = auto()
    FIM = auto()
    SE = auto()
    ENTAO = auto()
    SENAO = auto()
    ENQUANTO = auto()
    FACA = auto()
    LEIA = auto()
    ESCREVA = auto()
    PARE = auto()
    CONTINUE = auto()
    VERDADEIRO = auto()
    FALSO = auto()
    OU = auto()
    E = auto()
    NAO = auto()
    DIV = auto()
    
    # Identificadores e literais
    IDENTIFICADOR = auto()
    NUMERO = auto()
    
    # Operadores relacionais
    IGUAL = auto()          # ==
    DIFERENTE = auto()      # !=
    MENOR = auto()          # <
    MENOR_IGUAL = auto()    # <=
    MAIOR = auto()          # >
    MAIOR_IGUAL = auto()    # >=
    
    # Operadores aritméticos
    MAIS = auto()           # +
    MENOS = auto()          # -
    MULTIPLICACAO = auto()  # *
    
    # Delimitadores
    PONTO_VIRGULA = auto()  # ;
    DOIS_PONTOS = auto()    # :
    VIRGULA = auto()        # ,
    PONTO = auto()          # .
    ABRE_PAREN = auto()     # (
    FECHA_PAREN = auto()    # )
    ABRE_CHAVE = auto()     # {
    FECHA_CHAVE = auto()    # }
    ATRIBUICAO = auto()     # :=
    
    # Especiais
    EOF = auto()
    ERRO = auto()


# Palavras reservadas da linguagem
PALAVRAS_RESERVADAS = {
    'programa': TokenType.PROGRAMA,
    'var': TokenType.VAR,
    'inteiro': TokenType.INTEIRO,
    'booleano': TokenType.BOOLEANO,
    'procedimento': TokenType.PROCEDIMENTO,
    'funcao': TokenType.FUNCAO,
    'retorna': TokenType.RETORNA,
    'inicio': TokenType.INICIO,
    'fim': TokenType.FIM,
    'se': TokenType.SE,
    'entao': TokenType.ENTAO,
    'senao': TokenType.SENAO,
    'enquanto': TokenType.ENQUANTO,
    'faca': TokenType.FACA,
    'leia': TokenType.LEIA,
    'escreva': TokenType.ESCREVA,
    'pare': TokenType.PARE,
    'continue': TokenType.CONTINUE,
    'verdadeiro': TokenType.VERDADEIRO,
    'falso': TokenType.FALSO,
    'ou': TokenType.OU,
    'e': TokenType.E,
    'nao': TokenType.NAO,
    'div': TokenType.DIV,
}


class Token:
    """Representa um token encontrado no código fonte"""
    
    def __init__(self, tipo, lexema, linha, coluna):
        self.tipo = tipo
        self.lexema = lexema
        self.linha = linha
        self.coluna = coluna
    
    def __repr__(self):
        return f"Token({self.tipo.name}, '{self.lexema}', L{self.linha}:C{self.coluna})"
    
    def __str__(self):
        return f"<{self.tipo.name}, '{self.lexema}', linha {self.linha}>"
