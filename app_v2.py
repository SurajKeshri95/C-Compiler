# app_v2.py
from flask import Flask, render_template, request, jsonify
import sys
import os
import io
import traceback
from datetime import datetime

# Add src path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from lexer_v2 import Lexer, LexerError
from parser_v2 import Parser, CompileError
from semantic_v2 import SemanticAnalyser, SemanticError
from ir_generator_v2 import IRGenerator
from vm_v2 import VirtualMachine, VMError

app = Flask(__name__)

def format_error(error, source_code):
    """Format an error with context"""
    lines = source_code.split('\n')
    
    error_msg = str(error)
    line_num = getattr(error, 'line', 0)
    column = getattr(error, 'column', 0)
    
    result = {
        'type': type(error).__name__,
        'message': error_msg,
        'line': line_num,
        'column': column,
        'context': ''
    }
    
    if line_num > 0 and line_num <= len(lines):
        # Get context lines
        start = max(0, line_num - 2)
        end = min(len(lines), line_num + 1)
        
        context = []
        for i in range(start, end):
            marker = ">>> " if i == line_num - 1 else "    "
            context.append(f"{marker}{i+1:3d} | {lines[i]}")
            
            # Add caret under error column
            if i == line_num - 1 and column > 0:
                context.append(f"    {' ' * 6}{'~' * (column - 1) if column > 1 else '^'}")
        
        result['context'] = '\n'.join(context)
    
    return result

@app.route('/')
def index():
    return render_template('index_v2.html')

@app.route('/api/compile', methods=['POST'])
def compile_code():
    data = request.get_json()
    source_code = data.get('code', '')
    
    if not source_code.strip():
        return jsonify({
            'success': False,
            'error': {
                'type': 'Empty',
                'message': 'No code to compile',
                'line': 0,
                'column': 0,
                'context': ''
            },
            'output': '',
            'stats': {'time_ms': 0}
        })
    
    start_time = datetime.now()
    
    try:
        # ── Lexing ────────────────────────────────────
        try:
            lexer = Lexer(source_code)
            tokens = lexer.tokenize()
        except LexerError as e:
            return jsonify({
                'success': False,
                'phase': 'Lexical Analysis',
                'error': format_error(e, source_code),
                'output': '',
                'stats': {'time_ms': (datetime.now() - start_time).total_seconds() * 1000}
            })
        
        # ── Parsing ───────────────────────────────────
        try:
            parser = Parser(tokens)
            ast = parser.parse()
        except CompileError as e:
            return jsonify({
                'success': False,
                'phase': 'Syntax Analysis',
                'error': format_error(e, source_code),
                'output': '',
                'stats': {'time_ms': (datetime.now() - start_time).total_seconds() * 1000}
            })
        
        # ── Semantic Analysis ──────────────────────────
        try:
            analyser = SemanticAnalyser()
            analyser.analyse(ast)
        except SemanticError as e:
            return jsonify({
                'success': False,
                'phase': 'Semantic Analysis',
                'error': format_error(e, source_code),
                'output': '',
                'stats': {'time_ms': (datetime.now() - start_time).total_seconds() * 1000}
            })
        
        # ── IR Generation ──────────────────────────────
        try:
            ir_gen = IRGenerator()
            ir_gen.generate(ast)
        except Exception as e:
            return jsonify({
                'success': False,
                'phase': 'IR Generation',
                'error': {
                    'type': 'IRError',
                    'message': str(e),
                    'line': 0,
                    'column': 0,
                    'context': ''
                },
                'output': '',
                'stats': {'time_ms': (datetime.now() - start_time).total_seconds() * 1000}
            })
        
        # ── Virtual Machine Execution ──────────────────
        try:
            vm = VirtualMachine(ir_gen.instructions, ir_gen.string_literals)
            output = vm.run()
            
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            
            return jsonify({
                'success': True,
                'output': output if output else '[Program finished with no output]',
                'stats': {
                    'time_ms': elapsed,
                    'tokens': len(tokens),
                    'instructions': len(ir_gen.instructions)
                }
            })
        except VMError as e:
            return jsonify({
                'success': False,
                'phase': 'Runtime',
                'error': {
                    'type': 'RuntimeError',
                    'message': e.message,
                    'line': 0,
                    'column': 0,
                    'context': ''
                },
                'output': '',
                'stats': {'time_ms': (datetime.now() - start_time).total_seconds() * 1000}
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'phase': 'Unknown',
            'error': {
                'type': type(e).__name__,
                'message': str(e),
                'line': 0,
                'column': 0,
                'context': traceback.format_exc()
            },
            'output': '',
            'stats': {'time_ms': (datetime.now() - start_time).total_seconds() * 1000}
        })

@app.route('/api/lint', methods=['POST'])
def lint_code():
    """Quick syntax check without execution"""
    data = request.get_json()
    source_code = data.get('code', '')
    
    warnings = []
    
    try:
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        analyser = SemanticAnalyser()
        analyser.analyse(ast)
    except (LexerError, CompileError, SemanticError):
        pass  # Errors are fatal, not warnings
    
    return jsonify({'warnings': warnings})

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)