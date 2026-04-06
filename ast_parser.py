"""
ast_parser.py - Generador de Árbol de Sintaxis Abstracta (AST)

Uso:
    python ast_parser.py <archivo.txt>
    python ast_parser.py --ejemplo

Formato del archivo .txt:
    GRAMMAR
    <reglas de la gramática en formato BNF simplificado>
    END_GRAMMAR
    STRING
    <cadena a analizar>
    END_STRING
"""

import sys
import argparse
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────
#  Nodo del AST
# ─────────────────────────────────────────────

@dataclass
class ASTNode:
    name: str
    value: Optional[str] = None
    children: list = field(default_factory=list)

    def add_child(self, child: "ASTNode"):
        self.children.append(child)

    def pretty_print(self, indent: int = 0, prefix: str = ""):
        connector = "└── " if prefix == "last" else ("├── " if prefix else "")
        label = f'"{self.value}"' if self.value is not None else ""
        print(" " * indent + connector + f"[{self.name}] {label}")
        for i, child in enumerate(self.children):
            is_last = i == len(self.children) - 1
            child.pretty_print(indent + 4, "last" if is_last else "mid")


# ─────────────────────────────────────────────
#  Lexer (Tokenizador)
# ─────────────────────────────────────────────

@dataclass
class Token:
    type: str
    value: str

    def __repr__(self):
        return f"Token({self.type}, {self.value!r})"


class Lexer:
    """Tokeniza una cadena de entrada en tokens básicos."""

    RULES = [
        ("NUMBER",   r"\d+(\.\d+)?"),
        ("ID",       r"[a-zA-Z_][a-zA-Z0-9_]*"),
        ("OP",       r"[+\-*/^]"),
        ("LPAREN",   r"\("),
        ("RPAREN",   r"\)"),
        ("ASSIGN",   r"="),
        ("COMMA",    r","),
        ("SEMI",     r";"),
        ("WS",       r"\s+"),
    ]

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.tokens: list[Token] = []

    def tokenize(self) -> list[Token]:
        import re
        combined = "|".join(f"(?P<{name}>{pattern})" for name, pattern in self.RULES)
        regex = re.compile(combined)

        for match in regex.finditer(self.text):
            kind = match.lastgroup
            value = match.group()
            if kind == "WS":
                continue
            self.tokens.append(Token(kind, value))

        self.tokens.append(Token("EOF", ""))
        return self.tokens


# ─────────────────────────────────────────────
#  Gramática
# ─────────────────────────────────────────────

class Grammar:
    """
    Carga y representa una gramática BNF simplificada.

    Formato esperado:
        expr   -> term expr_tail
        expr_tail -> + term expr_tail | - term expr_tail | epsilon
        term   -> factor term_tail
        term_tail -> * factor term_tail | / factor term_tail | epsilon
        factor -> NUMBER | ID | ( expr )
    """

    def __init__(self):
        self.rules: dict[str, list[list[str]]] = {}
        self.start: Optional[str] = None

    def load(self, text: str):
        for line in text.strip().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "->" not in line:
                raise ValueError(f"Regla inválida (falta '->'): {line!r}")

            lhs, rhs = line.split("->", 1)
            lhs = lhs.strip()
            alternatives = [alt.split() for alt in rhs.split("|")]

            if lhs not in self.rules:
                self.rules[lhs] = []
            self.rules[lhs].extend(alternatives)

            if self.start is None:
                self.start = lhs

    def __repr__(self):
        lines = []
        for lhs, alts in self.rules.items():
            rhs = " | ".join(" ".join(a) for a in alts)
            lines.append(f"  {lhs} -> {rhs}")
        return "Grammar:\n" + "\n".join(lines)


# ─────────────────────────────────────────────
#  Parser LL(1) genérico
# ─────────────────────────────────────────────

class Parser:
    """
    Parser LL(1) que construye un AST basado en la gramática cargada.

    Limitaciones:
      - No calcula automáticamente la tabla LL(1); usa la gramática directamente
        con backtracking ligero para manejar alternativas.
      - Soporta el símbolo especial 'epsilon' para producciones vacías.
      - Los tokens terminales deben coincidir exactamente en tipo o valor.
    """

    def __init__(self, grammar: Grammar, tokens: list[Token]):
        self.grammar = grammar
        self.tokens = tokens
        self.pos = 0

    # ── utilidades ──────────────────────────────

    def current(self) -> Token:
        return self.tokens[self.pos]

    def consume(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def is_terminal(self, symbol: str) -> bool:
        return symbol not in self.grammar.rules

    def match_terminal(self, symbol: str) -> Optional[Token]:
        tok = self.current()
        if tok.value == symbol or tok.type == symbol:
            return self.consume()
        return None

    # ── parsing recursivo ────────────────────────

    def parse(self) -> ASTNode:
        if self.grammar.start is None:
            raise ValueError("La gramática está vacía (sin reglas).")
        root = self._parse_symbol(self.grammar.start)
        if root is None:
            raise SyntaxError(
                f"No se pudo analizar la cadena con la gramática dada.\n"
                f"Token problemático: {self.current()}"
            )
        if self.current().type != "EOF":
            raise SyntaxError(
                f"Entrada no consumida completamente. Resta desde: {self.current()!r}"
            )
        return root

    def _parse_symbol(self, symbol: str) -> Optional[ASTNode]:
        if symbol == "epsilon":
            return ASTNode("ε")

        if self.is_terminal(symbol):
            tok = self.match_terminal(symbol)
            if tok:
                return ASTNode(tok.type, tok.value)
            return None

        # No terminal: intentar cada alternativa (backtracking)
        alternatives = self.grammar.rules[symbol]
        saved_pos = self.pos

        for alt in alternatives:
            self.pos = saved_pos
            node = ASTNode(symbol)
            success = True

            for sym in alt:
                child = self._parse_symbol(sym)
                if child is None:
                    success = False
                    break
                if child.name != "ε":
                    node.add_child(child)

            if success:
                return node

        self.pos = saved_pos
        return None


# ─────────────────────────────────────────────
#  Lectura del archivo de entrada
# ─────────────────────────────────────────────

def parse_input_file(filepath: str) -> tuple[str, str]:
    """
    Lee el archivo .txt y extrae la gramática y la cadena.

    Formato:
        GRAMMAR
        ...reglas...
        END_GRAMMAR
        STRING
        ...cadena...
        END_STRING
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"[ERROR] Archivo no encontrado: {filepath!r}")
        sys.exit(1)

    def extract_block(tag: str) -> str:
        start_tag = tag
        end_tag = f"END_{tag}"
        try:
            start = content.index(start_tag) + len(start_tag)
            end = content.index(end_tag)
            return content[start:end].strip()
        except ValueError:
            print(f"[ERROR] No se encontró el bloque {tag} / {end_tag} en el archivo.")
            sys.exit(1)

    grammar_text = extract_block("GRAMMAR")
    string_text = extract_block("STRING")
    return grammar_text, string_text


# ─────────────────────────────────────────────
#  Ejemplo integrado
# ─────────────────────────────────────────────

EXAMPLE_GRAMMAR = """\
# Gramática para expresiones aritméticas simples
expr      -> term expr_tail
expr_tail -> + term expr_tail
expr_tail -> - term expr_tail
expr_tail -> epsilon
term      -> factor term_tail
term_tail -> * factor term_tail
term_tail -> / factor term_tail
term_tail -> epsilon
factor    -> ( expr )
factor    -> NUMBER
factor    -> ID
"""

EXAMPLE_STRING = "3 + x * 2"


def run_example():
    print("=" * 60)
    print("  EJEMPLO INTEGRADO")
    print("=" * 60)
    print(f"\nGramática:\n{EXAMPLE_GRAMMAR}")
    print(f"Cadena de entrada: {EXAMPLE_STRING!r}\n")
    run(EXAMPLE_GRAMMAR, EXAMPLE_STRING)


# ─────────────────────────────────────────────
#  Función principal
# ─────────────────────────────────────────────

def run(grammar_text: str, input_string: str):
    # 1. Cargar gramática
    grammar = Grammar()
    grammar.load(grammar_text)
    print(grammar)

    # 2. Tokenizar
    lexer = Lexer(input_string)
    tokens = lexer.tokenize()
    print(f"\nTokens: {tokens[:-1]}")  # omite EOF

    # 3. Parsear
    parser = Parser(grammar, tokens)
    try:
        tree = parser.parse()
    except SyntaxError as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)

    # 4. Mostrar árbol
    print("\nÁrbol AST:")
    print("─" * 40)
    tree.pretty_print()
    print("─" * 40)
    print("\n✓ Cadena aceptada por la gramática.")


def main():
    arg_parser = argparse.ArgumentParser(
        description="Generador de Árbol AST a partir de una gramática y una cadena."
    )
    arg_parser.add_argument(
        "archivo",
        nargs="?",
        help="Archivo .txt con la gramática y la cadena de entrada.",
    )
    arg_parser.add_argument(
        "--ejemplo",
        action="store_true",
        help="Ejecuta el ejemplo integrado (expresiones aritméticas).",
    )
    args = arg_parser.parse_args()

    if args.ejemplo:
        run_example()
        return

    if not args.archivo:
        arg_parser.print_help()
        sys.exit(0)

    grammar_text, input_string = parse_input_file(args.archivo)

    print("=" * 60)
    print(f"  Analizando archivo: {args.archivo}")
    print("=" * 60)
    print(f"\nCadena de entrada: {input_string!r}\n")
    run(grammar_text, input_string)


if __name__ == "__main__":
    main()
