from src.scanner import Scanner
from src.scanner import token_re
from src.parser import CParser
import sys

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python parser.py <input_file>")
        sys.exit(1)
    
    file_name = sys.argv[1]
    
    try:
        with open(file_name, "r") as file:
            input_text = file.read()
    except FileNotFoundError:
        print(f"Error: File '{file_name}' not found")
        sys.exit(1)
    
    # Run lexer
    scanner = Scanner(input_text, token_re)
    tokens, lex_errors = scanner.run()

    for i in tokens:
        print(i)
    
    if lex_errors:
        print("Lexical errors found:")
        for error in lex_errors:
            print(error)
    
    # Run parser
    parser = CParser(tokens)
    ast, errors = parser.parse()
    
    print("Abstract Syntax Tree:")
    print(ast)
    
    print("\nErrors encountered:")
    for error in errors:
        print(error)