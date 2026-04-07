import math
import re

class VMError(Exception):
    def __init__(self, message, pc=0):
        self.message = message
        self.pc = pc
        super().__init__(f"Runtime Error (PC={pc}): {message}")

class VirtualMachine:
    def __init__(self, instructions, string_literals=None):
        self.instructions = instructions
        self.string_literals = string_literals or {}
        self.pc = 0
        self.env = {}  # Global variables
        self.call_stack = []  # (return_pc, saved_env, result_var)
        self.param_stack = []
        self.labels = {}
        self.memory = {}  # Allocated memory blocks
        self.memory_ptr = 1000  # Starting memory address
        self.arrays = {}  # Array storage: name -> [elements]
        self.break_flag = False
        self.continue_flag = False
        self.output = ""
        self.init_stdlib()

    def init_stdlib(self):
        """Initialize standard library functions"""
        self.stdlib = {
            'print': self.builtin_print,
            'printf': self.builtin_printf,
            'scanf': self.builtin_scanf,
            'strlen': self.builtin_strlen,
            'strcmp': self.builtin_strcmp,
            'strcpy': self.builtin_strcpy,
            'malloc': self.builtin_malloc,
            'free': self.builtin_free,
            'abs': self.builtin_abs,
            'sqrt': self.builtin_sqrt,
            'pow': self.builtin_pow,
            'sin': self.builtin_sin,
            'cos': self.builtin_cos,
            'getchar': self.builtin_getchar,
            'putchar': self.builtin_putchar,
        }

    def _resolve_labels(self):
        """Build label table"""
        for i, inst in enumerate(self.instructions):
            if inst.op in ("FUNC", "LABEL"):
                self.labels[inst.arg1] = i

    def _get_val(self, arg):
        """Get value of an argument"""
        if arg is None:
            return None

        # Numeric literals
        if isinstance(arg, (int, float)):
            return arg

        # String literals
        if isinstance(arg, str):
            if arg.startswith("@str:"):
                # String literal reference
                match = re.match(r"@str:([^:]+):(.+)", arg)
                if match:
                    return match.group(2)
                return arg

            if arg.startswith("'") and arg.endswith("'"):
                # Character literal
                return ord(arg[1])

            # Try to parse as number
            try:
                return int(arg)
            except ValueError:
                try:
                    return float(arg)
                except ValueError:
                    pass

            # Variable lookup
            if arg in self.env:
                return self.env[arg]

            # Array access
            if "[" in arg and "]" in arg:
                match = re.match(r"(\w+)\[(\d+)\]", arg)
                if match:
                    arr_name, idx = match.groups()
                    idx = int(idx)
                    if arr_name in self.arrays and idx < len(self.arrays[arr_name]):
                        return self.arrays[arr_name][idx]

        raise VMError(f"Undefined variable or value: {arg}", self.pc)

    def _set_val(self, name, value):
        """Set a variable value"""
        if "[" in name and "]" in name:
            # Array assignment
            match = re.match(r"(\w+)\[(\d+)\]", name)
            if match:
                arr_name, idx = match.groups()
                idx = int(idx)
                if arr_name not in self.arrays:
                    self.arrays[arr_name] = []
                while len(self.arrays[arr_name]) <= idx:
                    self.arrays[arr_name].append(0)
                self.arrays[arr_name][idx] = value
                return

        self.env[name] = value

    def run(self):
        """Execute the program"""
        self._resolve_labels()

        if "main" not in self.labels:
            raise VMError("No 'main' function found")

        self.pc = self.labels["main"]

        try:
            while self.pc < len(self.instructions):
                inst = self.instructions[self.pc]
                self._execute_instruction(inst)
                self.pc += 1
        except VMError:
            raise

        return self.output

    def _execute_instruction(self, inst):
        """Execute a single instruction"""
        op = inst.op

        # Control flow
        if op in ("FUNC", "LABEL", "PARAM_DECL"):
            pass

        elif op == "VAR_DECL":
            self.env[inst.arg1] = 0

        elif op == "VAR_ASSIGN":
            val = self._get_val(inst.arg2)
            self._set_val(inst.arg1, val)

        elif op == "ASSIGN":
            val = self._get_val(inst.arg2)
            self._set_val(inst.result, val)

        elif op == "LOAD":
            val = self._get_val(inst.arg1)
            self._set_val(inst.result, val)

        # Arithmetic
        elif op == "+":
            result = self._get_val(inst.arg1) + self._get_val(inst.arg2)
            self.env[inst.result] = result

        elif op == "-":
            result = self._get_val(inst.arg1) - self._get_val(inst.arg2)
            self.env[inst.result] = result

        elif op == "*":
            result = self._get_val(inst.arg1) * self._get_val(inst.arg2)
            self.env[inst.result] = result

        elif op == "/":
            arg2 = self._get_val(inst.arg2)
            if arg2 == 0:
                raise VMError("Division by zero", self.pc)
            result = self._get_val(inst.arg1) / arg2
            self.env[inst.result] = int(result) if isinstance(result, float) and result.is_integer() else result

        elif op == "%":
            result = self._get_val(inst.arg1) % self._get_val(inst.arg2)
            self.env[inst.result] = result

        # Comparison
        elif op == "<":
            result = int(self._get_val(inst.arg1) < self._get_val(inst.arg2))
            self.env[inst.result] = result

        elif op == ">":
            result = int(self._get_val(inst.arg1) > self._get_val(inst.arg2))
            self.env[inst.result] = result

        elif op == "<=":
            result = int(self._get_val(inst.arg1) <= self._get_val(inst.arg2))
            self.env[inst.result] = result

        elif op == ">=":
            result = int(self._get_val(inst.arg1) >= self._get_val(inst.arg2))
            self.env[inst.result] = result

        elif op == "==":
            result = int(self._get_val(inst.arg1) == self._get_val(inst.arg2))
            self.env[inst.result] = result

        elif op == "!=":
            result = int(self._get_val(inst.arg1) != self._get_val(inst.arg2))
            self.env[inst.result] = result

        # Logical
        elif op == "&&":
            result = int(bool(self._get_val(inst.arg1)) and bool(self._get_val(inst.arg2)))
            self.env[inst.result] = result

        elif op == "||":
            result = int(bool(self._get_val(inst.arg1)) or bool(self._get_val(inst.arg2)))
            self.env[inst.result] = result

        # Unary
        elif op == "UNARY":
            operand = self._get_val(inst.arg2)
            if inst.arg1 == "!":
                self.env[inst.result] = int(not operand)
            elif inst.arg1 == "-":
                self.env[inst.result] = -operand
            elif inst.arg1 == "++":
                new_val = operand + 1
                self.env[inst.result] = operand if inst.arg3 == "postfix" else new_val
                # Update the original variable
            elif inst.arg1 == "--":
                new_val = operand - 1
                self.env[inst.result] = operand if inst.arg3 == "postfix" else new_val

        # Array operations
        elif op == "ARRAY_ACCESS":
            array_val = self._get_val(inst.arg1)
            index = int(self._get_val(inst.arg2))
            if isinstance(array_val, list) and index < len(array_val):
                self.env[inst.result] = array_val[index]
            else:
                raise VMError(f"Array index out of bounds: {index}", self.pc)

        # Member access
        elif op == "MEMBER":
            obj = self._get_val(inst.arg1)
            member = inst.arg2
            if isinstance(obj, dict) and member in obj:
                self.env[inst.result] = obj[member]

        elif op == "MEMBER_PTR":
            ptr = self._get_val(inst.arg1)
            member = inst.arg2
            # Pointer dereferencing
            if ptr in self.memory and isinstance(self.memory[ptr], dict):
                self.env[inst.result] = self.memory[ptr].get(member, 0)

        # Pointer operations
        elif op == "ADDR_OF":
            # Address of - allocate memory for variable
            var_name = inst.arg1
            self.env[inst.result] = id(var_name)  # Use Python id as address

        elif op == "PTR_DEREF":
            ptr = self._get_val(inst.arg1)
            if ptr in self.memory:
                self.env[inst.result] = self.memory[ptr]

        # Size of
        elif op == "SIZEOF_TYPE":
            type_str = inst.arg1
            # Simplified sizes
            sizes = {"int": 4, "float": 8, "char": 1, "void": 0}
            self.env[inst.result] = sizes.get(type_str, 4)

        elif op == "SIZEOF_EXPR":
            # Simplified
            self.env[inst.result] = 4

        # Cast
        elif op == "CAST":
            target_type = inst.arg1
            value = self._get_val(inst.arg2)
            if target_type == "int":
                self.env[inst.result] = int(value)
            elif target_type == "float":
                self.env[inst.result] = float(value)
            elif target_type == "char":
                self.env[inst.result] = chr(int(value))
            else:
                self.env[inst.result] = value

        # Control flow
        elif op == "JUMP":
            self.pc = self.labels[inst.arg1] - 1

        elif op == "JUMP_IF_TRUE":
            if self._get_val(inst.arg1):
                self.pc = self.labels[inst.arg2] - 1

        elif op == "JUMP_IF_FALSE":
            if not self._get_val(inst.arg1):
                self.pc = self.labels[inst.arg1] - 1

        # Function calls
        elif op == "PUSH_ARG":
            self.param_stack.append(self._get_val(inst.arg1))

        elif op == "CALL":
            func_name = inst.arg1
            num_args = int(inst.arg2)

            if func_name in self.stdlib:
                # Built-in function
                result = self.stdlib[func_name](self.param_stack[:num_args])
                self.param_stack = self.param_stack[num_args:]
                if inst.result:
                    self.env[inst.result] = result
            else:
                # User-defined function
                self.call_stack.append((self.pc + 1, self.env.copy(), inst.result))
                self.env = {}
                self.pc = self.labels[func_name] - 1

        elif op == "RETURN":
            ret_val = self._get_val(inst.arg1) if inst.arg1 else None
            if not self.call_stack:
                # Main function return
                return ret_val

            ret_pc, old_env, result_var = self.call_stack.pop()
            self.env = old_env
            if result_var:
                self.env[result_var] = ret_val
            self.pc = ret_pc - 1

        elif op == "BREAK":
            self.break_flag = True

        elif op == "CONTINUE":
            self.continue_flag = True

    # ── Standard Library Functions ────────────────────────────

    def builtin_print(self, args):
        if args:
            self.output += str(args[0]) + "\n"
        return 0

    def builtin_printf(self, args):
        if not args:
            return 0

        fmt = str(args[0])
        i = 1
        result_str = ""

        j = 0
        while j < len(fmt):
            if fmt[j] == '%' and j + 1 < len(fmt):
                spec = fmt[j + 1]
                if spec == 'd' or spec == 'i':
                    result_str += str(int(args[i]) if i < len(args) else 0)
                    i += 1
                elif spec == 'f':
                    result_str += str(float(args[i]) if i < len(args) else 0.0)
                    i += 1
                elif spec == 's':
                    result_str += str(args[i] if i < len(args) else "")
                    i += 1
                elif spec == 'c':
                    result_str += chr(int(args[i])) if i < len(args) else ""
                    i += 1
                elif spec == '%':
                    result_str += '%'
                j += 2
            elif fmt[j] == '\\' and j + 1 < len(fmt):
                escape = fmt[j + 1]
                if escape == 'n':
                    result_str += '\n'
                elif escape == 't':
                    result_str += '\t'
                elif escape == '\\':
                    result_str += '\\'
                j += 2
            else:
                result_str += fmt[j]
                j += 1

        self.output += result_str
        return len(result_str)

    def builtin_scanf(self, args):
        # Simplified: just return 0
        return 0

    def builtin_strlen(self, args):
        if args:
            return len(str(args[0]))
        return 0

    def builtin_strcmp(self, args):
        if len(args) >= 2:
            s1, s2 = str(args[0]), str(args[1])
            return 0 if s1 == s2 else (-1 if s1 < s2 else 1)
        return 0

    def builtin_strcpy(self, args):
        if len(args) >= 2:
            return str(args[1])
        return ""

    def builtin_malloc(self, args):
        if args:
            size = int(args[0])
            addr = self.memory_ptr
            self.memory[addr] = bytearray(size)
            self.memory_ptr += size
            return addr
        return 0

    def builtin_free(self, args):
        if args:
            addr = int(args[0])
            if addr in self.memory:
                del self.memory[addr]
        return 0

    def builtin_abs(self, args):
        if args:
            return abs(args[0])
        return 0

    def builtin_sqrt(self, args):
        if args:
            return math.sqrt(float(args[0]))
        return 0.0

    def builtin_pow(self, args):
        if len(args) >= 2:
            return math.pow(float(args[0]), float(args[1]))
        return 0.0

    def builtin_sin(self, args):
        if args:
            return math.sin(float(args[0]))
        return 0.0

    def builtin_cos(self, args):
        if args:
            return math.cos(float(args[0]))
        return 0.0

    def builtin_getchar(self, args):
        # Simplified: return 0
        return 0

    def builtin_putchar(self, args):
        if args:
            self.output += chr(int(args[0]))
            return int(args[0])
        return 0