from ast_nodes_v2 import *

class CompileError(Exception):
    def __init__(self, message, line=0, column=0, source_line=""):
        self.message = message
        self.line = line
        self.column = column
        self.source_line = source_line
        super().__init__(f"Error at {line}:{column}: {message}")

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[0] if tokens else None

    def advance(self):
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
            self.current_token = self.tokens[self.pos]
        return self.tokens[self.pos - 1] if self.pos > 0 else self.current_token

    def peek(self, offset=1):
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else self.tokens[-1]

    def expect(self, token_type):
        if self.current_token.type != token_type:
            raise CompileError(
                f"Expected '{token_type}' but got '{self.current_token.type}'",
                self.current_token.line,
                self.current_token.column
            )
        token = self.current_token
        self.advance()
        return token

    def match(self, *types):
        return self.current_token.type in types

    def parse(self):
        declarations = []
        while not self.match("EOF"):
            if self.match("STRUCT"):
                declarations.append(self.parse_struct())
            else:
                declarations.append(self.parse_function())
        return Program(declarations)

    # ── Type Parsing ──────────────────────────────────

    def parse_type(self):
        """Parse a type like: int, float, int*, int[], struct Node, etc."""
        if self.match("STRUCT"):
            self.advance()
            struct_name = self.expect("ID").value
            type_node = TypeNode(base_type="struct", struct_name=struct_name)
        elif self.match("INT", "FLOAT", "CHAR", "VOID"):
            type_node = TypeNode(base_type=self.current_token.value)
            self.advance()
        else:
            raise CompileError(
                "Expected type name",
                self.current_token.line,
                self.current_token.column
            )

        # Parse pointers
        pointers = 0
        while self.match("MUL") or self.match("AMP"):
            if self.match("MUL"):
                pointers += 1
                self.advance()
            elif self.match("AMP"):
                pointers += 1
                self.advance()

        type_node.pointers = pointers
        
        # Parse array dimensions
        while self.match("LBRACKET"):
            self.advance()
            if self.match("RBRACKET"):
                type_node.array_dims.append(0)  # Unsized array
            else:
                # Parse dimension (must be constant)
                if not self.match("NUMBER"):
                    raise CompileError(
                        "Array dimension must be a constant",
                        self.current_token.line,
                        self.current_token.column
                    )
                dim = int(self.current_token.value)
                type_node.array_dims.append(dim)
                self.advance()
            self.expect("RBRACKET")

        return type_node

    # ── Struct Parsing ────────────────────────────────

    def parse_struct(self):
        line = self.current_token.line
        self.expect("STRUCT")
        name = self.expect("ID").value
        self.expect("LBRACE")

        members = []
        while not self.match("RBRACE", "EOF"):
            member_type = self.parse_type()
            member_name = self.expect("ID").value
            members.append((member_type, member_name))
            self.expect("SEMI")

        self.expect("RBRACE")
        self.expect("SEMI")
        return StructDecl(name, members, line)

    # ── Function Parsing ──────────────────────────────

    def parse_function(self):
        line = self.current_token.line
        return_type = self.parse_type()
        func_name = self.expect("ID").value
        self.expect("LPAREN")

        params = []
        if not self.match("RPAREN"):
            while True:
                param_type = self.parse_type()
                param_name = self.expect("ID").value
                params.append((param_type, param_name))
                if not self.match("COMMA"):
                    break
                self.advance()

        self.expect("RPAREN")
        body = self.parse_block()

        return FuncDecl(return_type, func_name, params, body, line)

    # ── Statement Parsing ─────────────────────────────

    def parse_block(self):
        line = self.current_token.line
        self.expect("LBRACE")
        statements = []

        while not self.match("RBRACE", "EOF"):
            statements.append(self.parse_statement())

        self.expect("RBRACE")
        return Block(statements, line)

    def parse_statement(self):
        if self.match("IF"):
            return self.parse_if()
        elif self.match("WHILE"):
            return self.parse_while()
        elif self.match("DO"):
            return self.parse_do_while()
        elif self.match("FOR"):
            return self.parse_for()
        elif self.match("RETURN"):
            return self.parse_return()
        elif self.match("BREAK"):
            line = self.current_token.line
            self.advance()
            self.expect("SEMI")
            return BreakStmt(line)
        elif self.match("CONTINUE"):
            line = self.current_token.line
            self.advance()
            self.expect("SEMI")
            return ContinueStmt(line)
        elif self.match("LBRACE"):
            return self.parse_block()
        elif self.match("INT", "FLOAT", "CHAR", "VOID", "STRUCT"):
            return self.parse_var_decl()
        else:
            return self.parse_expr_stmt()

    def parse_var_decl(self):
        line = self.current_token.line
        type_node = self.parse_type()
        name = self.expect("ID").value
        value = None

        if self.match("ASSIGN"):
            self.advance()
            value = self.parse_expr()

        self.expect("SEMI")
        return VarDecl(type_node, name, value, line)

    def parse_if(self):
        line = self.current_token.line
        self.expect("IF")
        self.expect("LPAREN")
        condition = self.parse_expr()
        self.expect("RPAREN")
        body = self.parse_block()

        else_body = None
        if self.match("ELSE"):
            self.advance()
            if self.match("IF"):
                else_body = Block([self.parse_if()], line)
            else:
                else_body = self.parse_block()

        return IfStmt(condition, body, else_body, line)

    def parse_while(self):
        line = self.current_token.line
        self.expect("WHILE")
        self.expect("LPAREN")
        condition = self.parse_expr()
        self.expect("RPAREN")
        body = self.parse_block()
        return WhileStmt(condition, body, line)

    def parse_do_while(self):
        line = self.current_token.line
        self.expect("DO")
        body = self.parse_block()
        self.expect("WHILE")
        self.expect("LPAREN")
        condition = self.parse_expr()
        self.expect("RPAREN")
        self.expect("SEMI")
        return DoWhileStmt(body, condition, line)

    def parse_for(self):
        line = self.current_token.line
        self.expect("FOR")
        self.expect("LPAREN")

        # Init
        init = None
        if self.match("INT", "FLOAT", "CHAR", "VOID"):
            init = self.parse_var_decl()
        elif not self.match("SEMI"):
            init = self.parse_expr_stmt()
        else:
            self.advance()

        # Condition
        condition = None
        if not self.match("SEMI"):
            condition = self.parse_expr()
        self.expect("SEMI")

        # Increment
        increment = None
        if not self.match("RPAREN"):
            increment = self.parse_expr()
        self.expect("RPAREN")

        body = self.parse_block()
        return ForStmt(init, condition, increment, body, line)

    def parse_return(self):
        line = self.current_token.line
        self.expect("RETURN")
        value = None
        if not self.match("SEMI"):
            value = self.parse_expr()
        self.expect("SEMI")
        return ReturnStmt(value, line)

    def parse_expr_stmt(self):
        expr = self.parse_expr()
        self.expect("SEMI")
        return expr

    # ── Expression Parsing (with correct precedence) ────

    def parse_expr(self):
        return self.parse_ternary()

    def parse_ternary(self):
        expr = self.parse_logical_or()
        if self.match("QUESTION"):
            self.advance()
            true_expr = self.parse_expr()
            self.expect("COLON")
            false_expr = self.parse_expr()
            return TernaryOp(expr, true_expr, false_expr)
        return expr

    def parse_logical_or(self):
        left = self.parse_logical_and()
        while self.match("OR"):
            op = self.current_token.value
            self.advance()
            right = self.parse_logical_and()
            left = BinOp(left, op, right)
        return left

    def parse_logical_and(self):
        left = self.parse_equality()
        while self.match("AND"):
            op = self.current_token.value
            self.advance()
            right = self.parse_equality()
            left = BinOp(left, op, right)
        return left

    def parse_equality(self):
        left = self.parse_relational()
        while self.match("EQ", "NEQ"):
            op = self.current_token.value
            self.advance()
            right = self.parse_relational()
            left = BinOp(left, op, right)
        return left

    def parse_relational(self):
        left = self.parse_additive()
        while self.match("LT", "GT", "LE", "GE"):
            op = self.current_token.value
            self.advance()
            right = self.parse_additive()
            left = BinOp(left, op, right)
        return left

    def parse_additive(self):
        left = self.parse_term()
        while self.match("PLUS", "MINUS"):
            op = self.current_token.value
            self.advance()
            right = self.parse_term()
            left = BinOp(left, op, right)
        return left

    def parse_term(self):
        left = self.parse_unary()
        while self.match("MUL", "DIV", "MOD"):
            op = self.current_token.value
            self.advance()
            right = self.parse_unary()
            left = BinOp(left, op, right)
        return left

    def parse_unary(self):
        if self.match("NOT", "MINUS", "PLUS"):
            op = self.current_token.value
            self.advance()
            operand = self.parse_unary()
            return UnaryOp(op, operand)
        elif self.match("MUL"):  # Pointer dereference
            self.advance()
            operand = self.parse_unary()
            return PointerDeref(operand)
        elif self.match("AMP"):  # Address-of
            self.advance()
            operand = self.parse_unary()
            return AddressOf(operand)
        elif self.match("INC", "DEC"):
            op = self.current_token.value
            self.advance()
            operand = self.parse_unary()
            return UnaryOp(op, operand, is_postfix=False)
        elif self.match("SIZEOF"):
            self.advance()
            self.expect("LPAREN")
            if self.match("INT", "FLOAT", "CHAR", "VOID", "STRUCT"):
                type_node = self.parse_type()
                self.expect("RPAREN")
                return SizeOf(type_node, is_type=True)
            else:
                expr = self.parse_expr()
                self.expect("RPAREN")
                return SizeOf(expr, is_type=False)
        else:
            return self.parse_postfix()

    def parse_postfix(self):
        expr = self.parse_primary()

        while True:
            if self.match("LBRACKET"):  # Array access
                self.advance()
                index = self.parse_expr()
                self.expect("RBRACKET")
                expr = ArrayAccess(expr, index)

            elif self.match("DOT"):  # Member access
                self.advance()
                member = self.expect("ID").value
                expr = MemberAccess(expr, member, is_pointer=False)

            elif self.match("ARROW"):  # Pointer member access
                self.advance()
                member = self.expect("ID").value
                expr = MemberAccess(expr, member, is_pointer=True)

            elif self.match("INC", "DEC"):  # Postfix ++ and --
                op = self.current_token.value
                self.advance()
                expr = UnaryOp(op, expr, is_postfix=True)

            elif self.match("ASSIGN", "PLUS_ASSIGN", "MINUS_ASSIGN", "MUL_ASSIGN", "DIV_ASSIGN"):
                if isinstance(expr, Identifier):
                    op = self.current_token.value
                    self.advance()
                    value = self.parse_expr()
                    # Remove the '=' from compound operators
                    op = op.rstrip("=") if op.endswith("=") and op != "=" else op
                    return Assign(expr.name, value, op, expr.line)
                else:
                    raise CompileError(
                        "Invalid assignment target",
                        self.current_token.line,
                        self.current_token.column
                    )

            else:
                break

        return expr

    def parse_primary(self):
        tok = self.current_token

        # String literal
        if tok.type == "STRING":
            self.advance()
            return StringLiteral(tok.value, tok.line, tok.column)

        # Character literal
        if tok.type == "CHAR_LIT":
            self.advance()
            return CharLiteral(tok.value, tok.line, tok.column)

        # Number
        if tok.type in ("NUMBER", "FLOAT_NUM"):
            self.advance()
            return Number(tok.value, tok.line, tok.column)

        # Identifier or function call
        if tok.type == "ID":
            self.advance()
            if self.match("LPAREN"):  # Function call
                self.advance()
                args = []
                if not self.match("RPAREN"):
                    args.append(self.parse_expr())
                    while self.match("COMMA"):
                        self.advance()
                        args.append(self.parse_expr())
                self.expect("RPAREN")
                return FuncCall(tok.value, args, tok.line, tok.column)
            else:
                return Identifier(tok.value, tok.line, tok.column)

        # Parenthesized expression
        if tok.type == "LPAREN":
            self.advance()
            expr = self.parse_expr()
            self.expect("RPAREN")
            return expr

        raise CompileError(
            f"Unexpected token '{tok.value}'",
            tok.line,
            tok.column
        )
