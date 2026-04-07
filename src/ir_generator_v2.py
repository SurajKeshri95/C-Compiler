from ast_nodes_v2 import *

class Instruction:
    def __init__(self, op, arg1=None, arg2=None, arg3=None, result=None):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.arg3 = arg3
        self.result = result

    def __str__(self):
        parts = [f"{self.op}"]
        if self.arg1 is not None:
            parts.append(str(self.arg1))
        if self.arg2 is not None:
            parts.append(str(self.arg2))
        if self.arg3 is not None:
            parts.append(str(self.arg3))
        if self.result is not None:
            parts.append(f"-> {self.result}")
        return " ".join(parts)

class IRGenerator:
    def __init__(self):
        self.instructions = []
        self.temp_count = 0
        self.label_count = 0
        self.string_count = 0
        self.string_literals = {}  # Map string to string_id

    def new_temp(self):
        name = f"t{self.temp_count}"
        self.temp_count += 1
        return name

    def new_label(self):
        name = f"L{self.label_count}"
        self.label_count += 1
        return name

    def new_string(self, value):
        if value in self.string_literals:
            return self.string_literals[value]
        string_id = f"str_{self.string_count}"
        self.string_count += 1
        self.string_literals[value] = string_id
        return string_id

    def emit(self, op, arg1=None, arg2=None, arg3=None, result=None):
        instr = Instruction(op, arg1, arg2, arg3, result)
        self.instructions.append(instr)
        return result if result else None

    def generate(self, node):
        if isinstance(node, Program):
            for decl in node.declarations:
                if isinstance(decl, FuncDecl):
                    self.generate(decl)

        elif isinstance(node, FuncDecl):
            self.emit("FUNC", node.name)
            for ptype, pname in node.params:
                self.emit("PARAM_DECL", pname)
            self.generate(node.body)

        elif isinstance(node, StructDecl):
            pass  # Structs handled at runtime

        elif isinstance(node, Block):
            for stmt in node.statements:
                self.generate(stmt)

        elif isinstance(node, VarDecl):
            if node.value:
                val = self.generate(node.value)
                self.emit("VAR_ASSIGN", node.name, val)
            else:
                self.emit("VAR_DECL", node.name)

        elif isinstance(node, Assign):
            val = self.generate(node.value)
            if node.op == "=":
                self.emit("ASSIGN", node.name, val)
            else:
                # Compound assignment: x += 5 becomes x = x + 5
                op = node.op.rstrip("=")  # Get the operator
                temp = self.new_temp()
                self.emit("LOAD", node.name, result=temp)
                result = self.new_temp()
                self.emit(op, temp, val, result=result)
                self.emit("ASSIGN", node.name, result)

        elif isinstance(node, IfStmt):
            cond = self.generate(node.condition)
            false_label = self.new_label()
            self.emit("JUMP_IF_FALSE", cond, false_label)
            self.generate(node.body)
            if node.else_body:
                end_label = self.new_label()
                self.emit("JUMP", end_label)
                self.emit("LABEL", false_label)
                self.generate(node.else_body)
                self.emit("LABEL", end_label)
            else:
                self.emit("LABEL", false_label)

        elif isinstance(node, WhileStmt):
            start_label = self.new_label()
            end_label = self.new_label()
            self.emit("LABEL", start_label)
            cond = self.generate(node.condition)
            self.emit("JUMP_IF_FALSE", cond, end_label)
            self.generate(node.body)
            self.emit("JUMP", start_label)
            self.emit("LABEL", end_label)

        elif isinstance(node, DoWhileStmt):
            start_label = self.new_label()
            self.emit("LABEL", start_label)
            self.generate(node.body)
            cond = self.generate(node.condition)
            self.emit("JUMP_IF_TRUE", cond, start_label)

        elif isinstance(node, ForStmt):
            start_label = self.new_label()
            end_label = self.new_label()

            if node.init:
                self.generate(node.init)

            self.emit("LABEL", start_label)
            if node.condition:
                cond = self.generate(node.condition)
                self.emit("JUMP_IF_FALSE", cond, end_label)

            self.generate(node.body)

            if node.increment:
                self.generate(node.increment)

            self.emit("JUMP", start_label)
            self.emit("LABEL", end_label)

        elif isinstance(node, ReturnStmt):
            val = self.generate(node.value) if node.value else None
            self.emit("RETURN", val)

        elif isinstance(node, BreakStmt):
            self.emit("BREAK")

        elif isinstance(node, ContinueStmt):
            self.emit("CONTINUE")

        elif isinstance(node, FuncCall):
            return self._gen_func_call(node)

        else:
            return self.generate_expr(node)

    def generate_expr(self, node):
        if isinstance(node, StringLiteral):
            string_id = self.new_string(node.value)
            return f"@str:{string_id}:{node.value}"

        elif isinstance(node, CharLiteral):
            return f"'{node.value}'"

        elif isinstance(node, Number):
            return str(node.value)

        elif isinstance(node, Identifier):
            return node.name

        elif isinstance(node, BinOp):
            left = self.generate_expr(node.left)
            right = self.generate_expr(node.right)
            result = self.new_temp()
            self.emit(node.op, left, right, result=result)
            return result

        elif isinstance(node, UnaryOp):
            operand = self.generate_expr(node.operand)
            result = self.new_temp()
            if node.op in ("++", "--"):
                if node.is_postfix:
                    # Postfix: return old value, then increment
                    self.emit("UNARY", node.op, operand, result=result)
                else:
                    # Prefix: increment, then return
                    self.emit("UNARY", node.op, operand, result=result)
            else:
                self.emit("UNARY", node.op, operand, result=result)
            return result

        elif isinstance(node, ArrayAccess):
            array = self.generate_expr(node.array)
            index = self.generate_expr(node.index)
            result = self.new_temp()
            self.emit("ARRAY_ACCESS", array, index, result=result)
            return result

        elif isinstance(node, MemberAccess):
            obj = self.generate_expr(node.obj)
            op = "MEMBER_PTR" if node.is_pointer else "MEMBER"
            result = self.new_temp()
            self.emit(op, obj, node.member, result=result)
            return result

        elif isinstance(node, AddressOf):
            expr = self.generate_expr(node.expr)
            result = self.new_temp()
            self.emit("ADDR_OF", expr, result=result)
            return result

        elif isinstance(node, PointerDeref):
            expr = self.generate_expr(node.expr)
            result = self.new_temp()
            self.emit("PTR_DEREF", expr, result=result)
            return result

        elif isinstance(node, SizeOf):
            result = self.new_temp()
            if node.is_type:
                self.emit("SIZEOF_TYPE", str(node.type_or_expr), result=result)
            else:
                expr = self.generate_expr(node.type_or_expr)
                self.emit("SIZEOF_EXPR", expr, result=result)
            return result

        elif isinstance(node, FuncCall):
            return self._gen_func_call(node)

        elif isinstance(node, TernaryOp):
            cond = self.generate_expr(node.condition)
            true_label = self.new_label()
            false_label = self.new_label()
            end_label = self.new_label()

            self.emit("JUMP_IF_TRUE", cond, true_label)
            self.emit("JUMP", false_label)

            self.emit("LABEL", true_label)
            true_val = self.generate_expr(node.true_expr)
            true_result = self.new_temp()
            self.emit("ASSIGN", true_result, true_val)
            self.emit("JUMP", end_label)

            self.emit("LABEL", false_label)
            false_val = self.generate_expr(node.false_expr)
            false_result = self.new_temp()
            self.emit("ASSIGN", false_result, false_val)

            self.emit("LABEL", end_label)
            return true_result

        elif isinstance(node, Cast):
            expr = self.generate_expr(node.expr)
            result = self.new_temp()
            self.emit("CAST", str(node.type_node), expr, result=result)
            return result

        return None

    def _gen_func_call(self, node):
        args = []
        for arg in node.args:
            args.append(self.generate_expr(arg))

        result = self.new_temp()
        for arg in args:
            self.emit("PUSH_ARG", arg)

        self.emit("CALL", node.name, len(args), result=result)
        return result

    def print_ir(self):
        print("\n=== Intermediate Representation ===\n")
        for instr in self.instructions:
            print(instr)
        print("\n=== String Literals ===")
        for value, string_id in self.string_literals.items():
            print(f"{string_id}: {value!r}")