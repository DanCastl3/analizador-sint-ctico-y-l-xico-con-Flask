import ply.lex as lex
import ply.yacc as yacc
from flask import Flask, render_template, request

app = Flask(__name__)

# Definición de palabras reservadas
reserved = {
    'public': 'PUBLIC',
    'static': 'STATIC',
    'void': 'VOID',
    'n': 'N',
    'for': 'FOR',
    'System': 'SYSTEM',
    'out': 'OUT',
    'println': 'PRINTLN'
}

tokens = [
    'PABIERTO', 'PCERRADO', 'LLAVE_ABIERTA', 'LLAVE_CERRADA', 
    'OPERADOR', 'SIMBOLO', 'ID', 'NUMERO', 'CADENA'
] + list(reserved.values())

# Expresiones regulares para las palabras reservadas y otros tokens
t_PUBLIC = r'public'
t_STATIC = r'static'
t_VOID = r'void'
t_N = r'n'
t_FOR = r'for'
t_SYSTEM = r'System'
t_OUT = r'out'
t_PRINTLN = r'println'
t_OPERADOR = r'='

# Identificadores
def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'ID')  # Verificar si es una palabra reservada
    return t

# Números
def t_NUMERO(t):
    r'[0-9]+'
    t.value = int(t.value)
    return t

# Cadenas
def t_CADENA(t):
    r'"[^"]*"'
    return t

# Expresión regular para símbolos 
def t_SIMBOLO(t):
    r'[.;]'
    return t

# Símbolos
t_PABIERTO = r'\('
t_PCERRADO = r'\)'
t_LLAVE_ABIERTA = r'\{'
t_LLAVE_CERRADA = r'\}'

# Contador de líneas
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Ignorar espacios en blanco, tabulaciones y nuevas líneas
t_ignore = ' \t\r'

# Manejo de errores léxicos
def t_error(t):
    error_message = f"Error léxico: Caracter no válido '{t.value[0]}' en la línea {t.lexer.lineno}"
    t.lexer.errors.append(error_message)
    t.lexer.skip(1)

# Construcción del lexer
lexer = lex.lex()
lexer.errors = []  # Lista para almacenar errores léxicos

# Definir la jerarquía de las producciones
def p_program(p):
    '''program : PUBLIC STATIC VOID ID PABIERTO PCERRADO LLAVE_ABIERTA statements LLAVE_CERRADA'''
    p[0] = ('program', p[4], p[8])

def p_statements(p):
    '''statements : statement statements
                  | statement
                  | empty'''
    p[0] = p[1:] if len(p) > 1 else []

def p_statement(p):
    '''statement : N OPERADOR SIMBOLO
                 | FOR PABIERTO statement PCERRADO LLAVE_ABIERTA statements LLAVE_CERRADA
                 | LLAVE_ABIERTA statements LLAVE_CERRADA'''
    if len(p) == 4:  # Caso para 'N = SIMBOLO'
        p[0] = ('statement', p[1], p[2], p[3])
    elif len(p) == 8:  # Caso para el bucle for
        p[0] = ('for_loop', p[3], p[5])
    else:
        p[0] = ('statement', p[2])

def p_empty(p):
    '''empty : '''
    pass

# Manejo de errores sintácticos
def p_error(p):
    if p:
        error_message = f"Error sintáctico: Token inesperado '{p.value}' en la línea {p.lineno}"
        parser.errors.append(error_message)
    else:
        parser.errors.append("Error sintáctico: Entrada incompleta o inesperada al final")

# Construcción del parser
parser = yacc.yacc()
parser.errors = []  # Lista para almacenar errores sintácticos

@app.route('/', methods=['GET', 'POST'])
def index():
    error_message = None
    sintactico_result = None
    result_lexema = []
    contador = {}
    
    if request.method == 'POST':
        expresion = request.form.get('Expresion')
        lexer.lineno = 1  # Reiniciar el número de línea antes de procesar
        lexer.errors = []  # Reiniciar lista de errores léxicos
        lexer.input(expresion)
        
        # Proceso de tokens en el orden en que aparecen, con número de línea
        for token in lexer:
            if token.type in reserved.values():
                result_lexema.append(("RESERVADO", token.value, token.lineno))
            elif token.type == "ID":
                result_lexema.append(("IDENTIFICADOR", token.value, token.lineno))
            elif token.type == "PABIERTO":
                result_lexema.append(("PARENTESIS IZQUIERDO", token.value, token.lineno))
            elif token.type == "PCERRADO":
                result_lexema.append(("PARENTESIS DERECHO", token.value, token.lineno))
            elif token.type == "LLAVE_ABIERTA":
                result_lexema.append(("DELIMITADOR", token.value, token.lineno))
            elif token.type == "LLAVE_CERRADA":
                result_lexema.append(("DELIMITADOR", token.value, token.lineno))
            elif token.type == "OPERADOR":
                result_lexema.append(("OPERADOR", token.value, token.lineno))
            elif token.type == "SIMBOLO":
                result_lexema.append(("SIMBOLO", token.value, token.lineno))
            elif token.type == "NUMERO":
                result_lexema.append(("NUMERO", token.value, token.lineno))
            elif token.type == "CADENA":
                result_lexema.append(("CADENA", token.value, token.lineno))
        
        # Contar las ocurrencias de cada tipo de token
        for tipo, palabra, numero in result_lexema:
            if tipo in contador:
                contador[tipo] += 1
            else:
                contador[tipo] = 1

        # Verificar si hubo errores léxicos
        if lexer.errors:
            error_message = "\n".join(lexer.errors)
        else:
            # Intentar realizar el análisis sintáctico
            parser.errors = []  # Reiniciar lista de errores sintácticos
            try:
                sintactico_result = parser.parse(expresion)
            except Exception as e:
                error_message = str(e)
            
            # Verificar si hubo errores sintácticos
            if parser.errors:
                error_message = "\n".join(parser.errors)
        
        return render_template('index.html', tokens=result_lexema, contador=contador, 
                               expresion=expresion, error_message=error_message, 
                               sintactico_result=sintactico_result)
    
    return render_template('index.html', expresion=None)

if __name__ == '__main__':
    app.run(debug=True)
