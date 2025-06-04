from src.scanner import Scanner
from src.scanner import token_re
from src.parser import Parser
import sys

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python parser.py <arquivo_entrada>")
        sys.exit(1)
    
    file_name = sys.argv[1]
    
    try:
        with open(file_name, "r") as file:
            input_text = file.read()
    except FileNotFoundError:
        print(f"Erro: Arquivo '{file_name}' não encontrado")
        sys.exit(1)
    
    scanner = Scanner(input_text, token_re)
    tokens, lex_errors = scanner.run()

    for i in tokens:
        print(i)
    
    if lex_errors:
        print("Erros léxicos:")
        for error in lex_errors:
            print(error)
        sys.exit()

    parser = Parser(tokens)
    ast, errors = parser.parse()
    
    print("AST:")
    print(ast)
    
    print("\nErros Sintáticos:")
    for error in errors:
        print(error)