class ASTNode:
    """Base class for all AST nodes with location tracking"""
    def __init__(self, line=0, column=0):
        self.line = line
        self.column = column

# ── Types ───────────────────────────────────────────────

class TypeNode(ASTNode):
    """Represents a type (int, float, int[], int*, struct Node, etc.)"""
    def __init__(self, base_type, pointers=0, array_dims=None, struct_name=None):
        super().__init__()
        self.base_type = base_type      # "int", "float", "char", "void", "struct_name"
        self.pointers = pointers         # 0, 1, 2, etc. for *, **, etc.
        self.array_dims = array_dims or []  # [10, 20] for int[10][20]
        self.struct_name = struct_name   # For struct types
    
    def __str__(self):
        s = self.base_type
        s += "*" * self.pointers
        for dim in self.array_dims:
            s += f"[{dim}]"
        return s
    
    def is_pointer(self):
        return self.pointers > 0
    
    def is_array(self):
        return len(self.array_dims) > 0

# ── Expressions ──────────────────────────────────────────

class Number(ASTNode):
    def __init__(self, value, line=0, column=0):
        super().__init__(line, column)
        self.value = value

class StringLiteral(ASTNode):
    def __init__(self, value, line=0, column=0):
        super().__init__(line, column)
        self.value = value

class CharLiteral(ASTNode):
    def __init__(self, value, line=0, column=0):
        super().__init__(line, column)
        self.value = value

class Identifier(ASTNode):
    def __init__(self, name, line=0, column=0):
        super().__init__(line, column)
        self.name = name

class BinOp(ASTNode):
    def __init__(self, left, op, right, line=0, column=0):
        super().__init__(line, column)
        self.left = left
        self.op = op
        self.right = right

class UnaryOp(ASTNode):
    def __init__(self, op, operand, is_postfix=False, line=0, column=0):
        super().__init__(line, column)
        self.op = op
        self.operand = operand
        self.is_postfix = is_postfix  # For ++ and --

class Assign(ASTNode):
    def __init__(self, name, value, op="=", line=0, column=0):
        super().__init__(line, column)
        self.name = name
        self.value = value
        self.op = op  # "=", "+=", "-=", etc.

class ArrayAccess(ASTNode):
    def __init__(self, array, index, line=0, column=0):
        super().__init__(line, column)
        self.array = array
        self.index = index

class MemberAccess(ASTNode):
    def __init__(self, obj, member, is_pointer=False, line=0, column=0):
        super().__init__(line, column)
        self.obj = obj
        self.member = member
        self.is_pointer = is_pointer  # True for ->, False for .

class PointerDeref(ASTNode):
    def __init__(self, expr, line=0, column=0):
        super().__init__(line, column)
        self.expr = expr

class AddressOf(ASTNode):
    def __init__(self, expr, line=0, column=0):
        super().__init__(line, column)
        self.expr = expr

class SizeOf(ASTNode):
    def __init__(self, type_or_expr, is_type=True, line=0, column=0):
        super().__init__(line, column)
        self.type_or_expr = type_or_expr
        self.is_type = is_type

class FuncCall(ASTNode):
    def __init__(self, name, args, line=0, column=0):
        super().__init__(line, column)
        self.name = name
        self.args = args

class TernaryOp(ASTNode):
    def __init__(self, condition, true_expr, false_expr, line=0, column=0):
        super().__init__(line, column)
        self.condition = condition
        self.true_expr = true_expr
        self.false_expr = false_expr

class Cast(ASTNode):
    def __init__(self, type_node, expr, line=0, column=0):
        super().__init__(line, column)
        self.type_node = type_node
        self.expr = expr

# ── Statements ───────────────────────────────────────────

class VarDecl(ASTNode):
    def __init__(self, type_node, name, value=None, line=0, column=0):
        super().__init__(line, column)
        self.type_node = type_node
        self.name = name
        self.value = value

class IfStmt(ASTNode):
    def __init__(self, condition, body, else_body=None, line=0, column=0):
        super().__init__(line, column)
        self.condition = condition
        self.body = body
        self.else_body = else_body

class WhileStmt(ASTNode):
    def __init__(self, condition, body, line=0, column=0):
        super().__init__(line, column)
        self.condition = condition
        self.body = body

class DoWhileStmt(ASTNode):
    def __init__(self, body, condition, line=0, column=0):
        super().__init__(line, column)
        self.body = body
        self.condition = condition

class ForStmt(ASTNode):
    def __init__(self, init, condition, increment, body, line=0, column=0):
        super().__init__(line, column)
        self.init = init
        self.condition = condition
        self.increment = increment
        self.body = body

class ReturnStmt(ASTNode):
    def __init__(self, value=None, line=0, column=0):
        super().__init__(line, column)
        self.value = value

class BreakStmt(ASTNode):
    def __init__(self, line=0, column=0):
        super().__init__(line, column)
        pass

class ContinueStmt(ASTNode):
    def __init__(self, line=0, column=0):
        super().__init__(line, column)
        pass

class Block(ASTNode):
    def __init__(self, statements, line=0, column=0):
        super().__init__(line, column)
        self.statements = statements

# ── Top-level ───────────────────────────────────────────

class StructDecl(ASTNode):
    def __init__(self, name, members, line=0, column=0):
        super().__init__(line, column)
        self.name = name
        self.members = members  # list of (type_node, member_name)

class FuncDecl(ASTNode):
    def __init__(self, return_type_node, name, params, body, line=0, column=0):
        super().__init__(line, column)
        self.return_type_node = return_type_node
        self.name = name
        self.params = params  # list of (type_node, param_name)
        self.body = body

class Program(ASTNode):
    def __init__(self, declarations):
        super().__init__()
        self.declarations = declarations  # Can be FuncDecl or StructDecl

# ── Helper functions ────

def print_ast(node, indent=0):
    """Pretty-print AST for debugging"""
    pad = "  " * indent
    name = type(node).__name__

    if isinstance(node, Program):
        print(f"{pad}Program")
        for decl in node.declarations:
            print_ast(decl, indent + 1)

    elif isinstance(node, FuncDecl):
        print(f"{pad}FuncDecl: {node.return_type_node} {node.name}()")
        for ptype, pname in node.params:
            print(f"{pad}  param: {ptype} {pname}")
        print_ast(node.body, indent + 1)

    elif isinstance(node, StructDecl):
        print(f"{pad}StructDecl: {node.name}")
        for mtype, mname in node.members:
            print(f"{pad}  member: {mtype} {mname}")

    elif isinstance(node, Block):
        print(f"{pad}Block:")
        for stmt in node.statements:
            print_ast(stmt, indent + 1)

    elif isinstance(node, VarDecl):
        print(f"{pad}VarDecl: {node.type_node} {node.name}")
        if node.value:
            print_ast(node.value, indent + 1)

    elif isinstance(node, Assign):
        print(f"{pad}Assign: {node.name} {node.op}=")
        print_ast(node.value, indent + 1)

    elif isinstance(node, IfStmt):
        print(f"{pad}IfStmt:")
        print(f"{pad}  condition:")
        print_ast(node.condition, indent + 2)
        print(f"{pad}  body:")
        print_ast(node.body, indent + 2)
        if node.else_body:
            print(f"{pad}  else:")
            print_ast(node.else_body, indent + 2)

    elif isinstance(node, WhileStmt):
        print(f"{pad}WhileStmt:")
        print(f"{pad}  condition:")
        print_ast(node.condition, indent + 2)
        print(f"{pad}  body:")
        print_ast(node.body, indent + 2)

    elif isinstance(node, ForStmt):
        print(f"{pad}ForStmt:")
        if node.init: print(f"{pad}  init:"); print_ast(node.init, indent + 2)
        if node.condition: print(f"{pad}  condition:"); print_ast(node.condition, indent + 2)
        if node.increment: print(f"{pad}  increment:"); print_ast(node.increment, indent + 2)
        print(f"{pad}  body:")
        print_ast(node.body, indent + 2)

    elif isinstance(node, ReturnStmt):
        print(f"{pad}ReturnStmt:")
        if node.value:
            print_ast(node.value, indent + 1)

    elif isinstance(node, BinOp):
        print(f"{pad}BinOp: {node.op}")
        print_ast(node.left, indent + 1)
        print_ast(node.right, indent + 1)

    elif isinstance(node, UnaryOp):
        print(f"{pad}UnaryOp: {node.op}")
        print_ast(node.operand, indent + 1)

    elif isinstance(node, Number):
        print(f"{pad}Number: {node.value}")

    elif isinstance(node, StringLiteral):
        print(f"{pad}StringLiteral: {node.value!r}")

    elif isinstance(node, Identifier):
        print(f"{pad}Identifier: {node.name}")

    elif isinstance(node, FuncCall):
        print(f"{pad}FuncCall: {node.name}()")
        for arg in node.args:
            print_ast(arg, indent + 1)

    elif isinstance(node, ArrayAccess):
        print(f"{pad}ArrayAccess:")
        print_ast(node.array, indent + 1)
        print_ast(node.index, indent + 1)

    elif isinstance(node, MemberAccess):
        print(f"{pad}MemberAccess: {'.' if not node.is_pointer else '->'} {node.member}")
        print_ast(node.obj, indent + 1)

    elif isinstance(node, AddressOf):
        print(f"{pad}AddressOf:")
        print_ast(node.expr, indent + 1)

    elif isinstance(node, PointerDeref):
        print(f"{pad}PointerDeref:")
        print_ast(node.expr, indent + 1)

    elif isinstance(node, SizeOf):
        print(f"{pad}SizeOf: {node.type_or_expr}")

    else:
        print(f"{pad}{name}")