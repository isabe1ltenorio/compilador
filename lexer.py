"""
Analisador Léxico (Lexer)
"""

from tokens import Token, TokenType, PALAVRAS_RESERVADAS


class Lexer:
    """Analisador léxico que converte código fonte em tokens"""
    
    def __init__(self, codigo_fonte):
        self.codigo = codigo_fonte
        self.posicao = 0
        self.linha = 1
        self.coluna = 1
        self.char_atual = self.codigo[0] if codigo_fonte else None
        self.tokens = []
        self.erros = []
    
    def erro(self, mensagem):
        """Registra um erro léxico"""
        msg = f"Erro léxico na linha {self.linha}, coluna {self.coluna}: {mensagem}"
        self.erros.append(msg)
        return Token(TokenType.ERRO, '', self.linha, self.coluna)
    
    def avancar(self):
        """Avança para o próximo caractere"""
        if self.char_atual == '\n':
            self.linha += 1
            self.coluna = 1
        else:
            self.coluna += 1
        
        self.posicao += 1
        if self.posicao < len(self.codigo):
            self.char_atual = self.codigo[self.posicao]
        else:
            self.char_atual = None
    
    def proximo_char(self):
        """Retorna o próximo caractere sem avançar"""
        pos = self.posicao + 1
        if pos < len(self.codigo):
            return self.codigo[pos]
        return None
    
    def pular_espacos(self):
        """Pula espaços em branco, tabs, quebras de linha"""
        while self.char_atual and self.char_atual in ' \t\n\r':
            self.avancar()
    
    def pular_comentario(self):
        """Pula comentários entre { e }"""
        linha_inicio = self.linha
        self.avancar()  # pula '{'
        
        while self.char_atual and self.char_atual != '}':
            self.avancar()
        
        if self.char_atual == '}':
            self.avancar()  # pula '}'
        else:
            self.erro(f"Comentário não fechado (iniciado na linha {linha_inicio})")
    
    def ler_numero(self):
        """Lê um número inteiro"""
        linha_token = self.linha
        coluna_token = self.coluna
        numero = ''
        
        while self.char_atual and self.char_atual.isdigit():
            numero += self.char_atual
            self.avancar()
        
        return Token(TokenType.NUMERO, numero, linha_token, coluna_token)
    
    def ler_identificador(self):
        """Lê um identificador ou palavra reservada"""
        linha_token = self.linha
        coluna_token = self.coluna
        texto = ''
        
        # Primeiro caractere deve ser letra
        if self.char_atual and self.char_atual.isalpha():
            texto += self.char_atual
            self.avancar()
        
        # Próximos podem ser letras, dígitos ou underline
        while self.char_atual and (self.char_atual.isalnum() or self.char_atual == '_'):
            texto += self.char_atual
            self.avancar()
        
        # Verifica se é palavra reservada
        tipo = PALAVRAS_RESERVADAS.get(texto.lower(), TokenType.IDENTIFICADOR)
        
        return Token(tipo, texto, linha_token, coluna_token)
    
    def proximo_token(self):
        """Retorna o próximo token do código fonte"""
        while self.char_atual:
            # Pular espaços em branco
            if self.char_atual in ' \t\n\r':
                self.pular_espacos()
                continue
            
            # Pular comentários
            if self.char_atual == '{':
                self.pular_comentario()
                continue
            
            # Números
            if self.char_atual.isdigit():
                return self.ler_numero()
            
            # Identificadores e palavras reservadas
            if self.char_atual.isalpha():
                return self.ler_identificador()
            
            # Operadores e delimitadores de dois caracteres
            linha_token = self.linha
            coluna_token = self.coluna
            
            # :=
            if self.char_atual == ':':
                self.avancar()
                if self.char_atual == '=':
                    self.avancar()
                    return Token(TokenType.ATRIBUICAO, ':=', linha_token, coluna_token)
                return Token(TokenType.DOIS_PONTOS, ':', linha_token, coluna_token)
            
            # ==
            if self.char_atual == '=':
                self.avancar()
                if self.char_atual == '=':
                    self.avancar()
                    return Token(TokenType.IGUAL, '==', linha_token, coluna_token)
                return self.erro("Caractere '=' isolado não é válido. Use '==' para comparação ou ':=' para atribuição")
            
            # !=
            if self.char_atual == '!':
                self.avancar()
                if self.char_atual == '=':
                    self.avancar()
                    return Token(TokenType.DIFERENTE, '!=', linha_token, coluna_token)
                return self.erro("Caractere '!' deve ser seguido de '=' para formar '!='")
            
            # <= e <
            if self.char_atual == '<':
                self.avancar()
                if self.char_atual == '=':
                    self.avancar()
                    return Token(TokenType.MENOR_IGUAL, '<=', linha_token, coluna_token)
                return Token(TokenType.MENOR, '<', linha_token, coluna_token)
            
            # >= e >
            if self.char_atual == '>':
                self.avancar()
                if self.char_atual == '=':
                    self.avancar()
                    return Token(TokenType.MAIOR_IGUAL, '>=', linha_token, coluna_token)
                return Token(TokenType.MAIOR, '>', linha_token, coluna_token)
            
            # Operadores e delimitadores de um caractere
            char = self.char_atual
            self.avancar()
            
            if char == '+':
                return Token(TokenType.MAIS, '+', linha_token, coluna_token)
            elif char == '-':
                return Token(TokenType.MENOS, '-', linha_token, coluna_token)
            elif char == '*':
                return Token(TokenType.MULTIPLICACAO, '*', linha_token, coluna_token)
            elif char == ';':
                return Token(TokenType.PONTO_VIRGULA, ';', linha_token, coluna_token)
            elif char == ',':
                return Token(TokenType.VIRGULA, ',', linha_token, coluna_token)
            elif char == '.':
                return Token(TokenType.PONTO, '.', linha_token, coluna_token)
            elif char == '(':
                return Token(TokenType.ABRE_PAREN, '(', linha_token, coluna_token)
            elif char == ')':
                return Token(TokenType.FECHA_PAREN, ')', linha_token, coluna_token)
            elif char == '}':
                return self.erro("Caractere '}' sem '{' correspondente")
            else:
                return self.erro(f"Caractere inválido '{char}'")
        
        # Fim do arquivo
        return Token(TokenType.EOF, '', self.linha, self.coluna)
    
    def tokenizar(self):
        """Gera todos os tokens do código fonte"""
        self.tokens = []
        self.erros = []
        
        while True:
            token = self.proximo_token()
            self.tokens.append(token)
            
            if token.tipo == TokenType.EOF:
                break
        
        return self.tokens, self.erros
