import re

# Token specification for a simple C lexer
TOKEN_SPECIFICATION = [
    ('COMMENT',      r'//.*|/\*[\s\S]*?\*/'),
    ('STRING',       r'"(\\.|[^"\\])*"'),
    ('CHAR',         r"'(\\.|[^'\\])'"),
    ('NUMBER',       r'\b\d+(\.\d+)?([eE][-+]?\d+)?\b'),
    ('KEYWORD',      r'\b(?:int|float|char|if|else|while|for|return|void|struct|typedef|break|continue|double|long|short|unsigned|signed|const|static|enum|do|switch|case|default|sizeof|goto|union|volatile|register|extern|auto)\b'),
    ('IDENTIFIER',   r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'),
    ('OPERATOR',     r'\+{1,2}|-{1,2}|==|!=|<=|>=|&&|\|\||[+\-*/%<>=!&|^~]'),
    ('SEPARATOR',    r'[{}()\[\],.;]'),
    ('WHITESPACE',   r'\s+'),
    ('MISMATCH',     r'.'),
]

# Compile regex
TOKEN_REGEX = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPECIFICATION)
token_re = re.compile(TOKEN_REGEX)

def tokenize(code):
    tokens = []
    errors = []
    line_starts = [0]
    for match in re.finditer(r'\n', code):
        line_starts.append(match.end())

    token_id = 1

    for match in token_re.finditer(code):
        kind = match.lastgroup
        value = match.group()
        start = match.start()

        # Find line number using line_starts
        line_num = 1
        for i, line_start in enumerate(line_starts):
            if start >= line_start:
                line_num = i + 1
            else:
                break

        line_start_index = line_starts[line_num - 1]
        column = start - line_start_index + 1  # 1-based indexing

        if kind == 'WHITESPACE':
            continue
        elif kind == 'MISMATCH':
            errors.append({
                'line': line_num,
                'column': column,
                'value': value,
                'message': f"Lexical error: Unexpected character '{value}'"
            })
        else:
            tokens.append({
                'id': token_id,
                'type': kind,
                'value': value,
                'line': line_num,
                'column': column
            })
            token_id += 1

    return tokens, errors

# Example usage
if __name__ == "__main__":
    c_code = '''
    int main() {
        int a = 5;
        float b = 3.14;
        int** pooint;
        a++;
        char c = 'x';
        $invalid = 10;   // Invalid symbol $
        printf("Test@string");
        return 0;
    }
    '''

    tokens, errors = tokenize(c_code)

    print("Tokens:")
    for token in tokens:
        print(f"ID: {token['id']}, TYPE: {token['type']}, VALUE: {token['value']}, LINE: {token['line']}, COLUMN: {token['column']}")

    print("\nErrors:")
    if errors:
        for err in errors:
            print(f"[Line {err['line']}:{err['column']}] {err['message']}")
    else:
        print("No lexical errors found.")
