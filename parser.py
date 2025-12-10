"""
Analisador Sintático (Parser)
Análise preditiva top-down usando funções recursivas
"""

from tokens import Token, TokenType


class Parser:
    """Analisador sintático que verifica a estrutura do programa"""
    
    def __init__(self, tokens):
        self.tokens = tokens
        self.posicao = 0
        self.token_atual = self.tokens[0] if tokens else None
        self.erros = []
    
    def erro(self, mensagem):
        """Registra um erro sintático"""
        msg = f"Erro sintático na linha {self.token_atual.linha}: {mensagem}"
        self.erros.append(msg)
    
    def avancar(self):
        """Avança para o próximo token"""
        if self.posicao < len(self.tokens) - 1:
            self.posicao += 1
            self.token_atual = self.tokens[self.posicao]
    
    def esperar(self, tipo_esperado):
        """Verifica se o token atual é do tipo esperado e avança"""
        if self.token_atual.tipo == tipo_esperado:
            self.avancar()
            return True
        else:
            self.erro(f"esperado '{tipo_esperado.name}', encontrado '{self.token_atual.tipo.name}'")
            return False
    
    def verificar(self, tipo):
        """Verifica se o token atual é do tipo especificado sem avançar"""
        return self.token_atual.tipo == tipo
    
    
    # ESTRUTURA PRINCIPAL
    def programa(self):
        """<programa> ::= programa <identificador> ; <bloco> ."""
        if not self.esperar(TokenType.PROGRAMA):
            return False
        
        if not self.esperar(TokenType.IDENTIFICADOR):
            return False
        
        if not self.esperar(TokenType.PONTO_VIRGULA):
            return False
        
        if not self.bloco():
            return False
        
        if not self.esperar(TokenType.PONTO):
            return False
        
        return True
    
    def bloco(self):
        """<bloco> ::= <declaracoes> <comandos>"""
        if not self.declaracoes():
            return False
        
        if not self.comandos():
            return False
        
        return True
    

    # DECLARAÇÕES
    def declaracoes(self):
        """<declaracoes> ::= <declaracao> <declaracoes> | ε"""
        # FIRST(declaracao) = {var, procedimento, funcao}
        while self.verificar(TokenType.VAR) or \
              self.verificar(TokenType.PROCEDIMENTO) or \
              self.verificar(TokenType.FUNCAO):
            if not self.declaracao():
                return False
        
        return True
    
    def declaracao(self):
        """<declaracao> ::= <declaracao_variavel> | <declaracao_subrotina>"""
        if self.verificar(TokenType.VAR):
            return self.declaracao_variavel()
        elif self.verificar(TokenType.PROCEDIMENTO) or self.verificar(TokenType.FUNCAO):
            return self.declaracao_subrotina()
        else:
            self.erro(f"esperado 'VAR', 'PROCEDIMENTO' ou 'FUNCAO'")
            return False
    
    def declaracao_variavel(self):
        """<declaracao_variavel> ::= var <identificador> : <tipo> <inicializacao> ;"""
        if not self.esperar(TokenType.VAR):
            return False
        
        if not self.esperar(TokenType.IDENTIFICADOR):
            return False
        
        if not self.esperar(TokenType.DOIS_PONTOS):
            return False
        
        if not self.tipo():
            return False
        
        if not self.inicializacao():
            return False
        
        if not self.esperar(TokenType.PONTO_VIRGULA):
            return False
        
        return True
    
    def inicializacao(self):
        """<inicializacao> ::= := <expressao> | ε"""
        if self.verificar(TokenType.ATRIBUICAO):
            self.avancar()
            return self.expressao()
        
        # ε (produção vazia)
        return True
    
    def tipo(self):
        """<tipo> ::= inteiro | booleano"""
        if self.verificar(TokenType.INTEIRO) or self.verificar(TokenType.BOOLEANO):
            self.avancar()
            return True
        else:
            self.erro(f"esperado 'INTEIRO' ou 'BOOLEANO'")
            return False
    
    
    # SUBROTINAS
    def declaracao_subrotina(self):
        """<declaracao_subrotina> ::= <declaracao_procedimento> | <declaracao_funcao>"""
        if self.verificar(TokenType.PROCEDIMENTO):
            return self.declaracao_procedimento()
        elif self.verificar(TokenType.FUNCAO):
            return self.declaracao_funcao()
        else:
            self.erro(f"esperado 'PROCEDIMENTO' ou 'FUNCAO'")
            return False
    
    def declaracao_procedimento(self):
        """<declaracao_procedimento> ::= procedimento <identificador> ( <parametros> ) ; <bloco>"""
        if not self.esperar(TokenType.PROCEDIMENTO):
            return False
        
        if not self.esperar(TokenType.IDENTIFICADOR):
            return False
        
        if not self.esperar(TokenType.ABRE_PAREN):
            return False
        
        if not self.parametros():
            return False
        
        if not self.esperar(TokenType.FECHA_PAREN):
            return False
        
        if not self.esperar(TokenType.PONTO_VIRGULA):
            return False
        
        if not self.bloco():
            return False
        
        return True
    
    def declaracao_funcao(self):
        """<declaracao_funcao> ::= funcao <identificador> ( <parametros> ) : <tipo> ; <bloco_funcao>
           <bloco_funcao> ::= <declaracoes> inicio <lista_comandos> retorna <expressao> ; fim"""
        if not self.esperar(TokenType.FUNCAO):
            return False
        
        if not self.esperar(TokenType.IDENTIFICADOR):
            return False
        
        if not self.esperar(TokenType.ABRE_PAREN):
            return False
        
        if not self.parametros():
            return False
        
        if not self.esperar(TokenType.FECHA_PAREN):
            return False
        
        if not self.esperar(TokenType.DOIS_PONTOS):
            return False
        
        if not self.tipo():
            return False
        
        if not self.esperar(TokenType.PONTO_VIRGULA):
            return False
        
        # Bloco da função: declarações + comandos com retorna
        if not self.bloco_funcao():
            return False
        
        return True
    
    def bloco_funcao(self):
        """<bloco_funcao> ::= <declaracoes> inicio <lista_comandos_opcional> retorna <expressao> ; fim"""
        # Declarações locais
        if not self.declaracoes():
            return False
        
        if not self.esperar(TokenType.INICIO):
            return False
        
        # Lista de comandos é opcional antes do retorna
        if not self.verificar(TokenType.RETORNA):
            if not self.lista_comandos_funcao():
                return False
        
        if not self.esperar(TokenType.RETORNA):
            return False
        
        if not self.expressao():
            return False
        
        if not self.esperar(TokenType.PONTO_VIRGULA):
            return False
        
        if not self.esperar(TokenType.FIM):
            return False
        
        return True
    
    def lista_comandos_funcao(self):
        """<lista_comandos_funcao> ::= <comando> <lista_comandos_funcao_resto>"""
        if not self.comando():
            return False
        
        return self.lista_comandos_funcao_resto()
    
    def lista_comandos_funcao_resto(self):
        """<lista_comandos_funcao_resto> ::= ; <comando> <lista_comandos_funcao_resto> | ε
           Para quando encontra RETORNA"""
        while self.verificar(TokenType.PONTO_VIRGULA):
            self.avancar()
            
            # Verifica se não é retorna (fim dos comandos da função)
            if self.verificar(TokenType.RETORNA):
                break
            
            if not self.comando():
                return False
        
        return True
    
    def parametros(self):
        """<parametros> ::= <tipo> <identificador> <parametros_resto>"""
        # Parâmetros são obrigatórios nas funções
        if not self.tipo():
            return False
        
        if not self.esperar(TokenType.IDENTIFICADOR):
            return False
        
        return self.parametros_resto()
    
    def parametros_resto(self):
        """<parametros_resto> ::= , <tipo> <identificador> <parametros_resto> | ε"""
        while self.verificar(TokenType.VIRGULA):
            self.avancar()
            
            if not self.tipo():
                return False
            
            if not self.esperar(TokenType.IDENTIFICADOR):
                return False
        
        return True
    

    # COMANDOS
    def comandos(self):
        """<comandos> ::= inicio <lista_comandos> fim"""
        if not self.esperar(TokenType.INICIO):
            return False
        
        if not self.lista_comandos():
            return False
        
        if not self.esperar(TokenType.FIM):
            return False
        
        return True
    
    def lista_comandos(self):
        """<lista_comandos> ::= <comando> <lista_comandos_resto>"""
        if not self.comando():
            return False
        
        return self.lista_comandos_resto()
    
    def lista_comandos_resto(self):
        """<lista_comandos_resto> ::= ; <comando> <lista_comandos_resto> | ε"""
        while self.verificar(TokenType.PONTO_VIRGULA):
            self.avancar()
            
            # Verifica se não é fim do bloco
            if self.verificar(TokenType.FIM):
                break
            
            if not self.comando():
                return False
        
        return True
    
    def comando(self):
        """<comando> ::= <comando_identificador> | <comando_condicional> | 
                        <comando_enquanto> | <comando_leitura> | 
                        <comando_escrita> | <comando_desvio> | <comandos>"""
        
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
            return self.comandos()
        else:
            self.erro(f"comando inválido")
            return False
    
    def comando_identificador(self):
        """<comando_identificador> ::= <identificador> <continuacao_identificador>"""
        if not self.esperar(TokenType.IDENTIFICADOR):
            return False
        
        return self.continuacao_identificador()
    
    def continuacao_identificador(self):
        """<continuacao_identificador> ::= := <expressao> | ( <argumentos> )"""
        if self.verificar(TokenType.ATRIBUICAO):
            self.avancar()
            return self.expressao()
        elif self.verificar(TokenType.ABRE_PAREN):
            self.avancar()
            if not self.argumentos():
                return False
            return self.esperar(TokenType.FECHA_PAREN)
        else:
            self.erro(f"esperado ':=' ou '('")
            return False
    
    def argumentos(self):
        """<argumentos> ::= <expressao> <argumentos_resto> | ε"""
        # FIRST(expressao) inclui identificador, numero, verdadeiro, falso, (, nao
        if self.verificar(TokenType.IDENTIFICADOR) or \
           self.verificar(TokenType.NUMERO) or \
           self.verificar(TokenType.VERDADEIRO) or \
           self.verificar(TokenType.FALSO) or \
           self.verificar(TokenType.ABRE_PAREN) or \
           self.verificar(TokenType.NAO):
            
            if not self.expressao():
                return False
            
            return self.argumentos_resto()
        
        # ε (produção vazia - sem argumentos)
        return True
    
    def argumentos_resto(self):
        """<argumentos_resto> ::= , <expressao> <argumentos_resto> | ε"""
        while self.verificar(TokenType.VIRGULA):
            self.avancar()
            if not self.expressao():
                return False
        
        return True
    
    def comando_condicional(self):
        """<comando_condicional> ::= se <expressao> entao <comando> <parte_senao>"""
        if not self.esperar(TokenType.SE):
            return False
        
        if not self.expressao():
            return False
        
        if not self.esperar(TokenType.ENTAO):
            return False
        
        if not self.comando():
            return False
        
        return self.parte_senao()
    
    def parte_senao(self):
        """<parte_senao> ::= senao <comando> | ε"""
        if self.verificar(TokenType.SENAO):
            self.avancar()
            return self.comando()
        
        # ε (produção vazia)
        return True
    
    def comando_enquanto(self):
        """<comando_enquanto> ::= enquanto <expressao> faca <comando>"""
        if not self.esperar(TokenType.ENQUANTO):
            return False
        
        if not self.expressao():
            return False
        
        if not self.esperar(TokenType.FACA):
            return False
        
        return self.comando()
    
    def comando_leitura(self):
        """<comando_leitura> ::= leia ( <identificador> )"""
        if not self.esperar(TokenType.LEIA):
            return False
        
        if not self.esperar(TokenType.ABRE_PAREN):
            return False
        
        if not self.esperar(TokenType.IDENTIFICADOR):
            return False
        
        return self.esperar(TokenType.FECHA_PAREN)
    
    def comando_escrita(self):
        """<comando_escrita> ::= escreva ( <conteudo_escrita> )"""
        if not self.esperar(TokenType.ESCREVA):
            return False
        
        if not self.esperar(TokenType.ABRE_PAREN):
            return False
        
        if not self.conteudo_escrita():
            return False
        
        return self.esperar(TokenType.FECHA_PAREN)
    
    def conteudo_escrita(self):
        """<conteudo_escrita> ::= <identificador> | <expressao>"""
        # Como identificador também é uma expressão, apenas chamamos expressao
        return self.expressao()
    
    def comando_desvio(self):
        """<comando_desvio> ::= pare | continue"""
        if self.verificar(TokenType.PARE) or self.verificar(TokenType.CONTINUE):
            self.avancar()
            return True
        else:
            self.erro(f"esperado 'PARE' ou 'CONTINUE'")
            return False
    
    # EXPRESSÕES
    def expressao(self):
        """<expressao> ::= <expressao_ou>"""
        return self.expressao_ou()
    
    def expressao_ou(self):
        """<expressao_ou> ::= <expressao_e> <expressao_ou_resto>"""
        if not self.expressao_e():
            return False
        
        return self.expressao_ou_resto()
    
    def expressao_ou_resto(self):
        """<expressao_ou_resto> ::= ou <expressao_e> <expressao_ou_resto> | ε"""
        while self.verificar(TokenType.OU):
            self.avancar()
            if not self.expressao_e():
                return False
        
        return True
    
    def expressao_e(self):
        """<expressao_e> ::= <expressao_relacional> <expressao_e_resto>"""
        if not self.expressao_relacional():
            return False
        
        return self.expressao_e_resto()
    
    def expressao_e_resto(self):
        """<expressao_e_resto> ::= e <expressao_relacional> <expressao_e_resto> | ε"""
        while self.verificar(TokenType.E):
            self.avancar()
            if not self.expressao_relacional():
                return False
        
        return True
    
    def expressao_relacional(self):
        """<expressao_relacional> ::= <expressao_aritmetica> <expressao_relacional_resto>"""
        if not self.expressao_aritmetica():
            return False
        
        return self.expressao_relacional_resto()
    
    def expressao_relacional_resto(self):
        """<expressao_relacional_resto> ::= <op_relacional> <expressao_aritmetica> | ε"""
        if self.op_relacional():
            return self.expressao_aritmetica()
        
        # ε (produção vazia)
        return True
    
    def op_relacional(self):
        """<op_relacional> ::= == | != | < | <= | > | >="""
        if self.verificar(TokenType.IGUAL) or \
           self.verificar(TokenType.DIFERENTE) or \
           self.verificar(TokenType.MENOR) or \
           self.verificar(TokenType.MENOR_IGUAL) or \
           self.verificar(TokenType.MAIOR) or \
           self.verificar(TokenType.MAIOR_IGUAL):
            self.avancar()
            return True
        
        return False
    
    def expressao_aritmetica(self):
        """<expressao_aritmetica> ::= <termo> <expressao_aritmetica_resto>"""
        if not self.termo():
            return False
        
        return self.expressao_aritmetica_resto()
    
    def expressao_aritmetica_resto(self):
        """<expressao_aritmetica_resto> ::= <op_soma> <termo> <expressao_aritmetica_resto> | ε"""
        while self.op_soma():
            if not self.termo():
                return False
        
        return True
    
    def op_soma(self):
        """<op_soma> ::= + | -"""
        if self.verificar(TokenType.MAIS) or self.verificar(TokenType.MENOS):
            self.avancar()
            return True
        
        return False
    
    def termo(self):
        """<termo> ::= <fator> <termo_resto>"""
        if not self.fator():
            return False
        
        return self.termo_resto()
    
    def termo_resto(self):
        """<termo_resto> ::= <op_mult> <fator> <termo_resto> | ε"""
        while self.op_mult():
            if not self.fator():
                return False
        
        return True
    
    def op_mult(self):
        """<op_mult> ::= * | div"""
        if self.verificar(TokenType.MULTIPLICACAO) or self.verificar(TokenType.DIV):
            self.avancar()
            return True
        
        return False
    
    def fator(self):
        """<fator> ::= <identificador> <fator_resto> | <numero> | verdadeiro | falso | ( <expressao> ) | nao <fator>"""
        
        if self.verificar(TokenType.IDENTIFICADOR):
            self.avancar()
            return self.fator_resto()
        
        elif self.verificar(TokenType.NUMERO):
            self.avancar()
            return True
        
        elif self.verificar(TokenType.VERDADEIRO) or self.verificar(TokenType.FALSO):
            self.avancar()
            return True
        
        elif self.verificar(TokenType.ABRE_PAREN):
            self.avancar()
            if not self.expressao():
                return False
            return self.esperar(TokenType.FECHA_PAREN)
        
        elif self.verificar(TokenType.NAO):
            self.avancar()
            return self.fator()
        
        else:
            self.erro(f"esperado identificador, número, literal booleano, '(' ou 'nao'")
            return False
    
    def fator_resto(self):
        """<fator_resto> ::= ( <argumentos> ) | ε"""
        if self.verificar(TokenType.ABRE_PAREN):
            self.avancar()
            if not self.argumentos():
                return False
            return self.esperar(TokenType.FECHA_PAREN)
        
        # ε (produção vazia)
        return True
    
    # MÉTODO PRINCIPAL
    def analisar(self):
        """Inicia a análise sintática"""
        sucesso = self.programa()
        
        # Verifica se chegou ao EOF
        if sucesso and not self.verificar(TokenType.EOF):
            self.erro(f"código após o fim do programa")
            sucesso = False
        
        return sucesso, self.erros
