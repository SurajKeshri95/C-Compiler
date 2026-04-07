# Advanced C Compiler IDE

A production-grade C compiler and IDE built from scratch with comprehensive language support, advanced error reporting, and professional debugging tools.

## ✨ Features

### Language Support
- **Data Types**: `int`, `float`, `char`, `void`
- **Control Flow**: `if/else`, `while`, `do-while`, `for` loops with `break`/`continue`
- **Functions**: User-defined functions with parameters and return values
- **Arrays**: Multi-dimensional arrays with proper indexing
- **Pointers**: Pointer declaration, dereferencing, address-of operations
- **Structs**: Structure definitions with member access (`.` and `->`)
- **Operators**: Arithmetic, comparison, logical, bitwise, increment/decrement, compound assignment
- **String Literals**: Double-quoted strings with escape sequences
- **Comments**: Single-line (`//`) and multi-line (`/* */`)

### Standard Library Functions
- **I/O**: `print()`, `printf()` with format specifiers, `scanf()`, `getchar()`, `putchar()`
- **String**: `strlen()`, `strcmp()`, `strcpy()`
- **Memory**: `malloc()`, `free()`, `sizeof()`
- **Math**: `abs()`, `sqrt()`, `pow()`, `sin()`, `cos()`

### Compilation Pipeline
1. **Lexical Analysis** - Tokenization with precise error locations
2. **Syntax Analysis** - Recursive descent parser with operator precedence
3. **Semantic Analysis** - Type checking, symbol resolution, scope management
4. **IR Generation** - Three-address code intermediate representation
5. **Execution** - Virtual machine with runtime error handling

### Professional IDE Features
- **Real-time Syntax Highlighting** - CodeMirror integration with C/C++ syntax
- **Comprehensive Error Reporting**
  - Error type (Lexical, Syntax, Semantic, Runtime)
  - Line and column numbers with source context
  - Helpful hints and suggestions
  - Error visualization in editor
- **Multiple Output Panels**
  - Program output
  - Detailed error messages
  - Variable state inspector
  - Compilation statistics
- **Performance Metrics**
  - Compilation time
  - Token count
  - Instruction count
  - Memory usage

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8+
- Flask
- CodeMirror (loaded via CDN)

### Quick Start

1. **Create project structure**:
```bash
mkdir c-compiler-ide
cd c-compiler-ide
mkdir src templates static
```

2. **Copy files**:
```bash
# Core compiler modules
cp lexer_v2.py src/lexer.py
cp parser_v2.py src/parser.py
cp ast_nodes_v2.py src/ast_nodes.py
cp semantic_v2.py src/semantic.py
cp ir_generator_v2.py src/ir_generator.py
cp vm_v2.py src/vm.py

# Web interface
cp app_v2.py app.py
cp index_v2.html templates/index.html

# Create __init__.py
touch src/__init__.py
```

3. **Install Flask** (if needed):
```bash
pip install flask
```

5. **Open browser**:
```
https://c-compiler-dgqk.onrender.com/
```

## 📖 Usage Examples

### Basic Program
```c
int main() {
    int x = 10;
    int y = 20;
    int sum = x + y;
    print(sum);
    return 0;
}
```

### Functions
```c
int add(int a, int b) {
    return a + b;
}

int main() {
    int result = add(5, 3);
    printf("Result: %d\n", result);
    return 0;
}
```

### Arrays
```c
int main() {
    int arr[5];
    arr[0] = 10;
    arr[1] = 20;
    arr[2] = arr[0] + arr[1];
    print(arr[2]);
    return 0;
}
```

### Loops
```c
int main() {
    int i;
    for (i = 0; i < 10; i++) {
        print(i);
    }
    return 0;
}
```

### String Handling
```c
int main() {
    char str[20];
    str[0] = 'H';
    str[1] = 'i';
    str[2] = '\0';
    printf("String: %s\n", str);
    printf("Length: %d\n", strlen(str));
    return 0;
}
```

### Pointers
```c
int main() {
    int x = 42;
    int ptr;
    ptr = &x;  // Address of x
    printf("Value: %d\n", *ptr);  // Dereference
    return 0;
}
```

### Structures
```c
struct Point {
    int x;
    int y;
};

int main() {
    struct Point p;
    p.x = 10;
    p.y = 20;
    printf("Point: (%d, %d)\n", p.x, p.y);
    return 0;
}
```

## 🎯 Error Messages

The compiler provides detailed, helpful error messages:

### Lexical Errors
```
Lexer Error at line 5:10: Unterminated string
    5 | printf("Hello
      |         ~~~~~~~
```

### Syntax Errors
```
Error at 3:15: expected ';' but got 'EOF'
    3 | int x = 10
      |               ^
```

### Semantic Errors
```
Semantic Error at 2:5: 'x' is not declared
  Hint: Did you forget to declare this variable?
```

### Runtime Errors
```
Runtime Error: Division by zero
```

## 🔧 Architecture

### Lexer (`lexer_v2.py`)
- Character-by-character tokenization
- Support for all C operators and keywords
- Precise line/column tracking
- String and character literal parsing

### Parser (`parser_v2.py`)
- Recursive descent parser
- Correct operator precedence
- Full statement and expression parsing
- Support for all language constructs

### AST (`ast_nodes_v2.py`)
- Clean node hierarchy
- Support for complex types (pointers, arrays, structs)
- Location tracking for error reporting

### Semantic Analyzer (`semantic_v2.py`)
- Symbol table with scope management
- Type checking and inference
- Comprehensive error reporting
- Standard library function signatures

### IR Generator (`ir_generator_v2.py`)
- Three-address code generation
- Label management for control flow
- String literal pooling
- Support for all language features

### Virtual Machine (`vm_v2.py`)
- Stack-based execution
- Function call handling
- Memory management (malloc/free simulation)
- Standard library implementation
- Proper error handling

## 🎨 IDE Features Explained

### Editor
- **Line Numbers** - Track code location
- **Syntax Highlighting** - C/C++ mode with color coding
- **Auto-completion** - Basic bracket matching
- **Keyboard Shortcuts** - Ctrl/Cmd+Enter to run

### Tabs
- **Output** - Program output and print statements
- **Errors** - Detailed compilation/runtime errors
- **Variables** - Variable state during execution
- **Statistics** - Performance metrics

### Error Visualization
- Shows error type (Lexical, Syntax, Semantic, Runtime)
- Displays source context with line/column markers
- Provides helpful hints for common mistakes
- Clickable error navigation

## 📝 Compilation Process

```
Source Code
    ↓
[Lexer] → Tokens
    ↓
[Parser] → Abstract Syntax Tree (AST)
    ↓
[Semantic Analyzer] → Type-checked AST + Symbols
    ↓
[IR Generator] → Intermediate Representation
    ↓
[Virtual Machine] → Program Execution
    ↓
Output
```

## 🐛 Known Limitations

- No support for `typedef` yet
- No bit field support in structs
- No multi-file compilation
- Dynamic arrays limited (fixed size at declaration)
- String operations simplified
- No standard library floating point precision
- Recursion depth limited by Python stack

## 🔮 Future Enhancements

- [ ] Debugger with breakpoints and step-through
- [ ] Memory visualization and heap inspector
- [ ] AST visualization
- [ ] Optimization passes
- [ ] More standard library functions
- [ ] Preprocessor support (#include, #define)
- [ ] Typedef support
- [ ] Goto statements
- [ ] Switch/case statements
- [ ] Enum support
- [ ] Union types
- [ ] Variable-length arrays (VLA)

## 📄 License

Free to use for educational and personal projects.

## 🤝 Contributing

Ideas and improvements welcome!

---

**Built with Python, Flask, and CodeMirror**
