import sys
import readline


class ParseError(Exception):
    pass


def tokenize(expr):
    expr = expr.replace(" ", "")
    return expr, 0


def peek(expr, pos):
    if pos < len(expr):
        return expr[pos]
    return None


def next_token(expr, pos):
    if pos < len(expr):
        return expr[pos], pos + 1
    return None, pos


def consume(expr, pos, expected):
    if peek(expr, pos) == expected:
        return next_token(expr, pos)
    raise ParseError(f"Expected '{expected}' at position {pos}")


def parse(expr):
    expr, pos = tokenize(expr)
    node, pos = parse_expr(expr, pos)
    if peek(expr, pos) is not None:
        raise ParseError(f"Unexpected character '{peek(expr, pos)}' at position {pos}")
    return node


def parse_expr(expr, pos):
    node, pos = parse_term(expr, pos)
    while peek(expr, pos) in ("+", "-"):
        op, pos = next_token(expr, pos)
        right, pos = parse_term(expr, pos)
        node = (op, node, right)
    return node, pos


def parse_term(expr, pos):
    node, pos = parse_factor(expr, pos)
    while peek(expr, pos) in ("*", "/"):
        op, pos = next_token(expr, pos)
        right, pos = parse_factor(expr, pos)
        node = (op, node, right)
    return node, pos


def parse_factor(expr, pos):
    node, pos = parse_power(expr, pos)
    return node, pos


def parse_power(expr, pos):
    node, pos = parse_atom(expr, pos)
    while peek(expr, pos) == "^":
        _, pos = next_token(expr, pos)
        right, pos = parse_atom(expr, pos)
        node = ("^", node, right)
    return node, pos


def parse_atom(expr, pos):
    ch = peek(expr, pos)
    if ch is None:
        raise ParseError("Unexpected end of input")
    if ch == "(":
        _, pos = next_token(expr, pos)
        node, pos = parse_expr(expr, pos)
        _, pos = consume(expr, pos, ")")
        return node, pos
    elif ch in "+-":
        op, pos = next_token(expr, pos)
        node, pos = parse_atom(expr, pos)
        return (op, 0.0, node), pos
    else:
        return parse_number(expr, pos)


def parse_number(expr, pos):
    num_str = ""
    dot_seen = False
    while True:
        ch = peek(expr, pos)
        if ch is not None and (ch.isdigit() or (ch == "." and not dot_seen)):
            if ch == ".":
                dot_seen = True
            num_str += ch
            pos += 1
        else:
            break
    if not num_str:
        raise ParseError(f"Expected number at position {pos}")
    return float(num_str), pos


def eval_ast(node):
    if isinstance(node, float):
        return node
    if isinstance(node, tuple):
        op = node[0]
        if op == "+":
            return eval_ast(node[1]) + eval_ast(node[2])
        elif op == "-":
            return eval_ast(node[1]) - eval_ast(node[2])
        elif op == "*":
            return eval_ast(node[1]) * eval_ast(node[2])
        elif op == "/":
            right = eval_ast(node[2])
            if right == 0:
                raise ZeroDivisionError("Division by zero")
            return eval_ast(node[1]) / right
        elif op == "^":
            return eval_ast(node[1]) ** eval_ast(node[2])
    raise ParseError("Invalid syntax tree")


def main():
    print("Python Calculator. Type 'exit' or Ctrl+C to quit.")
    last_expr = ""
    while True:
        try:
            expr = input("> ")
            if expr.strip() == "":
                continue
            if expr.strip().lower() in ("exit", "quit"):
                break
            last_expr = expr
            ast = parse(expr)
            result = eval_ast(ast)
            print(result)
        except EOFError:
            print("")
            break
        except ParseError as e:
            print(f"Parse error: {e}")
        except ZeroDivisionError as e:
            print(f"Math error: {e}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
