import sys
import readline  # Add this import for history and key handling


class ParseError(Exception):
    pass


class Tokenizer:
    def __init__(self, expr):
        self.expr = expr.replace(" ", "")
        self.pos = 0

    def peek(self):
        if self.pos < len(self.expr):
            return self.expr[self.pos]
        return None

    def next(self):
        if self.pos < len(self.expr):
            ch = self.expr[self.pos]
            self.pos += 1
            return ch
        return None

    def consume(self, expected):
        if self.peek() == expected:
            self.next()
        else:
            raise ParseError(f"Expected '{expected}' at position {self.pos}")


class Parser:
    def __init__(self, expr):
        self.tokens = Tokenizer(expr)

    def parse(self):
        result = self.expr()
        if self.tokens.peek() is not None:
            raise ParseError(
                f"Unexpected character '{self.tokens.peek()}' at position {self.tokens.pos}"
            )
        return result

    def expr(self):
        node = self.term()
        while self.tokens.peek() in ("+", "-"):
            op = self.tokens.next()
            right = self.term()
            node = (op, node, right)
        return node

    def term(self):
        node = self.factor()
        while self.tokens.peek() in ("*", "/"):
            op = self.tokens.next()
            right = self.factor()
            node = (op, node, right)
        return node

    def factor(self):
        node = self.power()
        return node

    def power(self):
        node = self.atom()
        while self.tokens.peek() == "^":
            self.tokens.next()
            right = self.atom()
            node = ("^", node, right)
        return node

    def atom(self):
        ch = self.tokens.peek()
        if ch is None:
            raise ParseError("Unexpected end of input")
        if ch == "(":
            self.tokens.next()
            node = self.expr()
            self.tokens.consume(")")
            return node
        elif ch in "+-":
            op = self.tokens.next()
            node = self.atom()
            return (op, 0.0, node)
        else:
            return self.number()

    def number(self):
        num_str = ""
        dot_seen = False
        while True:
            ch = self.tokens.peek()
            if ch is not None and (ch.isdigit() or (ch == "." and not dot_seen)):
                if ch == ".":
                    dot_seen = True
                num_str += self.tokens.next()
            else:
                break
        if not num_str:
            raise ParseError(f"Expected number at position {self.tokens.pos}")
        return float(num_str)


class Evaluator:
    def eval(self, node):
        if isinstance(node, float):
            return node
        if isinstance(node, tuple):
            op = node[0]
            if op == "+":
                return self.eval(node[1]) + self.eval(node[2])
            elif op == "-":
                return self.eval(node[1]) - self.eval(node[2])
            elif op == "*":
                return self.eval(node[1]) * self.eval(node[2])
            elif op == "/":
                right = self.eval(node[2])
                if right == 0:
                    raise ZeroDivisionError("Division by zero")
                return self.eval(node[1]) / right
            elif op == "^":
                return self.eval(node[1]) ** self.eval(node[2])
        raise ParseError("Invalid syntax tree")


def main():
    print("Python Calculator. Type 'exit' or Ctrl+C to quit.")
    last_expr = ""
    expr_buffer = ""
    up_pressed = False

    def pre_input_hook():
        nonlocal expr_buffer, last_expr, up_pressed
        # Called before input() prompt
        if up_pressed and last_expr:
            readline.redisplay()
            sys.stdout.write("\r> " + last_expr)
            sys.stdout.flush()
            readline.insert_text(last_expr)
            readline.redisplay()
            up_pressed = False
        elif expr_buffer == "" and not up_pressed:
            readline.redisplay()
            sys.stdout.write("\r>> ")
            sys.stdout.flush()

    # Set up readline hooks
    readline.set_pre_input_hook(pre_input_hook)

    while True:
        try:
            expr = input("> ")
            if expr.strip() == "":
                continue  # Just prompt again if input is empty
            if expr.strip().lower() in ("exit", "quit"):
                break
            if expr.strip():
                last_expr = expr
            parser = Parser(expr)
            ast = parser.parse()
            result = Evaluator().eval(ast)
            print(result)
        except ParseError as e:
            print(f"Parse error: {e}")
        except ZeroDivisionError as e:
            print(f"Math error: {e}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
