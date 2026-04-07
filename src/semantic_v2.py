from ast_nodes_v2 import *

class Symbol:
    def __init__(self, name, type_node, scope_level, line, column):
        self.name = name
        self.type_node = type_node
        self.scope_level = scope_level
        self.line = line
        self.column = column
        self.is_function = False
        self.param_types = []

class SymbolTable:
    def __init__(self):
        self.scopes = [{}]

    def push_scope(self):
        self.scopes.append({})

    def pop_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()

    def declare(self, name, type_node, line, column):
        current = self.scopes[-1]
        if name in current:
            raise SemanticError(
                f"'{name}' already declared in this scope",
                line, column,
                f"Previous declaration at line {current[name].line}"
            )
        current[name] = Symbol(name, type_node, len(self.scopes) - 1, line, column)

    def lookup(self, name, line, column):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise SemanticError(
            f"'{name}' is not declared",
            line, column,
            "Did you forget to declare this variable?"
        )

class SemanticError(Exception):
    def __init__(self, message, line=0, column=0, hint=""):
        self.message = message
        self.line = line
        self.column = column
        self.hint = hint
        super().__init__(f"Semantic Error at {line}:{column}: {message}\n  Hint: {hint}" if hint else f"Semantic Error at {line}:{column}: {message}")

class SemanticAnalyser:
    def __init__(self):
        self.symbols = SymbolTable()
        self.functions = {}
        self.structs = {}
        self.errors = []
        self.current_return_type = None
        self.in_loop = False
        self.init_stdlib()

    def init_stdlib(self):
        """Initialize standard library functions"""
        self.stdlib_functions = {
            "print": (TypeNode("void"), [TypeNode("any")]),
            "printf": (TypeNode("int"), [TypeNode("any")]),  # Variable args
            "scanf": (TypeNode("int"), [TypeNode("any")]),
            "strlen": (TypeNode("int"), [TypeNode("char", pointers=1)]),
            "strcmp": (TypeNode("int"), [TypeNode("char", pointers=1), TypeNode("char", pointers=1)]),
            "strcpy": (TypeNode("char", pointers=1), [TypeNode("char", pointers=1), TypeNode("char", pointers=1)]),
            "malloc": (TypeNode("any", pointers=1), [TypeNode("int")]),
            "free": (TypeNode("void"), [TypeNode("any", pointers=1)]),
            "abs": (TypeNode("int"), [TypeNode("int")]),
            "sqrt": (TypeNode("float"), [TypeNode("float")]),
            "pow": (TypeNode("float"), [TypeNode("float"), TypeNode("float")]),
            "sin": (TypeNode("float"), [TypeNode("float")]),
            "cos": (TypeNode("float"), [TypeNode("float")]),
            "getchar": (TypeNode("int"), []),
            "putchar": (TypeNode("int"), [TypeNode("int")]),
        }

    def analyse(self, program):
        """Main analysis entry point"""
        # First pass: register structs and functions
        for decl in program.declarations:
            if isinstance(decl, StructDecl):
                self._register_struct(decl)
            elif isinstance(decl, FuncDecl):
                self._register_function(decl)

        # Second pass: analyze functions
        for decl in program.declarations:
            if isinstance(decl, FuncDecl):
                self._analyse_function(decl)

        if self.errors:
            error_msg = "Semantic Analysis Failed:\n"
            for e in self.errors:
                error_msg += f"\n  {e}"
            raise SemanticError(error_msg)

    def _register_struct(self, node):
        if node.name in self.structs:
            self.errors.append(SemanticError(f"Struct '{node.name}' already defined", node.line, 0))
            return
        self.structs[node.name] = node.members

    def _register_function(self, node):
        if node.name in self.functions:
            self.errors.append(SemanticError(
                f"Function '{node.name}' already defined",
                node.line, 0,
                f"Previous definition at line {self.functions[node.name]['line']}"
            ))
            return

        param_types = [ptype for ptype, _ in node.params]
        self.functions[node.name] = {
            'return_type': node.return_type_node,
            'param_types': param_types,
            'line': node.line
        }

    def _analyse_function(self, node):
        self.current_return_type = node.return_type_node
        self.symbols.push_scope()

        # Declare parameters
        for param_type, param_name in node.params:
            try:
                self.symbols.declare(param_name, param_type, node.line, 0)
            except SemanticError as e:
                self.errors.append(e)

        # Analyze body
        try:
            self._analyse_block(node.body)
        except SemanticError as e:
            self.errors.append(e)

        self.symbols.pop_scope()

    def _analyse_block(self, block):
        for stmt in block.statements:
            self._analyse_stmt(stmt)

    def _analyse_stmt(self, node):
        try:
            if isinstance(node, VarDecl):
                self._analyse_var_decl(node)
            elif isinstance(node, Assign):
                self._analyse_assign(node)
            elif isinstance(node, IfStmt):
                self._analyse_if(node)
            elif isinstance(node, WhileStmt):
                self._analyse_while(node)
            elif isinstance(node, DoWhileStmt):
                self._analyse_do_while(node)
            elif isinstance(node, ForStmt):
                self._analyse_for(node)
            elif isinstance(node, ReturnStmt):
                self._analyse_return(node)
            elif isinstance(node, BreakStmt):
                if not self.in_loop:
                    raise SemanticError("'break' can only be used in loops", node.line, 0)
            elif isinstance(node, ContinueStmt):
                if not self.in_loop:
                    raise SemanticError("'continue' can only be used in loops", node.line, 0)
            elif isinstance(node, FuncCall):
                self._analyse_func_call(node)
            elif isinstance(node, Block):
                self.symbols.push_scope()
                self._analyse_block(node)
                self.symbols.pop_scope()
            else:
                self._analyse_expr(node)
        except SemanticError as e:
            if e not in self.errors:
                self.errors.append(e)

    def _analyse_var_decl(self, node):
        if node.value:
            val_type = self._analyse_expr(node.value)
            self._check_assignment_compat(node.type_node, val_type, node.line, node.column)

        try:
            self.symbols.declare(node.name, node.type_node, node.line, node.column)
        except SemanticError as e:
            self.errors.append(e)

    def _analyse_assign(self, node):
        try:
            sym = self.symbols.lookup(node.name, node.line, node.column)
            val_type = self._analyse_expr(node.value)
            self._check_assignment_compat(sym.type_node, val_type, node.line, node.column)
        except SemanticError as e:
            self.errors.append(e)

    def _analyse_if(self, node):
        try:
            self._analyse_expr(node.condition)
            self.symbols.push_scope()
            self._analyse_block(node.body)
            self.symbols.pop_scope()

            if node.else_body:
                self.symbols.push_scope()
                self._analyse_block(node.else_body)
                self.symbols.pop_scope()
        except SemanticError as e:
            self.errors.append(e)

    def _analyse_while(self, node):
        try:
            self._analyse_expr(node.condition)
            old_in_loop = self.in_loop
            self.in_loop = True
            self.symbols.push_scope()
            self._analyse_block(node.body)
            self.symbols.pop_scope()
            self.in_loop = old_in_loop
        except SemanticError as e:
            self.errors.append(e)

    def _analyse_do_while(self, node):
        try:
            old_in_loop = self.in_loop
            self.in_loop = True
            self.symbols.push_scope()
            self._analyse_block(node.body)
            self.symbols.pop_scope()
            self._analyse_expr(node.condition)
            self.in_loop = old_in_loop
        except SemanticError as e:
            self.errors.append(e)

    def _analyse_for(self, node):
        try:
            self.symbols.push_scope()

            if node.init:
                self._analyse_stmt(node.init)
            if node.condition:
                self._analyse_expr(node.condition)
            if node.increment:
                self._analyse_expr(node.increment)

            old_in_loop = self.in_loop
            self.in_loop = True
            self._analyse_block(node.body)
            self.in_loop = old_in_loop

            self.symbols.pop_scope()
        except SemanticError as e:
            self.errors.append(e)

    def _analyse_return(self, node):
        try:
            if node.value:
                val_type = self._analyse_expr(node.value)
                self._check_assignment_compat(self.current_return_type, val_type, node.line, node.column)
        except SemanticError as e:
            self.errors.append(e)

    def _analyse_expr(self, node):
        if isinstance(node, StringLiteral):
            return TypeNode("char", pointers=1)  # String is char*

        elif isinstance(node, CharLiteral):
            return TypeNode("char")

        elif isinstance(node, Number):
            return TypeNode("float" if isinstance(node.value, float) else "int")

        elif isinstance(node, Identifier):
            try:
                sym = self.symbols.lookup(node.name, node.line, node.column)
                return sym.type_node
            except SemanticError as e:
                self.errors.append(e)
                return TypeNode("int")  # Default fallback

        elif isinstance(node, BinOp):
            left = self._analyse_expr(node.left)
            right = self._analyse_expr(node.right)
            # Return float if either operand is float
            if left and right:
                if left.base_type == "float" or right.base_type == "float":
                    return TypeNode("float")
            return left or right

        elif isinstance(node, UnaryOp):
            operand_type = self._analyse_expr(node.operand)
            if node.op in ("++", "--"):
                if not isinstance(node.operand, Identifier):
                    self.errors.append(SemanticError(
                        f"Can only apply '{node.op}' to variables",
                        node.line, node.column
                    ))
            return operand_type

        elif isinstance(node, ArrayAccess):
            arr_type = self._analyse_expr(node.array)
            self._analyse_expr(node.index)
            # Return the base type (remove one array dimension)
            if arr_type and arr_type.array_dims:
                new_dims = arr_type.array_dims[1:]
                return TypeNode(arr_type.base_type, arr_type.pointers, new_dims)
            return arr_type

        elif isinstance(node, MemberAccess):
            obj_type = self._analyse_expr(node.obj)
            if obj_type and obj_type.base_type == "struct":
                if obj_type.struct_name not in self.structs:
                    self.errors.append(SemanticError(
                        f"Undefined struct '{obj_type.struct_name}'",
                        node.line, node.column
                    ))
                    return TypeNode("int")
                # Find member in struct
                for mtype, mname in self.structs[obj_type.struct_name]:
                    if mname == node.member:
                        return mtype
                self.errors.append(SemanticError(
                    f"Struct has no member '{node.member}'",
                    node.line, node.column
                ))
            return TypeNode("int")

        elif isinstance(node, AddressOf):
            expr_type = self._analyse_expr(node.expr)
            if expr_type:
                result = TypeNode(expr_type.base_type, expr_type.pointers + 1, expr_type.array_dims)
                return result
            return TypeNode("int", pointers=1)

        elif isinstance(node, PointerDeref):
            expr_type = self._analyse_expr(node.expr)
            if expr_type and expr_type.pointers > 0:
                result = TypeNode(expr_type.base_type, expr_type.pointers - 1, expr_type.array_dims)
                return result
            return TypeNode("int")

        elif isinstance(node, FuncCall):
            return self._analyse_func_call(node)

        elif isinstance(node, TernaryOp):
            self._analyse_expr(node.condition)
            true_type = self._analyse_expr(node.true_expr)
            false_type = self._analyse_expr(node.false_expr)
            return true_type  # Simplified: return true branch type

        elif isinstance(node, Cast):
            self._analyse_expr(node.expr)
            return node.type_node

        elif isinstance(node, SizeOf):
            return TypeNode("int")

        return None

    def _analyse_func_call(self, node):
        # Check stdlib functions
        if node.name in self.stdlib_functions:
            return_type, _ = self.stdlib_functions[node.name]
            return return_type

        # Check user-defined functions
        if node.name not in self.functions:
            self.errors.append(SemanticError(
                f"Undefined function '{node.name}'",
                node.line, node.column,
                f"Did you mean to define '{node.name}'?"
            ))
            return TypeNode("int")

        func_info = self.functions[node.name]
        param_types = func_info['param_types']

        if len(node.args) != len(param_types):
            self.errors.append(SemanticError(
                f"Function '{node.name}' expects {len(param_types)} arguments, got {len(node.args)}",
                node.line, node.column,
                f"Function signature: ({', '.join(str(t) for t in param_types)})"
            ))

        for arg in node.args:
            self._analyse_expr(arg)

        return func_info['return_type']

    def _check_assignment_compat(self, target_type, source_type, line, column):
        """Check if source can be assigned to target"""
        if not target_type or not source_type:
            return

        # Allow any to int/float conversion
        if source_type.base_type == "any":
            return

        # Exact match
        if target_type.base_type == source_type.base_type and \
           target_type.pointers == source_type.pointers and \
           target_type.array_dims == source_type.array_dims:
            return

        # Allow int/float conversion
        if target_type.base_type in ("int", "float") and source_type.base_type in ("int", "float"):
            return

        # Allow pointer assignments
        if target_type.pointers > 0 and source_type.pointers > 0:
            return

        self.errors.append(SemanticError(
            f"Cannot assign '{source_type}' to '{target_type}'",
            line, column,
            "Check your variable types and ensure they are compatible"
        ))
