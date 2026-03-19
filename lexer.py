"""
Analisador Léxico (Lexer)
"""

from tokens import Token, TokenType, PALAVRAS_RESERVADAS

class Lexer:
    """
    analisador léxico que converte código fonte em tokens
    """

    def __init__(self, codigo_fonte):
        """
        Inicializa o lexer com o código fonte completo
        Atributos:
            self.codigo     → o texto fonte completo (imutável durante a execução)
            self.posicao    → índice do caractere atual na string
            self.linha      → linha atual (começa em 1, para mensagens de erro)
            self.coluna     → coluna atual (começa em 1, para mensagens de erro)
            self.char_atual → o caractere na posição atual (None = fim do arquivo)
            self.tokens     → lista de tokens produzidos (preenchida por tokenizar())
            self.erros      → lista de mensagens de erro léxico encontradas
        """
        self.codigo     = codigo_fonte
        self.posicao    = 0
        self.linha      = 1
        self.coluna     = 1
        self.char_atual = self.codigo[0] if codigo_fonte else None
        self.tokens     = []
        self.erros      = []

    def erro(self, mensagem):
        """
        Registra um erro léxico e retorna um token de erro
        """
        msg = f"Erro léxico na linha {self.linha}, coluna {self.coluna}: {mensagem}"
        self.erros.append(msg)
        # Retorna token de erro para que proximo_token() possa retorná-lo normalmente
        return Token(TokenType.ERRO, '', self.linha, self.coluna)

    def avancar(self):
        """
        Avança o ponteiro para o próximo caractere, atualizando linha e coluna
        """
        if self.char_atual == '\n':
            self.linha  += 1   # cruzou linha: incrementa contador
            self.coluna  = 1   # e reseta a coluna
        else:
            self.coluna += 1   # mesmo linha: só avança coluna
        self.posicao += 1
        # Se ainda há caracteres, atualiza; senão, sinaliza fim com None
        self.char_atual = self.codigo[self.posicao] if self.posicao < len(self.codigo) else None

    def proximo_char(self):
        """
        Retorna o próximo caracter SEM avançar o ponteiro 
        """
        pos = self.posicao + 1
        return self.codigo[pos] if pos < len(self.codigo) else None

    def pular_espacos(self):
        """
        Avança enquanto o caracter atual for espaco, tab, newline
        Espaços não tem significado sintático nessa linguagem — 'var x' e 'var   x' são equivalentes
        """
        while self.char_atual and self.char_atual in ' \t\n\r':
            self.avancar()

    def pular_comentario(self):
        linha_inicio = self.linha       # guarda onde o comentário começou
        self.avancar()                  # consome o '{' de abertura

        # Avança até fechar o comentário ou chegar no fim do arquivo
        while self.char_atual and self.char_atual != '}':
            self.avancar()

        if self.char_atual == '}':
            self.avancar()              # consome o '}' de fechamento 
        else:
            # char_atual é None → chegou no EOF sem fechar o comentário
            msg = (f"Erro léxico na linha {self.linha}, coluna {self.coluna}: "
                   f"Comentário não fechado (iniciado na linha {linha_inicio})")
            self.erros.append(msg)

    def ler_numero(self):
        linha_token  = self.linha
        coluna_token = self.coluna
        numero = ''

        # Fase 1: lê a parte inteira
        while self.char_atual and self.char_atual.isdigit():
            numero += self.char_atual
            self.avancar()

        # Fase 2: verifica se é float
        # proximo_char() aqui é o único look-ahead de 2 posições do lexer inteiro
        if self.char_atual == '.' and self.proximo_char() and self.proximo_char().isdigit():
            numero += self.char_atual   # adiciona o ponto decimal
            self.avancar()              # consome o '.'
            # Lê a parte fracionária
            while self.char_atual and self.char_atual.isdigit():
                numero += self.char_atual
                self.avancar()
            return Token(TokenType.NUMERO_FLOAT, numero, linha_token, coluna_token)
        # Não é float: retorna como inteiro
        return Token(TokenType.NUMERO, numero, linha_token, coluna_token)

    def ler_char_literal(self):
        linha_token  = self.linha
        coluna_token = self.coluna
        self.avancar()  # consome a aspa de abertura '

        # Erro: chegou no fim do arquivo ou nova linha sem fechar
        if self.char_atual is None or self.char_atual == '\n':
            return self.erro("literal char não fechado")

        # Erro: literal vazio ''
        if self.char_atual == '\'':
            return self.erro("literal char vazio ''")

        # Lê o único caractere válido
        ch = self.char_atual
        self.avancar()  # consome o caractere

        # Verifica se o próximo é a aspa de fechamento
        if self.char_atual != '\'':
            # Mais de um caractere: tenta recuperar consumindo até fechar ou nova linha
            while self.char_atual and self.char_atual not in ('\'', '\n'):
                self.avancar()
            if self.char_atual == '\'':
                self.avancar()  # consome a aspa de fechamento para recuperação
            return self.erro("literal char deve conter exatamente um caractere")

        self.avancar()  # consome a aspa de fechamento 
        return Token(TokenType.CHAR_LITERAL, ch, linha_token, coluna_token)

    def ler_identificador(self):
        linha_token  = self.linha
        coluna_token = self.coluna
        texto = ''

        # Primeiro caractere (já verificado como letra pelo chamador)
        texto += self.char_atual
        self.avancar()

        # Caracteres seguintes: letra, dígito ou underscore
        while self.char_atual and (self.char_atual.isalnum() or self.char_atual == '_'):
            texto += self.char_atual
            self.avancar()

        # Consulta o dicionário com .lower() → case-insensitive
        # Se não encontrar, default é identificador 
        tipo = PALAVRAS_RESERVADAS.get(texto.lower(), TokenType.IDENTIFICADOR)
        return Token(tipo, texto, linha_token, coluna_token)


    def proximo_token(self):
        while self.char_atual:

            # espaços em branco
            # não produzem token, apenas avançam o ponteiro
            if self.char_atual in ' \t\n\r':
                self.pular_espacos()
                continue    # volta ao topo do loop para verificar o próximo char

            # comentarios
            # '{' inicia comentário — tudo até '}' é descartado
            if self.char_atual == '{':
                self.pular_comentario()
                continue    # volta ao loop; o comentário não vira token

            # literais numéricos 
            # Qualquer dígito inicia um número (inteiro ou float)
            if self.char_atual.isdigit():
                return self.ler_numero()

            # literal char
            # Aspa simples inicia um literal de caractere: 'a'
            if self.char_atual == '\'':
                return self.ler_char_literal()

            # identificadores e palavras reservadas
            # letra ou underscore -> pode ser 'var', 'inicio', 'x', 'somar', etc
            if self.char_atual.isalpha() or self.char_atual == '_':
                return self.ler_identificador()

            # operadores de dois (ou um) caracteres
            # Guardamos linha/coluna ANTES de avançar, pois o token começa aqui
            linha_token  = self.linha
            coluna_token = self.coluna

            # ':' pode ser ':' (DOIS_PONTOS) ou ':=' (ATRIBUICAO)
            # Estratégia: avança, aí verifica char_atual (sem proximo_char)
            if self.char_atual == ':':
                self.avancar()          # consome ':'
                if self.char_atual == '=':
                    self.avancar()      # consome '=' → é ':='
                    return Token(TokenType.ATRIBUICAO, ':=', linha_token, coluna_token)
                # Próximo não é '=' -> é só ':'
                return Token(TokenType.DOIS_PONTOS, ':', linha_token, coluna_token)

            # '=' isolado é inválido nessa linguagem
            # Comparação usa '==' e atribuição usa ':='
            if self.char_atual == '=':
                self.avancar()
                if self.char_atual == '=':
                    self.avancar()
                    return Token(TokenType.IGUAL, '==', linha_token, coluna_token)
                return self.erro("'=' isolado é inválido; use '==' para comparação ou ':=' para atribuição")

            # '!' só é válido como parte de '!=' (diferente)
            if self.char_atual == '!':
                self.avancar()
                if self.char_atual == '=':
                    self.avancar()
                    return Token(TokenType.DIFERENTE, '!=', linha_token, coluna_token)
                return self.erro("'!' deve ser seguido de '=' para formar '!='")

            # '<' pode ser '<' (MENOR) ou '<=' (MENOR_IGUAL)
            if self.char_atual == '<':
                self.avancar()
                if self.char_atual == '=':
                    self.avancar()
                    return Token(TokenType.MENOR_IGUAL, '<=', linha_token, coluna_token)
                return Token(TokenType.MENOR, '<', linha_token, coluna_token)

            # '>' pode ser '>' (MAIOR) ou '>=' (MAIOR_IGUAL)
            if self.char_atual == '>':
                self.avancar()
                if self.char_atual == '=':
                    self.avancar()
                    return Token(TokenType.MAIOR_IGUAL, '>=', linha_token, coluna_token)
                return Token(TokenType.MAIOR, '>', linha_token, coluna_token)

            # operadores e delimitadores de um único caractere
            # Consome o caractere e usa um dicionário para mapear ao TokenType
            char = self.char_atual
            self.avancar()  # consome antes de verificar (já guardamos linha/coluna)

            mapa = {
                '+': TokenType.MAIS,            # operador de adição
                '-': TokenType.MENOS,           # operador de subtração
                '*': TokenType.MULTIPLICACAO,   # operador de multiplicação
                ';': TokenType.PONTO_VIRGULA,   # separador de comandos
                ',': TokenType.VIRGULA,         # separador de parâmetros/argumentos
                '.': TokenType.PONTO,           # fim do programa
                '(': TokenType.ABRE_PAREN,      # abertura de parêntese
                ')': TokenType.FECHA_PAREN,     # fechamento de parêntese
            }
            if char in mapa:
                return Token(mapa[char], char, linha_token, coluna_token)

            #Erros
            # '}' sem '{' correspondente (comentário nunca aberto)
            if char == '}':
                return self.erro("'}' sem '{' correspondente")

            # Qualquer outro caractere não reconhecido pela linguagem
            return self.erro(f"caractere inválido '{char}'")

        #Fim do arquivo
        # EOF sinaliza ao parser que o programa terminou
        return Token(TokenType.EOF, '', self.linha, self.coluna)

    def tokenizar(self):
        self.tokens = []
        self.erros  = []

        while True:
            token = self.proximo_token()
            self.tokens.append(token)
            if token.tipo == TokenType.EOF:
                break  
        return self.tokens, self.erros