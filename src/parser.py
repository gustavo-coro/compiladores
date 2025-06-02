from collections import deque

class ASTNode:
    def __init__(self, node_type, value=None, children=None):
        self.node_type = node_type
        self.value = value
        self.children = children or []
        
    def __repr__(self, level=0):
        ret = "  " * level + f"{self.node_type}"
        if self.value is not None:
            ret += f": {self.value}"
        ret += "\n"
        for child in self.children:
            ret += child.__repr__(level + 1)
        return ret

class ParserError:
    def __init__(self, message, line, column):
        self.message = message
        self.line = line
        self.column = column
        
    def __str__(self):
        return f"Error at line {self.line}, column {self.column}: {self.message}"

class CParser:
    def __init__(self, token_list):
        self.tokens = deque(token_list)
        self.current_token = None
        self.errors = []
        self.advance()
        
    def advance(self):
        try:
            self.current_token = self.tokens.popleft()
        except IndexError:
            self.current_token = None
            
    def expect(self, token_type, value=None, error_message=None):
        if self.current_token is None:
            msg = error_message or f"Expected {token_type} but found end of input"
            self.errors.append(ParserError(msg, -1, -1))
            return False
            
        if self.current_token['tipo'] != token_type:
            msg = error_message or f"Expected {token_type} but found {self.current_token['tipo']}"
            self.errors.append(ParserError(msg, self.current_token['linha'], self.current_token['coluna']))
            return False
            
        if value is not None and self.current_token['valor'] != value:
            msg = error_message or f"Expected {value} but found {self.current_token['valor']}"
            self.errors.append(ParserError(msg, self.current_token['linha'], self.current_token['coluna']))
            return False
            
        self.advance()
        return True
        
    def log_error(self, message):
        if self.current_token:
            self.errors.append(ParserError(message, self.current_token['linha'], self.current_token['coluna']))
        else:
            self.errors.append(ParserError(message, -1, -1))
            
    def parse(self):
        ast = self.parse_program()
        if self.current_token is not None:
            self.log_error("Unexpected token at end of program")
        return ast, self.errors
        
    def parse_program(self):
        functions = []
        while self.current_token is not None:
            if self.current_token['tipo'] == 'PALAVRA_CHAVE' and self.current_token['valor'] in ['int', 'float', 'void']:
                func = self.parse_function()
                if func:
                    functions.append(func)
            else:
                self.log_error(f"Unexpected token {self.current_token['valor']} at global scope")
                self.advance()
                
        return ASTNode('Program', children=functions)
        
    def parse_function(self):
        # Parse return type
        if not self.current_token or self.current_token['tipo'] != 'PALAVRA_CHAVE':
            self.log_error("Expected return type for function")
            return None
            
        return_type = self.current_token['valor']
        self.advance()
        
        # Parse function name
        if not self.current_token or self.current_token['tipo'] != 'IDENTIFICADOR':
            self.log_error("Expected function name")
            return None
            
        func_name = self.current_token['valor']
        self.advance()
        
        # Parse parameters
        if not self.expect('SEPARADOR', '(', "Expected '(' after function name"):
            return None
            
        params = []
        # Simplified parameter parsing - just types and names
        while self.current_token and self.current_token['tipo'] != 'SEPARADOR' or self.current_token['valor'] != ')':
            if self.current_token['tipo'] == 'PALAVRA_CHAVE':
                param_type = self.current_token['valor']
                self.advance()
                if self.current_token and self.current_token['tipo'] == 'IDENTIFICADOR':
                    param_name = self.current_token['valor']
                    self.advance()
                    params.append(ASTNode('Parameter', children=[
                        ASTNode('Type', param_type),
                        ASTNode('Identifier', param_name)
                    ]))
                else:
                    self.log_error("Expected parameter name")
            elif self.current_token['tipo'] == 'SEPARADOR' and self.current_token['valor'] == ',':
                self.advance()
            else:
                self.log_error("Unexpected token in parameter list")
                self.advance()
                
        if not self.expect('SEPARADOR', ')', "Expected ')' after parameters"):
            return None
            
        # Parse function body
        if not self.expect('SEPARADOR', '{', "Expected '{' before function body"):
            return None
            
        body = []
        while self.current_token and (self.current_token['tipo'] != 'SEPARADOR' or self.current_token['valor'] != '}'):
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)
                
        if not self.expect('SEPARADOR', '}', "Expected '}' after function body"):
            return None
            
        return ASTNode('Function', func_name, children=[
            ASTNode('ReturnType', return_type),
            ASTNode('Parameters', children=params),
            ASTNode('Body', children=body)
        ])
        
    def parse_statement(self):
        if not self.current_token:
            return None
            
        # Variable declaration
        if self.current_token['tipo'] == 'PALAVRA_CHAVE' and self.current_token['valor'] in ['int', 'float', 'char']:
            return self.parse_declaration()
        # If statement
        elif self.current_token['tipo'] == 'PALAVRA_CHAVE' and self.current_token['valor'] == 'if':
            return self.parse_if_statement()
        # Return statement
        elif self.current_token['tipo'] == 'PALAVRA_CHAVE' and self.current_token['valor'] == 'return':
            return self.parse_return_statement()
        # Block statement
        elif self.current_token['tipo'] == 'SEPARADOR' and self.current_token['valor'] == '{':
            return self.parse_block()
        # Expression statement (assignment, etc.)
        elif self.current_token['tipo'] == 'IDENTIFICADOR':
            return self.parse_expression_statement()
        else:
            self.log_error(f"Unexpected token {self.current_token['valor']} in statement")
            self.advance()
            return None
            
    def parse_declaration(self):
        type_token = self.current_token
        self.advance()
        
        if not self.current_token or self.current_token['tipo'] != 'IDENTIFICADOR':
            self.log_error("Expected variable name in declaration")
            return None
            
        var_name = self.current_token['valor']
        self.advance()
        
        # Handle initialization
        if self.current_token and self.current_token['tipo'] == 'OPERADOR' and self.current_token['valor'] == '=':
            self.advance()  # consume '='
            init_expr = self.parse_expression()
            if not init_expr:
                self.log_error("Expected expression after '=' in initialization")
                return None
        else:
            init_expr = ASTNode('NoInit')
            
        if not self.expect('SEPARADOR', ';', "Expected ';' after declaration"):
            return None
            
        return ASTNode('Declaration', children=[
            ASTNode('Type', type_token['valor']),
            ASTNode('Identifier', var_name),
            init_expr
        ])
        
    def parse_if_statement(self):
        if not self.expect('PALAVRA_CHAVE', 'if', "Expected 'if'"):
            return None
            
        if not self.expect('SEPARADOR', '(', "Expected '(' after 'if'"):
            return None
            
        condition = self.parse_expression()
        
        if not self.expect('SEPARADOR', ')', "Expected ')' after if condition"):
            return None
            
        then_branch = self.parse_statement()
        
        # Optional else branch
        else_branch = None
        if self.current_token and self.current_token['tipo'] == 'PALAVRA_CHAVE' and self.current_token['valor'] == 'else':
            self.advance()
            else_branch = self.parse_statement()
            
        return ASTNode('IfStatement', children=[
            condition,
            then_branch,
            else_branch or ASTNode('NoElse')
        ])
        
    def parse_return_statement(self):
        if not self.expect('PALAVRA_CHAVE', 'return', "Expected 'return'"):
            return None
            
        expr = self.parse_expression()
        
        if not self.expect('SEPARADOR', ';', "Expected ';' after return"):
            return None
            
        return ASTNode('ReturnStatement', children=[expr])
        
    def parse_block(self):
        if not self.expect('SEPARADOR', '{', "Expected '{' for block"):
            return None
            
        statements = []
        while self.current_token and (self.current_token['tipo'] != 'SEPARADOR' or self.current_token['valor'] != '}'):
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
                
        if not self.expect('SEPARADOR', '}', "Expected '}' after block"):
            return None
            
        return ASTNode('Block', children=statements)
        
    def parse_expression_statement(self):
        expr = self.parse_expression()
        
        if not self.expect('SEPARADOR', ';', "Expected ';' after expression"):
            return None
            
        return ASTNode('ExpressionStatement', children=[expr])
        
    def parse_expression(self):
        # Handle simple expressions: identifiers, numbers, and assignments
        if not self.current_token:
            self.log_error("Unexpected end of input in expression")
            return None
            
        # Handle numeric literals
        if self.current_token['tipo'] == 'NUMERO':
            node = ASTNode('Literal', self.current_token['valor'])
            self.advance()
            return node
            
        # Handle identifiers and assignments
        if self.current_token['tipo'] == 'IDENTIFICADOR':
            left = ASTNode('Identifier', self.current_token['valor'])
            self.advance()
            
            # Check for assignment
            if self.current_token and self.current_token['tipo'] == 'OPERADOR' and self.current_token['valor'] == '=':
                op = self.current_token['valor']
                self.advance()
                right = self.parse_expression()
                return ASTNode('Assignment', op, children=[left, right])
            else:
                return left
                
        self.log_error("Unexpected token in expression")
        return None