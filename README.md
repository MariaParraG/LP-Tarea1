# Generador de Árbol AST

Programa en Python que, dada una **gramática BNF simplificada** y una **cadena de entrada**, genera y visualiza su **Árbol de Sintaxis Abstracta (AST)**.

---

## Características

- Lee gramática y cadena desde un archivo `.txt` estructurado.
- Tokenizador (Lexer) integrado con soporte para: números, identificadores, operadores aritméticos y paréntesis.
- Parser **LL(1) con backtracking** que construye el AST recursivamente.
- Visualización del árbol en consola con conectores tipo árbol (`├──`, `└──`).
- Modo de ejemplo integrado (`--ejemplo`) sin necesidad de archivo externo.
- Sin dependencias externas — solo Python 3.10+ estándar.

---

## Estructura del proyecto

```
.
├── ast_parser.py   # Programa principal
├── ejemplo.txt     # Archivo de entrada de ejemplo
└── README.md       # Este archivo
```

---

## Instalación

No requiere instalación de paquetes externos. Solo necesitas **Python 3.10 o superior**.

```bash
python --version   # Verificar versión
```

---

## Uso

### Opción 1 — Archivo `.txt`

```bash
python ast_parser.py <archivo.txt>
```

### Opción 2 — Ejemplo integrado

```bash
python ast_parser.py --ejemplo
```

### Ayuda

```bash
python ast_parser.py --help
```

---

## Formato del archivo `.txt`

El archivo debe contener dos bloques obligatorios:

```
GRAMMAR
<reglas de la gramática>
END_GRAMMAR

STRING
<cadena a analizar>
END_STRING
```

### Reglas de la gramática

Cada línea define una producción con el formato:

```
no_terminal -> símbolo1 símbolo2 ... | alternativa2 | ...
```

También se puede usar una línea por alternativa:

```
expr_tail -> + term expr_tail
expr_tail -> - term expr_tail
expr_tail -> epsilon
```

- El símbolo especial `epsilon` representa la producción vacía (ε).
- Las líneas que empiezan con `#` son comentarios y se ignoran.
- El **primer no terminal** definido se toma como símbolo inicial.

---

## Ejemplo completo

### Archivo `ejemplo.txt`

```
GRAMMAR
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
END_GRAMMAR

STRING
3 + x * 2
END_STRING
```

### Ejecución

```bash
python ast_parser.py ejemplo.txt
```

### Salida esperada

```
============================================================
  Analizando archivo: ejemplo.txt
============================================================

Cadena de entrada: '3 + x * 2'

Grammar:
  expr -> term expr_tail
  expr_tail -> + term expr_tail | - term expr_tail | epsilon
  term -> factor term_tail
  term_tail -> * factor term_tail | / factor term_tail | epsilon
  factor -> ( expr ) | NUMBER | ID

Tokens: [Token(NUMBER, '3'), Token(OP, '+'), Token(ID, 'x'), Token(OP, '*'), Token(NUMBER, '2')]

Árbol AST:
────────────────────────────────────────
[expr]
    ├── [term]
    │   ├── [factor]
    │   │   └── [NUMBER] "3"
    │   └── [term_tail]
    └── [expr_tail]
        ├── [OP] "+"
        ├── [term]
        │   ├── [factor]
        │   │   └── [ID] "x"
        │   └── [term_tail]
        │       ├── [OP] "*"
        │       ├── [factor]
        │       │   └── [NUMBER] "2"
        │       └── [term_tail]
        └── [expr_tail]
────────────────────────────────────────

✓ Cadena aceptada por la gramática.
```

---

## Arquitectura

El programa está dividido en los siguientes módulos (todos dentro de `ast_parser.py`):

| Componente | Clase | Descripción |
|---|---|---|
| Nodo del AST | `ASTNode` | Nodo con nombre, valor opcional e hijos. Incluye `pretty_print`. |
| Token | `Token` | Unidad léxica con tipo y valor. |
| Lexer | `Lexer` | Tokenizador por expresiones regulares. |
| Gramática | `Grammar` | Carga y representa reglas BNF simplificadas. |
| Parser | `Parser` | Parser LL(1) con backtracking que construye el AST. |

### Flujo de ejecución

```
Archivo .txt
     │
     ▼
parse_input_file()  ──► grammar_text, input_string
     │
     ├──► Grammar.load()    ──► reglas BNF
     │
     ├──► Lexer.tokenize()  ──► lista de Tokens
     │
     └──► Parser.parse()    ──► ASTNode (árbol)
               │
               ▼
         ASTNode.pretty_print()  ──► salida en consola
```

---

## Limitaciones

- El Lexer reconoce los siguientes tipos de tokens: `NUMBER`, `ID`, `OP` (`+ - * / ^`), `LPAREN`, `RPAREN`, `ASSIGN`, `COMMA`, `SEMI`. Para cadenas con otros tokens se debe extender `Lexer.RULES`.
- El Parser usa **backtracking**, por lo que gramáticas muy ambiguas o con muchas alternativas pueden ser lentas.
- No valida automáticamente si la gramática es LL(1); es responsabilidad del usuario diseñar una gramática adecuada.

---

## Extensión del Lexer

Para agregar nuevos tipos de tokens, añade una tupla a `Lexer.RULES` en `ast_parser.py`:

```python
RULES = [
    ("FLOAT",  r"\d+\.\d+"),   # nuevo: float antes de NUMBER
    ("NUMBER", r"\d+"),
    ...
]
```

El orden importa: los patrones se evalúan de arriba hacia abajo.
