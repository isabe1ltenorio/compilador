"""
Analisador Semântico — Tabela de Símbolos e Controle de Escopo
Tipos suportados: inteiro, booleano, char, float, void
Tipagem estática e forte — sem coerção implícita
Sem sobrecarga de operadores ou funções
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict

TIPOS_VALIDOS   = {'inteiro', 'booleano', 'char', 'float', 'void'}

# Tipos que aceitam operadores aritméticos: +, -, *
# char NÃO está aqui — não pode fazer 'a' + 'b'
TIPOS_NUMERICOS = {'inteiro', 'float'}

# Tipos que aceitam operadores de ordem: <, <=, >, >=
# char ESTÁ aqui — pode comparar 'a' < 'z' (comparação de caracteres)
# booleano NÃO está — 'verdadeiro < falso' não faz sentido
TIPOS_ORDENADOS = {'inteiro', 'float', 'char'}

# Categorias possíveis de um símbolo
CATEGORIAS = {'variavel', 'parametro', 'funcao', 'procedimento'}

@dataclass
class EntradaSimbolo:
    nome:       str
    tipo:       str
    categoria:  str
    escopo:     str
    parametros: List[str] = field(default_factory=list)
    linha:      int = 0

    def __str__(self) -> str:
        """
        Define como a entrada aparece quando impressa no terminal
        """
        if self.categoria in ('funcao', 'procedimento'):
            # ', '.join(['inteiro', 'inteiro']) -> 'inteiro, inteiro'
            params = ', '.join(self.parametros) if self.parametros else '—'
            return (f"[{self.categoria.upper():12}] {self.nome:20} "
                    f"retorno={self.tipo:8}  params=({params})  "
                    f"escopo={self.escopo}  linha={self.linha}")
        return (f"[{self.categoria.upper():12}] {self.nome:20} "
                f"tipo={self.tipo:8}  escopo={self.escopo}  linha={self.linha}")


class TabelaSimbolos:
    def __init__(self):
        # List[Dict[str, EntradaSimbolo]] — anotação de tipo para clareza
        self._pilha:         List[Dict[str, EntradaSimbolo]] = [{}]
        self._nomes_escopos: List[str]                       = ['global']
        self._historico:     List[EntradaSimbolo]            = []
        self.tipo_retorno_atual: Optional[str]               = None

    # ── Propriedades ──────────────────────────────────────────────────────────

    @property
    def escopo_atual(self) -> str:
        return self._nomes_escopos[-1]

    @property
    def em_funcao(self) -> bool:
        return self.tipo_retorno_atual is not None

    @property
    def profundidade(self) -> int:
        return len(self._pilha)

    def entrar_escopo(self, nome: str, tipo_retorno: Optional[str] = None):
        self._pilha.append({})              # abre dicionário vazio no topo
        self._nomes_escopos.append(nome)    # registra o nome do novo escopo
        if tipo_retorno is not None:
            self.tipo_retorno_atual = tipo_retorno

    def sair_escopo(self):
        self._pilha.pop()           # remove o topo — a e b desaparecem
        self._nomes_escopos.pop()   # remove o nome do escopo fechado
        # Volta ao global? Reseta o tipo de retorno
        if len(self._pilha) == 1:
            self.tipo_retorno_atual = None

    # ── Operações na tabela ───────────────────────────────────────────────────

    def declarar(self, nome: str, entrada: EntradaSimbolo) -> bool:
        chave = nome.lower()
        # _pilha[-1] é sempre o escopo atual (topo)
        if chave in self._pilha[-1]:
            return False                        # duplicata no escopo atual
        self._pilha[-1][chave] = entrada        # registra no escopo atual
        self._historico.append(entrada)         # registra no histórico permanente
        return True

    def buscar(self, nome: str) -> Optional[EntradaSimbolo]:
        chave = nome.lower()
        # Percorre do topo (índice -1) para a base (índice 0)
        for escopo in reversed(self._pilha):
            if chave in escopo:
                return escopo[chave]    # encontrou — retorna imediatamente
        return None                     # não encontrou em nenhum escopo

    def listar_historico(self) -> List[EntradaSimbolo]:
        return list(self._historico)