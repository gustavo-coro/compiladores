import re
import sys

REGEX_LIST = [
    ('COMENTARIO',      r'//.*|/\*[\s\S]*?\*/'),
    ('TEXTO',           r'"(\\.|[^"\\])*"|\'(\\.|[^\'\\])\''),
    ('NUMERO',          r'\b(0[xX][0-9a-fA-F]+|0[0-7]+|\d+(\.\d+)?([eE][-+]?\d+)?)([uUlL]*)\b'),
    ('PALAVRA_CHAVE',   r'\b(?:int|float|char|if|else|while|for|return|void|struct|typedef|break|continue|double|long|short|unsigned|signed|const|static|enum|do|switch|case|default|sizeof|goto|union|volatile|register|extern|auto)\b'),
    ('IDENTIFICADOR',   r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'),
    ('OPERADOR',        r'(\+\+|--|==|!=|<=|>=|&&|\|\||<<=|>>=|\+=|-=|\*=|/=|%=|&=|\|=|\^=|=|<<|>>|\?|:|[+\-*/%<>=!&|^~])'),
    ('SEPARADOR',       r'[{}()\[\],.;]'),
    ('ESPACO',          r'\s+'),
    ('ERRO',            r'.'),
]

TOKEN_REGEX = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in REGEX_LIST)
token_re = re.compile(TOKEN_REGEX)

class Scanner:

    def __init__(self, input: str, token_regex:re.Pattern[str]):
        self.input = input
        self.token_regex = token_re
        self.id = 1
        self.tokens = []
        self.errors = []

        self.line_starts = [0]
        for match in re.finditer(r'\n', self.input):
            self.line_starts.append(match.end())

    def run(self):
        for match in token_re.finditer(self.input):
            kind = match.lastgroup
            value = match.group()
            start = match.start()

            line_num = 1
            for i, line_start in enumerate(self.line_starts):
                if start >= line_start:
                    line_num = i + 1
                else:
                    break

            line_start_index = self.line_starts[line_num - 1]
            column = start - line_start_index + 1

            if kind == 'ESPACO':
                continue
            elif kind == 'ERRO':
                self.errors.append({
                    'linha': line_num,
                    'coluna': column,
                    'valor': value,
                    'mensagem': f"ERRO: valor inesperado '{value}'"
                })
            else:
                self.tokens.append({
                    'id': self.id,
                    'tipo': kind,
                    'valor': value,
                    'linha': line_num,
                    'coluna': column
                })
                self.id += 1

        return self.tokens, self.errors
    
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Erro no número de argumentos.")
        print("Especifique o caminho do arquivo")
        exit()

    file_name = sys.argv[1]

    try:
        with open(file_name, "r") as file:
            input = file.read()
    except FileNotFoundError:
        print("Arquivo não encontrado.")
        exit()

    scanner = Scanner(input, token_re)

    tokens, errors = scanner.run()

    print("Tokens:")
    for token in tokens:
        print(f"ID: {token['id']}, TIPO: {token['tipo']}, VALOR: {token['valor']}, LINHA: {token['linha']}, COLUNA: {token['coluna']}")

    print("\Erros:")
    if errors:
        for err in errors:
            print(f"[Linha {err['linha']}:{err['coluna']}] {err['mensagem']}")