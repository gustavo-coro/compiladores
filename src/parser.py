class Node:
    def __init__(self, type_, children=None, value=None):
        self.type = type_
        self.children = children if children is not None else []
        self.value = value

    def __repr__(self, level=0):
        ret = "\t" * level + f"{self.type}: {self.value if self.value else ''}\n"
        for child in self.children:
            ret += child.__repr__(level + 1)
        return ret


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0
        self.errors = []

    def current_token(self):
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        return None

    def advance(self):
        self.position += 1

    def expect(self, tipo, valor=None):
        token = self.current_token()
        if token and token['tipo'] == tipo and (valor is None or token['valor'] == valor):
            self.advance()
            return token
        else:
            expected = f"{tipo}" + (f"('{valor}')" if valor else "")
            found = token['tipo'] if token else 'EOF'
            self.errors.append({
                'mensagem': f"Esperado {expected}, mas encontrado {found}",
                'linha': token['linha'] if token else 'EOF',
                'coluna': token['coluna'] if token else 'EOF'
            })
            return None

    def parse(self):
        nodes = []
        while self.current_token() is not None:
            node = self.parse_function() or self.parse_statement()
            if node:
                nodes.append(node)
            else:
                self.advance()
        return Node('Programa', nodes), self.errors

    def parse_statement(self):
        token = self.current_token()
        if token is None:
            return None

        if token['tipo'] == 'COMENTARIO':
            return self.parse_comment()
            
        if token['tipo'] == 'PALAVRA_CHAVE':
            if token['valor'] in {'int', 'float', 'char', 'double', 'long', 'short', 'unsigned'}:
                return self.parse_declaration()
            elif token['valor'] == 'if':
                return self.parse_if_statement()
            elif token['valor'] == 'while':
                return self.parse_while_loop()
            elif token['valor'] == 'for':
                return self.parse_for_loop()
            elif token['valor'] == 'return':
                return self.parse_return_statement()
            elif token['valor'] == 'do':
                return self.parse_do_while_loop()
        elif token['tipo'] == 'IDENTIFICADOR':
            next_token = self.tokens[self.position + 1] if self.position + 1 < len(self.tokens) else None
            if next_token and next_token['valor'] == '(':
                return self.parse_function_call()
            else:
                return self.parse_assignment_or_expression()
        elif token['valor'] == '{':
            return self.parse_block()
        elif token['valor'] == ';':
            self.advance()
            return Node('Declaração Vazia')
        else:
            self.errors.append({
                'mensagem': f"Declaração ou comando inválido: '{token['valor']}'",
                'linha': token['linha'],
                'coluna': token['coluna']
            })
            return None

    def parse_block(self):
        self.expect('SEPARADOR', '{')
        statements = []
        while self.current_token() and self.current_token()['valor'] != '}':
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
        self.expect('SEPARADOR', '}')
        return Node('Bloco', statements)

    def parse_function(self):
        token = self.current_token()
        if token is None or token['tipo'] != 'PALAVRA_CHAVE' or token['valor'] not in {
            'int', 'float', 'char', 'double', 'long', 'short', 'unsigned', 'void'
        }:
            return None

        return_type = self.expect('PALAVRA_CHAVE')
        func_name = self.expect('IDENTIFICADOR')
        self.expect('SEPARADOR', '(')
        
        parameters = []
        while self.current_token() and self.current_token()['valor'] != ')':
            param_type = self.expect('PALAVRA_CHAVE')
            param_name = self.expect('IDENTIFICADOR')
            parameters.append(Node('Parâmetro', [
                Node('Tipo', value=param_type['valor']),
                Node('Identificador', value=param_name['valor'])
            ]))
            if self.current_token() and self.current_token()['valor'] == ',':
                self.expect('SEPARADOR', ',')
        
        self.expect('SEPARADOR', ')')
        
        body = self.parse_block()
        
        return Node('Função', [
            Node('Tipo de Retorno', value=return_type['valor']),
            Node('Nome da Função', value=func_name['valor']),
            Node('Parâmetro', parameters),
            body
        ])

    def parse_pointer_type(self):
        base_type = self.expect('PALAVRA_CHAVE')
        pointers = []
        
        while self.current_token() and self.current_token()['valor'] == '*':
            pointers.append(self.expect('OPERADOR', '*'))
        
        return base_type, pointers

    def parse_declaration(self):
        base_type, pointers = self.parse_pointer_type()
        id_token = self.expect('IDENTIFICADOR')

        array_sizes = []
        while self.current_token() and self.current_token()['valor'] == '[':
            self.expect('SEPARADOR', '[')
            size_token = self.expect('NUMERO') if self.current_token() and self.current_token()['tipo'] == 'NUMERO' else None
            self.expect('SEPARADOR', ']')
            array_sizes.append(Node('Tamanho do Array', value=size_token['valor'] if size_token else None))
        
        init_expr = None
        if self.current_token() and self.current_token()['valor'] == '=':
            self.expect('OPERADOR', '=')
            init_expr = self.parse_expression()
        
        self.expect('SEPARADOR', ';')

        declaration = Node('Declaração', [
            Node('Tipo', value=base_type['valor']),
            *[Node('Ponteiro') for _ in pointers],
            Node('Identificador', value=id_token['valor'])
        ])
        if array_sizes:
            declaration.children.append(Node('Dimensão do Array', array_sizes))
        if init_expr:
            declaration.children.append(Node('Inicialização', [init_expr]))
        
        return declaration

    def parse_assignment_or_expression(self):
        left = self.parse_expression()
        
        token = self.current_token()
        if token and token['tipo'] == 'OPERADOR' and token['valor'] in {
            '=', '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '<<=', '>>='
        }:
            op_token = self.expect('OPERADOR')
            right = self.parse_expression()
            self.expect('SEPARADOR', ';')
            return Node('Atribuição', [
                left,
                Node('Operador', value=op_token['valor']),
                right
            ])
        else:
            self.expect('SEPARADOR', ';')
            return left

    
    def parse_expression(self):
        return self.parse_ternary_expression()

    def parse_ternary_expression(self):
        condition = self.parse_logical_or_expression()
        
        if self.current_token() and self.current_token()['valor'] == '?':
            self.expect('OPERADOR', '?')
            true_expr = self.parse_expression()
            self.expect('OPERADOR', ':')
            false_expr = self.parse_ternary_expression()
            
            return Node('Operação Ternária', [
                condition,
                true_expr,
                false_expr
            ])
        
        return condition

    def parse_logical_or_expression(self):
        left = self.parse_logical_and_expression()
        
        while self.current_token() and self.current_token()['valor'] == '||':
            op_token = self.expect('OPERADOR')
            right = self.parse_logical_and_expression()
            left = Node('Operação OR Lógico', [
                left,
                Node('Operador', value=op_token['valor']),
                right
            ])
            
        return left

    def parse_logical_and_expression(self):
        left = self.parse_bitwise_or_expression()
        
        while self.current_token() and self.current_token()['valor'] == '&&':
            op_token = self.expect('OPERADOR')
            right = self.parse_bitwise_or_expression()
            left = Node('Operação AND Lógico', [
                left,
                Node('Operador', value=op_token['valor']),
                right
            ])
            
        return left

    def parse_bitwise_or_expression(self):
        left = self.parse_bitwise_xor_expression()
        
        while self.current_token() and self.current_token()['valor'] == '|':
            next_token = self.tokens[self.position + 1] if self.position + 1 < len(self.tokens) else None
            if next_token and next_token['valor'] == '|':
                break
                
            op_token = self.expect('OPERADOR')
            right = self.parse_bitwise_xor_expression()
            left = Node('Operador Bitwise Or', [
                left,
                Node('Operador', value=op_token['valor']),
                right
            ])
            
        return left

    def parse_bitwise_xor_expression(self):
        left = self.parse_bitwise_and_expression()
        
        while self.current_token() and self.current_token()['valor'] == '^':
            op_token = self.expect('OPERADOR')
            right = self.parse_bitwise_and_expression()
            left = Node('Operador Bitwise Xor', [
                left,
                Node('Operador', value=op_token['valor']),
                right
            ])
            
        return left

    def parse_bitwise_and_expression(self):
        left = self.parse_equality_expression()
        
        while self.current_token() and self.current_token()['valor'] == '&':
            next_token = self.tokens[self.position + 1] if self.position + 1 < len(self.tokens) else None
            if next_token and next_token['valor'] == '&':
                break
                
            op_token = self.expect('OPERADOR')
            right = self.parse_equality_expression()
            left = Node('Operador Bitwise And', [
                left,
                Node('Operador', value=op_token['valor']),
                right
            ])
            
        return left

    def parse_equality_expression(self):
        left = self.parse_relational_expression()
        
        while self.current_token() and self.current_token()['valor'] in {'==', '!='}:
            op_token = self.expect('OPERADOR')
            right = self.parse_relational_expression()
            left = Node('Operação Binária', [
                left,
                Node('Operador', value=op_token['valor']),
                right
            ])
            
        return left

    def parse_relational_expression(self):
        left = self.parse_additive_expression()
        
        while self.current_token() and self.current_token()['valor'] in {'<', '>', '<=', '>='}:
            op_token = self.expect('OPERADOR')
            right = self.parse_additive_expression()
            left = Node('Operação Binária', [
                left,
                Node('Operador', value=op_token['valor']),
                right
            ])
            
        return left

    def parse_additive_expression(self):
        left = self.parse_multiplicative_expression()
        
        while self.current_token() and self.current_token()['valor'] in {'+', '-'}:
            op_token = self.expect('OPERADOR')
            right = self.parse_multiplicative_expression()
            left = Node('Operação Binária', [
                left,
                Node('Operador', value=op_token['valor']),
                right
            ])
            
        return left
    
    def parse_increment_decrement(self):
        token = self.current_token()
        if token is None or token['tipo'] != 'OPERADOR' or token['valor'] not in {'++', '--'}:
            return None
        
        next_token = self.tokens[self.position + 1] if self.position + 1 < len(self.tokens) else None
        prev_token = self.tokens[self.position - 1] if self.position > 0 else None
        
        if (next_token and next_token['tipo'] == 'IDENTIFICADOR') or \
        (next_token and next_token['valor'] == '(' and self.position + 2 < len(self.tokens) and \
        self.tokens[self.position + 2]['tipo'] == 'IDENTIFICADOR'):
            op_token = self.expect('OPERADOR')
            operand = self.parse_primary_expression()
            return Node('Incremento Decremento Prefixo', [
                Node('Operador', value=op_token['valor']),
                operand
            ])
        elif prev_token and prev_token['tipo'] == 'IDENTIFICADOR':
            operand = Node('Identifier', value=prev_token['valor'])
            self.position -= 1 
            operand = self.parse_primary_expression() 
            op_token = self.expect('OPERADOR')
            return Node('Incremento Decremento Posfixo', [
                operand,
                Node('Operador', value=op_token['valor'])
            ])
        else:
            self.errors.append({
                'mensagem': f"Operador de incremento/decremento mal posicionado: '{token['valor']}'",
                'linha': token['linha'],
                'coluna': token['coluna']
            })
            self.advance()
            return Node('Expressão', value='ERROR')

    def parse_multiplicative_expression(self):
        left = self.parse_unary_expression()
        
        while self.current_token() and self.current_token()['valor'] in {'*', '/', '%'}:
            op_token = self.expect('OPERADOR')
            right = self.parse_unary_expression()
            left = Node('Operação Binária', [
                left,
                Node('Operador', value=op_token['valor']),
                right
            ])
            
        return left

    def parse_unary_expression(self):
        token = self.current_token()
        if token and token['tipo'] == 'OPERADOR':
            if token['valor'] in {'*', '&'}:
                op_token = self.expect('OPERADOR')
                operand = self.parse_unary_expression()
                return Node('Operação Unária', [
                    Node('Operador', value=op_token['valor']),
                    operand
                ])
            elif token['valor'] in {'++', '--'}:
                return self.parse_increment_decrement()
            elif token['valor'] in {'+', '-', '!', '~'}:
                op_token = self.expect('OPERADOR')
                operand = self.parse_unary_expression()
                return Node('Operação Unária', [
                    Node('Operador', value=op_token['valor']),
                    operand
                ])
        if token and token['valor'] == '(':
            self.expect('SEPARADOR', '(')
            expr = self.parse_expression()
            self.expect('SEPARADOR', ')')
            return expr
        
        return self.parse_primary_expression()

    def parse_primary_expression(self):
        token = self.current_token()
        if token is None:
            self.errors.append({
                'mensagem': "Expressão esperada mas não encontrada",
                'linha': 'EOF',
                'coluna': 'EOF'
            })
            return Node('Expressão', value='ERROR')

        if token['tipo'] == 'NUMERO':
            self.advance()
            return Node('Número', value=token['valor'])
        elif token['tipo'] == 'IDENTIFICADOR':
            next_token = self.tokens[self.position + 1] if self.position + 1 < len(self.tokens) else None
            if next_token and next_token['valor'] == '(':
                return self.parse_function_call()
            else:
                if next_token and next_token['valor'] in {'++', '--'}:
                    ident = self.expect('IDENTIFICADOR')
                    op = self.expect('OPERADOR')
                    return Node('Incremento Decremento Posfixo', [
                        Node('Identificador', value=ident['valor']),
                        Node('Operador', value=op['valor'])
                    ])
                else:
                    self.advance()
                    return Node('Identificador', value=token['valor'])
        elif token['tipo'] == 'TEXTO':
            self.advance()
            return Node('String', value=token['valor'])
        else:
            self.errors.append({
                'mensagem': f"Expressão inválida iniciando com '{token['valor']}'",
                'linha': token['linha'],
                'coluna': token['coluna']
            })
            self.advance()
            return Node('Expressão', value='ERROR')

    def parse_function_call(self):
        func_name = self.expect('IDENTIFICADOR')
        self.expect('SEPARADOR', '(')
        
        arguments = []
        while self.current_token() and self.current_token()['valor'] != ')':
            arg = self.parse_expression()
            arguments.append(arg)
            if self.current_token() and self.current_token()['valor'] == ',':
                self.expect('SEPARADOR', ',')
        
        self.expect('SEPARADOR', ')')
        
        return Node('Chamada de Função', [
            Node('Nome da Função', value=func_name['valor']),
            Node('Argumentos', arguments)
        ])

    def parse_if_statement(self):
        self.expect('PALAVRA_CHAVE', 'if')
        self.expect('SEPARADOR', '(')
        condition = self.parse_expression()
        self.expect('SEPARADOR', ')')
        
        then_branch = self.parse_statement()
        
        else_branch = None
        if self.current_token() and self.current_token()['valor'] == 'else':
            self.expect('PALAVRA_CHAVE', 'else')
            else_branch = self.parse_statement()
            
        return Node('Declaração if', [
            condition,
            then_branch,
            else_branch if else_branch else Node('Else vazio')
        ])

    def parse_while_loop(self):
        self.expect('PALAVRA_CHAVE', 'while')
        self.expect('SEPARADOR', '(')
        condition = self.parse_expression()
        self.expect('SEPARADOR', ')')
        
        body = self.parse_statement()
        
        return Node('WhileLoop', [
            condition,
            body
        ])

    def parse_do_while_loop(self):
        self.expect('PALAVRA_CHAVE', 'do')
        body = self.parse_statement()
        self.expect('PALAVRA_CHAVE', 'while')
        self.expect('SEPARADOR', '(')
        condition = self.parse_expression()
        self.expect('SEPARADOR', ')')
        self.expect('SEPARADOR', ';')
        
        return Node('DoWhileLoop', [
            body,
            condition
        ])

    def parse_for_loop(self):
        self.expect('PALAVRA_CHAVE', 'for')
        self.expect('SEPARADOR', '(')

        init = None
        if self.current_token() and self.current_token()['valor'] != ';':
            if self.current_token()['tipo'] == 'PALAVRA_CHAVE' and self.current_token()['valor'] in {
                'int', 'float', 'char', 'double', 'long', 'short', 'unsigned'
            }:
                init = self.parse_declaration()
            else:
                init = self.parse_assignment_or_expression()
                if self.current_token() and self.current_token()['valor'] == ';':
                    self.expect('SEPARADOR', ';')
        else:
            self.expect('SEPARADOR', ';')

        condition = None
        if self.current_token() and self.current_token()['valor'] != ';':
            condition = self.parse_expression()
        self.expect('SEPARADOR', ';')

        increment = None
        if self.current_token() and self.current_token()['valor'] != ')':
            increment = self.parse_expression()
        self.expect('SEPARADOR', ')')
        
        body = self.parse_statement()
        
        return Node('ForLoop', [
            init if init else Node('Inicialização for vazia'),
            condition if condition else Node('Condição for vazia'),
            increment if increment else Node('Incremento for vazio'),
            body
        ])

    def parse_return_statement(self):
        self.expect('PALAVRA_CHAVE', 'return')
        expr = None
        if self.current_token() and self.current_token()['valor'] != ';':
            expr = self.parse_expression()
        self.expect('SEPARADOR', ';')
        
        return Node('Declaração Return', [expr] if expr else [])
    
    def parse_comment(self):
        token = self.current_token()
        if token and token['tipo'] == 'COMENTARIO':
            self.advance()
            return Node('Comentário', value=token['valor'])
        return None