"""
Analisador Sintático + Semântico (Parser)
"""

from typing import Optional, List, Tuple
from tokens import Token, TokenType
from semantic import TabelaSimbolos, EntradaSimbolo, TIPOS_NUMERICOS, TIPOS_ORDENADOS


_FIRST_EXPRESSAO = {
    TokenType.IDENTIFICADOR,
    TokenType.NUMERO,
    TokenType.NUMERO_FLOAT,
    TokenType.CHAR_LITERAL,
    TokenType.VERDADEIRO,
    TokenType.FALSO,
    TokenType.ABRE_PAREN,
    TokenType.NAO,
    TokenType.MENOS, 
}

class Parser:
    def __init__(self, tokens):
        """
        Inicializa o parser com a lista de tokens vinda do lexer
        Atributos:
            self.tokens           -> lista completa de tokens (imutável)
            self.posicao          -> índice do token atual
            self.token_atual      -> token sendo analisado agora (look-ahead de 1)
            self.erros            -> erros SINTÁTICOS acumulados
            self.erros_semanticos -> erros SEMÂNTICOS acumulados 
            self.tabela           -> tabela de símbolos com controle de escopo
        """
        self.tokens           = tokens
        self.posicao          = 0
        self.token_atual      = self.tokens[0] if tokens else None
        self.erros            = []
        self.erros_semanticos = []
        self.tabela           = TabelaSimbolos()

    def erro(self, mensagem: str):
        msg = f"Erro sintático na linha {self.token_atual.linha}: {mensagem}"
        self.erros.append(msg)

    def erro_semantico(self, mensagem: str):
        msg = f"Erro semântico na linha {self.token_atual.linha}: {mensagem}"
        self.erros_semanticos.append(msg)

    def avancar(self):
        if self.posicao < len(self.tokens) - 1:
            self.posicao    += 1
            self.token_atual = self.tokens[self.posicao]

    def esperar(self, tipo_esperado: TokenType) -> bool:
        """
        Verifica se o token atual é do tipo esperado e avança se sim
        toda vez que a gramática diz "aqui DEVE ter X", usa-se esperar(X).
        Retorna True e avança -> token correto
        Retorna False        -> token errado, registra erro sintático
        """
        if self.token_atual.tipo == tipo_esperado:
            self.avancar()
            return True
        self.erro(f"esperado '{tipo_esperado.name}', encontrado '{self.token_atual.tipo.name}'")
        return False

    def verificar(self, tipo: TokenType) -> bool:
        """
        Verifica se o token atual é do tipo especificado SEM avançar
        """
        return self.token_atual.tipo == tipo

    def programa(self) -> bool:
        """
        <programa> ::= programa <identificador> ; <bloco> .
        """
        if not self.esperar(TokenType.PROGRAMA):      return False
        if not self.esperar(TokenType.IDENTIFICADOR): return False
        if not self.esperar(TokenType.PONTO_VIRGULA): return False
        if not self.bloco():                          return False
        if not self.esperar(TokenType.PONTO):         return False
        return True

    def bloco(self) -> bool:
        """
        <bloco> ::= <declaracoes> <comandos>
        """
        if not self.declaracoes(): return False
        if not self.comandos():    return False
        return True

    def declaracoes(self) -> bool:
        """
        <declaracoes> ::= <declaracao> <declaracoes> | ε
        """
        while (self.verificar(TokenType.VAR) or
               self.verificar(TokenType.PROCEDIMENTO) or
               self.verificar(TokenType.FUNCAO)):
            if not self.declaracao():
                return False
        return True 

    def declaracao(self) -> bool:
        """
        <declaracao> ::= <declaracao_variavel> | <declaracao_subrotina>
        """
        if self.verificar(TokenType.VAR):
            return self.declaracao_variavel()
        elif self.verificar(TokenType.PROCEDIMENTO) or self.verificar(TokenType.FUNCAO):
            return self.declaracao_subrotina()
        self.erro("esperado 'VAR', 'PROCEDIMENTO' ou 'FUNCAO'")
        return False

    # ────────────────────────────────────────────────────────────

    def declaracao_variavel(self) -> bool:
        """
        <declaracao_variavel> ::= var <identificador> : <tipo> <inicializacao> ;
        """
        if not self.esperar(TokenType.VAR): return False

        nome  = self.token_atual.lexema   # guarda antes de avançar
        linha = self.token_atual.linha
        if not self.esperar(TokenType.IDENTIFICADOR): return False
        if not self.esperar(TokenType.DOIS_PONTOS):   return False

        tipo_var = self.tipo()            # retorna string do tipo ou None
        if tipo_var is None: return False

        # Verificação semântica 1: void não pode ser tipo de variável
        if tipo_var == 'void':
            self.erro_semantico(f"variável '{nome}' não pode ser do tipo 'void'")
            return False

        # Verificação semântica 2: sem duplicatas no escopo atual
        entrada = EntradaSimbolo(nome, tipo_var, 'variavel',
                                 self.tabela.escopo_atual, [], linha)
        if not self.tabela.declarar(nome, entrada):
            self.erro_semantico(
                f"variável '{nome}' já declarada no escopo '{self.tabela.escopo_atual}'")
            return False

        # Verificação semântica 3: tipo da inicialização (dentro de inicializacao())
        if not self.inicializacao(tipo_var): return False
        if not self.esperar(TokenType.PONTO_VIRGULA): return False
        return True

    def inicializacao(self, tipo_var: str) -> bool:
        """
        <inicializacao> ::= := <expressao> | ε
        """
        if self.verificar(TokenType.ATRIBUICAO):
            self.avancar()                    # consome ':='
            tipo_expr = self.expressao()      # avalia a expressão e obtém seu tipo
            if tipo_expr is None: return False
            if tipo_expr != tipo_var:         # tipagem forte: sem coerção implícita
                self.erro_semantico(
                    f"tipo incompatível na inicialização: "
                    f"variável é '{tipo_var}', expressão é '{tipo_expr}'")
                return False
        return True  # ε - sem inicialização também é válido

    def tipo(self) -> Optional[str]:
        """
        <tipo> ::= inteiro | booleano | char | float | void
        """
        mapa = {
            TokenType.INTEIRO:  'inteiro',
            TokenType.BOOLEANO: 'booleano',
            TokenType.CHAR:     'char',
            TokenType.FLOAT:    'float',
            TokenType.VOID:     'void',
        }
        if self.token_atual.tipo in mapa:
            nome_tipo = mapa[self.token_atual.tipo]
            self.avancar()
            return nome_tipo
        self.erro("esperado tipo: inteiro, booleano, char, float ou void")
        return None

    def declaracao_subrotina(self) -> bool:
        """
        <declaracao_subrotina> ::= <declaracao_procedimento> | <declaracao_funcao>
        """
        if self.verificar(TokenType.PROCEDIMENTO):
            return self.declaracao_procedimento()
        elif self.verificar(TokenType.FUNCAO):
            return self.declaracao_funcao()
        self.erro("esperado 'PROCEDIMENTO' ou 'FUNCAO'")
        return False

    def declaracao_procedimento(self) -> bool:
        """
        <declaracao_procedimento> ::= procedimento <identificador> ( <parametros> ) ; <bloco>
        """
        if not self.esperar(TokenType.PROCEDIMENTO): return False

        nome  = self.token_atual.lexema
        linha = self.token_atual.linha
        if not self.esperar(TokenType.IDENTIFICADOR): return False
        if not self.esperar(TokenType.ABRE_PAREN):    return False

        # Coleta parâmetros sem registrar na tabela ainda
        params_raw = self._coletar_parametros()   # [(tipo, nome, linha), ...]
        if params_raw is None: return False
        tipos_params = [p[0] for p in params_raw] # só os tipos, para EntradaSimbolo

        if not self.esperar(TokenType.FECHA_PAREN):   return False
        if not self.esperar(TokenType.PONTO_VIRGULA): return False

        # Registra o procedimento no escopo atual com tipo de retorno 'void'
        entrada = EntradaSimbolo(nome, 'void', 'procedimento',
                                 self.tabela.escopo_atual, tipos_params, linha)
        if not self.tabela.declarar(nome, entrada):
            self.erro_semantico(
                f"procedimento '{nome}' já declarado no escopo '{self.tabela.escopo_atual}'")
            return False

        # Abre escopo local do procedimento (sem tipo de retorno — é void)
        self.tabela.entrar_escopo(nome, tipo_retorno=None)

        # Registra cada parâmetro no escopo local
        for tipo_p, nome_p, linha_p in params_raw:
            e = EntradaSimbolo(nome_p, tipo_p, 'parametro', nome, [], linha_p)
            if not self.tabela.declarar(nome_p, e):
                self.erro_semantico(f"parâmetro '{nome_p}' duplicado em '{nome}'")
                self.tabela.sair_escopo()
                return False

        ok = self.bloco()            # processa o corpo
        self.tabela.sair_escopo()    # fecha o escopo ao terminar
        return ok

    def declaracao_funcao(self) -> bool:
        """
        <declaracao_funcao> ::= funcao <identificador> ( <parametros> ) : <tipo> ; <bloco_funcao>
        """
        if not self.esperar(TokenType.FUNCAO): return False

        nome  = self.token_atual.lexema
        linha = self.token_atual.linha
        if not self.esperar(TokenType.IDENTIFICADOR): return False
        if not self.esperar(TokenType.ABRE_PAREN):    return False

        params_raw = self._coletar_parametros()
        if params_raw is None: return False
        tipos_params = [p[0] for p in params_raw]

        if not self.esperar(TokenType.FECHA_PAREN): return False
        if not self.esperar(TokenType.DOIS_PONTOS): return False

        tipo_ret = self.tipo()          # tipo de retorno declarado (ex: 'inteiro')
        if tipo_ret is None: return False

        if not self.esperar(TokenType.PONTO_VIRGULA): return False

        # Registra a função no escopo atual com seu tipo de retorno real
        entrada = EntradaSimbolo(nome, tipo_ret, 'funcao',
                                 self.tabela.escopo_atual, tipos_params, linha)
        if not self.tabela.declarar(nome, entrada):
            self.erro_semantico(
                f"função '{nome}' já declarada no escopo '{self.tabela.escopo_atual}'")
            return False

        # Abre escopo local com tipo_retorno — bloco_funcao() vai consultar isso
        # para verificar se o 'retorna' tem o tipo correto
        self.tabela.entrar_escopo(nome, tipo_retorno=tipo_ret)

        for tipo_p, nome_p, linha_p in params_raw:
            e = EntradaSimbolo(nome_p, tipo_p, 'parametro', nome, [], linha_p)
            if not self.tabela.declarar(nome_p, e):
                self.erro_semantico(f"parâmetro '{nome_p}' duplicado em '{nome}'")
                self.tabela.sair_escopo()
                return False

        ok = self.bloco_funcao()     # corpo da função com retorna obrigatório
        self.tabela.sair_escopo()
        return ok

    def _coletar_parametros(self) -> Optional[List[Tuple[str, str, int]]]:
        params: List[Tuple[str, str, int]] = []

        # Primeiro parâmetro (obrigatório)
        tipo_p = self.tipo()
        if tipo_p is None: return None

        if tipo_p == 'void':
            self.erro_semantico("'void' não pode ser tipo de parâmetro")
            return None

        nome_p  = self.token_atual.lexema
        linha_p = self.token_atual.linha
        if not self.esperar(TokenType.IDENTIFICADOR): return None
        params.append((tipo_p, nome_p, linha_p))

        # Parâmetros adicionais separados por vírgula
        while self.verificar(TokenType.VIRGULA):
            self.avancar()    # consome ','
            tipo_p = self.tipo()
            if tipo_p is None: return None
            if tipo_p == 'void':
                self.erro_semantico("'void' não pode ser tipo de parâmetro")
                return None
            nome_p  = self.token_atual.lexema
            linha_p = self.token_atual.linha
            if not self.esperar(TokenType.IDENTIFICADOR): return None
            params.append((tipo_p, nome_p, linha_p))

        return params

    def bloco_funcao(self) -> bool:
        """
        <bloco_funcao> ::= <declaracoes> inicio <lista_comandos_funcao> retorna <expressao> ; fim
        """
        if not self.declaracoes(): return False
        if not self.esperar(TokenType.INICIO): return False

        # Comandos antes do 'retorna' são opcionais
        # Se o próximo token já for RETORNA, pula direto
        if not self.verificar(TokenType.RETORNA):
            if not self.lista_comandos_funcao(): return False

        if not self.esperar(TokenType.RETORNA): return False

        tipo_expr = self.expressao()   # avalia a expressão retornada
        if tipo_expr is None: return False

        # Verificação semântica: tipo do retorno deve bater com o declarado
        tipo_esperado = self.tabela.tipo_retorno_atual
        if tipo_esperado != 'void' and tipo_expr != tipo_esperado:
            self.erro_semantico(
                f"tipo de retorno incompatível: "
                f"função declara '{tipo_esperado}', expressão retorna '{tipo_expr}'")
            return False

        if not self.esperar(TokenType.PONTO_VIRGULA): return False
        if not self.esperar(TokenType.FIM):           return False
        return True

    def lista_comandos_funcao(self) -> bool:
        if not self.comando(): return False
        return self.lista_comandos_funcao_resto()

    def lista_comandos_funcao_resto(self) -> bool:
        while self.verificar(TokenType.PONTO_VIRGULA):
            self.avancar()
            if self.verificar(TokenType.RETORNA):
                break   # chegou no retorna — para sem consumir
            if not self.comando(): return False
        return True

    def comandos(self) -> bool:
        """
        <comandos> ::= inicio <lista_comandos> fim
        """
        if not self.esperar(TokenType.INICIO): return False
        if not self.lista_comandos():          return False
        if not self.esperar(TokenType.FIM):    return False
        return True

    def lista_comandos(self) -> bool:
        """
        <lista_comandos> ::= <comando> <lista_comandos_resto>
        """
        if not self.comando(): return False
        return self.lista_comandos_resto()

    def lista_comandos_resto(self) -> bool:
        """
        <lista_comandos_resto> ::= ; <comando> <lista_comandos_resto> | ; | ε
        """
        while self.verificar(TokenType.PONTO_VIRGULA):
            self.avancar()
            if self.verificar(TokenType.FIM):
                break 
            if not self.comando(): return False
        return True

    def comando(self) -> bool:
        """
        <comando> ::= <comando_identificador> | <comando_condicional>
                    | <comando_enquanto> | <comando_leitura> | <comando_escrita>
                    | <comando_desvio> | <comandos>

        FIRST de cada alternativa:
            IDENTIFICADOR -> atribuição ou chamada de procedimento
            SE            -> desvio condicional
            ENQUANTO      -> laço
            LEIA          -> leitura
            ESCREVA       -> escrita
            PARE/CONTINUE -> desvio incondicional
            INICIO        -> bloco aninhado de comandos
        """
        if self.verificar(TokenType.IDENTIFICADOR):
            return self.comando_identificador()
        elif self.verificar(TokenType.SE):
            return self.comando_condicional()
        elif self.verificar(TokenType.ENQUANTO):
            return self.comando_enquanto()
        elif self.verificar(TokenType.LEIA):
            return self.comando_leitura()
        elif self.verificar(TokenType.ESCREVA):
            return self.comando_escrita()
        elif self.verificar(TokenType.PARE) or self.verificar(TokenType.CONTINUE):
            return self.comando_desvio()
        elif self.verificar(TokenType.INICIO):
            return self.comandos()    # bloco aninhado: inicio / fim dentro de outro
        self.erro("comando inválido")
        return False


    def comando_identificador(self) -> bool:
        """
        <comando_identificador> ::= <identificador> <continuacao_identificador>
        """
        nome  = self.token_atual.lexema
        linha = self.token_atual.linha
        if not self.esperar(TokenType.IDENTIFICADOR): return False
        return self.continuacao_identificador(nome, linha)

    def continuacao_identificador(self, nome: str, linha: int) -> bool:
        """
        <continuacao_identificador> ::= := <expressao> | ( <argumentos> )
        """
        # ── Atribuição ────────────────────────────────────────────────────
        if self.verificar(TokenType.ATRIBUICAO):
            simbolo = self.tabela.buscar(nome)
            if simbolo is None:
                self.erro_semantico(f"variável '{nome}' não declarada (linha {linha})")
                return False
            if simbolo.categoria not in ('variavel', 'parametro'):
                self.erro_semantico(
                    f"'{nome}' é {simbolo.categoria}, não pode receber atribuição")
                return False
            self.avancar()                    # consome ':='
            tipo_expr = self.expressao()      # avalia o lado direito
            if tipo_expr is None: return False
            if tipo_expr != simbolo.tipo:     # tipagem forte: sem coerção
                self.erro_semantico(
                    f"atribuição incompatível: '{nome}' é '{simbolo.tipo}', "
                    f"expressão é '{tipo_expr}'")
                return False
            return True

        # ── Chamada de procedimento ───────────────────────────────────────
        elif self.verificar(TokenType.ABRE_PAREN):
            simbolo = self.tabela.buscar(nome)
            if simbolo is None:
                self.erro_semantico(f"'{nome}' não declarado (linha {linha})")
                return False
            # Funções retornam valor — não podem ser usadas como comando isolado
            if simbolo.categoria != 'procedimento':
                self.erro_semantico(
                    f"'{nome}' é {simbolo.categoria}, não um procedimento; "
                    f"chamadas de função só são válidas dentro de expressões")
                return False
            self.avancar()                    # consome '('
            tipos_args = self.argumentos()    # coleta tipos dos argumentos
            if tipos_args is None: return False
            if not self.esperar(TokenType.FECHA_PAREN): return False
            return self._verificar_argumentos(nome, simbolo, tipos_args)

        self.erro("esperado ':=' ou '('")
        return False

    # ── Desvio condicional ─────────────────────────────────────────────────

    def comando_condicional(self) -> bool:
        """
        <comando_condicional> ::= se <expressao> entao <comando> <parte_senao>
        """
        if not self.esperar(TokenType.SE): return False
        tipo_cond = self.expressao()
        if tipo_cond is None: return False
        # Tipagem forte: condição obrigatoriamente booleana
        if tipo_cond != 'booleano':
            self.erro_semantico(
                f"condição do 'se' deve ser 'booleano', encontrado '{tipo_cond}'")
            return False
        if not self.esperar(TokenType.ENTAO): return False
        if not self.comando(): return False
        return self.parte_senao()    # senao é opcional (ε)

    def parte_senao(self) -> bool:
        """
        <parte_senao> ::= senao <comando> | ε
        """
        if self.verificar(TokenType.SENAO):
            self.avancar()
            return self.comando()
        return True  # ε — sem senao é válido

    # ── Laço ───────────────────────────────────────────────────────────────

    def comando_enquanto(self) -> bool:
        """
        <comando_enquanto> ::= enquanto <expressao> faca <comando>
        """
        if not self.esperar(TokenType.ENQUANTO): return False
        tipo_cond = self.expressao()
        if tipo_cond is None: return False
        if tipo_cond != 'booleano':
            self.erro_semantico(
                f"condição do 'enquanto' deve ser 'booleano', encontrado '{tipo_cond}'")
            return False
        if not self.esperar(TokenType.FACA): return False
        return self.comando()    # corpo do laço (pode ser um bloco inicio...fim)

    # ── Entrada/saída ──────────────────────────────────────────────────────

    def comando_leitura(self) -> bool:
        """
        <comando_leitura> ::= leia ( <identificador> )
        """
        if not self.esperar(TokenType.LEIA):       return False
        if not self.esperar(TokenType.ABRE_PAREN): return False
        nome  = self.token_atual.lexema
        linha = self.token_atual.linha
        if not self.esperar(TokenType.IDENTIFICADOR): return False
        simbolo = self.tabela.buscar(nome)
        if simbolo is None:
            self.erro_semantico(f"variável '{nome}' não declarada (linha {linha})")
            return False
        if simbolo.categoria not in ('variavel', 'parametro'):
            self.erro_semantico(
                f"'leia' requer uma variável, '{nome}' é {simbolo.categoria}")
            return False
        return self.esperar(TokenType.FECHA_PAREN)

    def comando_escrita(self) -> bool:
        """
        <comando_escrita> ::= escreva ( <expressao> )
        """
        if not self.esperar(TokenType.ESCREVA):    return False
        if not self.esperar(TokenType.ABRE_PAREN): return False
        tipo_expr = self.expressao()
        if tipo_expr is None: return False
        if tipo_expr == 'void':
            self.erro_semantico("'escreva' não pode imprimir expressão do tipo 'void'")
            return False
        return self.esperar(TokenType.FECHA_PAREN)

    def comando_desvio(self) -> bool:
        """
        <comando_desvio> ::= pare | continue
        """
        if self.verificar(TokenType.PARE) or self.verificar(TokenType.CONTINUE):
            self.avancar()
            return True
        self.erro("esperado 'PARE' ou 'CONTINUE'")
        return False

    def argumentos(self) -> Optional[List[str]]:
        """
        <argumentos> ::= <expressao> <argumentos_resto> | ε
        """
        if self.token_atual.tipo not in _FIRST_EXPRESSAO:
            return []   # ε — sem argumentos

        tipo = self.expressao()
        if tipo is None: return None
        tipos = [tipo]

        # Argumentos adicionais separados por vírgula
        while self.verificar(TokenType.VIRGULA):
            self.avancar()
            tipo = self.expressao()
            if tipo is None: return None
            tipos.append(tipo)

        return tipos

    def _verificar_argumentos(self, nome: str, simbolo, tipos_args: List[str]) -> bool:
        """
        Verifica se os argumentos passados correspondem aos parâmetros declarados
        """
        n_params = len(simbolo.parametros)
        n_args   = len(tipos_args)
        if n_args != n_params:
            self.erro_semantico(
                f"{simbolo.categoria} '{nome}' espera {n_params} argumento(s), recebeu {n_args}")
            return False
        # Verifica tipo de cada argumento na ordem (zip para iterar em paralelo)
        for i, (arg_tipo, param_tipo) in enumerate(zip(tipos_args, simbolo.parametros)):
            if arg_tipo != param_tipo:
                self.erro_semantico(
                    f"argumento {i+1} de '{nome}': "
                    f"esperado '{param_tipo}', recebido '{arg_tipo}'")
                return False
        return True

    def expressao(self) -> Optional[str]:
        return self.expressao_ou()

    # ── Nível 1 ───────────────────────────────────

    def expressao_ou(self) -> Optional[str]:
        """
        <expressao_ou> ::= <expressao_e> <expressao_ou_resto>
        Avalia o lado esquerdo e passa para _ou_resto com o tipo resultante.
        """
        tipo = self.expressao_e()
        if tipo is None: return None
        return self._ou_resto(tipo)

    def _ou_resto(self, tipo_esq: str) -> Optional[str]:
        """
        <expressao_ou_resto> ::= ou <expressao_e> <expressao_ou_resto> | ε

        Verificação semântica: 'ou' só funciona com booleanos.
        'verdadeiro ou falso'  -> OK  (booleano ou booleano = booleano)
        '1 ou 2'               -> ERRO
        'x ou verdadeiro'      -> ERRO se x não for booleano
        """
        while self.verificar(TokenType.OU):
            self.avancar()
            tipo_dir = self.expressao_e()
            if tipo_dir is None: return None
            if tipo_esq != 'booleano' or tipo_dir != 'booleano':
                self.erro_semantico(
                    f"operador 'ou' requer operandos 'booleano', "
                    f"encontrado '{tipo_esq}' e '{tipo_dir}'")
                return None
            tipo_esq = 'booleano'   # resultado de 'ou' é sempre booleano
        return tipo_esq

    # ── Nível 2 ────────────────────────────────────────────────────────

    def expressao_e(self) -> Optional[str]:
        tipo = self.expressao_relacional()
        if tipo is None: return None
        return self._e_resto(tipo)

    def _e_resto(self, tipo_esq: str) -> Optional[str]:
        """
        'e' só funciona com booleanos, igual ao 'ou'.
        'verdadeiro e falso' -> OK
        '1 e 2'              -> ERRO
        """
        while self.verificar(TokenType.E):
            self.avancar()
            tipo_dir = self.expressao_relacional()
            if tipo_dir is None: return None
            if tipo_esq != 'booleano' or tipo_dir != 'booleano':
                self.erro_semantico(
                    f"operador 'e' requer operandos 'booleano', "
                    f"encontrado '{tipo_esq}' e '{tipo_dir}'")
                return None
            tipo_esq = 'booleano'
        return tipo_esq

    # ── Nível 3 ───────────────────────────────────────────────

    def expressao_relacional(self) -> Optional[str]:
        tipo = self.expressao_aritmetica()
        if tipo is None: return None
        return self._relacional_resto(tipo)

    def _relacional_resto(self, tipo_esq: str) -> Optional[str]:
        """
        <op_relacional> ::= == | != | < | <= | > | >=
        """
        ops_ordem  = {TokenType.MENOR, TokenType.MENOR_IGUAL,
                      TokenType.MAIOR, TokenType.MAIOR_IGUAL}
        ops_iguald = {TokenType.IGUAL, TokenType.DIFERENTE}

        op_token = self.token_atual.tipo
        if op_token not in ops_ordem | ops_iguald:
            return tipo_esq   # ε — sem operador relacional, retorna tipo atual

        self.avancar()   # consome o operador relacional
        tipo_dir = self.expressao_aritmetica()
        if tipo_dir is None: return None

        if op_token in ops_ordem:
            if tipo_esq not in TIPOS_ORDENADOS or tipo_dir not in TIPOS_ORDENADOS:
                self.erro_semantico(
                    f"operador relacional de ordem requer tipos ordenáveis "
                    f"(inteiro, float, char), encontrado '{tipo_esq}' e '{tipo_dir}'")
                return None
            if tipo_esq != tipo_dir:
                self.erro_semantico(
                    f"operador relacional requer operandos do mesmo tipo, "
                    f"encontrado '{tipo_esq}' e '{tipo_dir}'")
                return None
        else:
            if tipo_esq != tipo_dir:
                self.erro_semantico(
                    f"operador '==' / '!=' requer operandos do mesmo tipo, "
                    f"encontrado '{tipo_esq}' e '{tipo_dir}'")
                return None

        return 'booleano'   # resultado de toda comparação é booleano

    # ── Nível 4 ───────────────────────────────────────────

    def expressao_aritmetica(self) -> Optional[str]:
        tipo = self.termo()
        if tipo is None: return None
        return self._aritmetica_resto(tipo)

    def _aritmetica_resto(self, tipo_esq: str) -> Optional[str]:

        while self.verificar(TokenType.MAIS) or self.verificar(TokenType.MENOS):
            op = self.token_atual.lexema
            self.avancar()
            tipo_dir = self.termo()
            if tipo_dir is None: return None
            if tipo_esq not in TIPOS_NUMERICOS:
                self.erro_semantico(
                    f"operador '{op}' requer tipos numéricos, encontrado '{tipo_esq}'")
                return None
            if tipo_esq != tipo_dir:
                self.erro_semantico(
                    f"operador '{op}' requer operandos do mesmo tipo numérico, "
                    f"encontrado '{tipo_esq}' e '{tipo_dir}'")
                return None
        return tipo_esq

    # ── Nível 5 ──────────────────────────────────

    def termo(self) -> Optional[str]:
        tipo = self.fator()
        if tipo is None: return None
        return self._termo_resto(tipo)

    def _termo_resto(self, tipo_esq: str) -> Optional[str]:
        while self.verificar(TokenType.MULTIPLICACAO) or self.verificar(TokenType.DIV):
            is_div = self.verificar(TokenType.DIV)
            op     = self.token_atual.lexema
            self.avancar()
            tipo_dir = self.fator()
            if tipo_dir is None: return None

            if is_div:
                # div é divisão inteira — ambos DEVEM ser inteiro
                if tipo_esq != 'inteiro' or tipo_dir != 'inteiro':
                    self.erro_semantico(
                        f"operador 'div' requer operandos 'inteiro', "
                        f"encontrado '{tipo_esq}' e '{tipo_dir}'")
                    return None
            else:
                if tipo_esq not in TIPOS_NUMERICOS:
                    self.erro_semantico(
                        f"operador '*' requer tipos numéricos, encontrado '{tipo_esq}'")
                    return None
                if tipo_esq != tipo_dir:
                    self.erro_semantico(
                        f"operador '*' requer operandos do mesmo tipo numérico, "
                        f"encontrado '{tipo_esq}' e '{tipo_dir}'")
                    return None
        return tipo_esq

    # ── Nível 6 ──────────────────────────────

    def fator(self) -> Optional[str]:
        """
        <fator> ::= <identificador> <fator_resto>
        """
        if self.verificar(TokenType.IDENTIFICADOR):
            nome  = self.token_atual.lexema
            linha = self.token_atual.linha
            self.avancar()
            return self.fator_resto(nome, linha)   # variável ou chamada de função

        elif self.verificar(TokenType.NUMERO):
            self.avancar()
            return 'inteiro'

        elif self.verificar(TokenType.NUMERO_FLOAT):
            self.avancar()
            return 'float'

        elif self.verificar(TokenType.CHAR_LITERAL):
            self.avancar()
            return 'char'

        elif self.verificar(TokenType.VERDADEIRO) or self.verificar(TokenType.FALSO):
            self.avancar()
            return 'booleano'

        elif self.verificar(TokenType.ABRE_PAREN):
            self.avancar()              # consome '('
            tipo = self.expressao()     # avalia a sub-expressão
            if tipo is None: return None
            if not self.esperar(TokenType.FECHA_PAREN): return None
            return tipo                 # tipo da expressão entre parênteses

        elif self.verificar(TokenType.NAO):
            self.avancar()              # consome 'nao'
            tipo = self.fator()         # recursão: nao (nao x) é válido
            if tipo is None: return None
            if tipo != 'booleano':
                self.erro_semantico(
                    f"operador 'nao' requer operando 'booleano', encontrado '{tipo}'")
                return None
            return 'booleano'

        self.erro("esperado identificador, número, literal, '(' ou 'nao'")
        return None

    def fator_resto(self, nome: str, linha: int) -> Optional[str]:
        """
        <fator_resto> ::= ( <argumentos> ) | ε
        """
        if self.verificar(TokenType.ABRE_PAREN):
            # Chamada de função dentro de expressão
            self.avancar()   # consome '('
            simbolo = self.tabela.buscar(nome)
            if simbolo is None:
                self.erro_semantico(f"'{nome}' não declarado (linha {linha})")
                return None
            if simbolo.categoria != 'funcao':
                self.erro_semantico(
                    f"'{nome}' é {simbolo.categoria}, não uma função; "
                    f"apenas funções podem ser chamadas dentro de expressões")
                return None
            tipos_args = self.argumentos()
            if tipos_args is None: return None
            if not self.esperar(TokenType.FECHA_PAREN): return None
            if not self._verificar_argumentos(nome, simbolo, tipos_args):
                return None
            return simbolo.tipo   # tipo de retorno da função

        else:
            # Referência a variável ou parâmetro 
            simbolo = self.tabela.buscar(nome)
            if simbolo is None:
                self.erro_semantico(f"'{nome}' não declarado (linha {linha})")
                return None
            if simbolo.categoria in ('funcao', 'procedimento'):
                self.erro_semantico(
                    f"'{nome}' é {simbolo.categoria}; "
                    f"use '{nome}(...)' para chamá-lo")
                return None
            return simbolo.tipo   # tipo da variável/parâmetro na tabela

    def analisar(self):
        sucesso = self.programa()

        # Verifica código extra após o fim do programa
        if sucesso and not self.verificar(TokenType.EOF):
            self.erro("código encontrado após o fim do programa")
            sucesso = False

        # Sucesso real = sem erros sintáticos E sem erros semânticos
        tem_erros = bool(self.erros) or bool(self.erros_semanticos)
        return not tem_erros, self.erros, self.erros_semanticos