#!/usr/bin/env python3

from collections import deque
from operator import add, sub, mul, truediv, mod

class InputError(Exception): pass

operators = {
            '+': add,
            '-': sub,
            '*': mul,
            '/': truediv,
            '**': pow,
            '%': mod
            }

def eval_rpn(*seq):
    seq = deque(seq)
    stack = []
    while seq:
        token = seq.popleft()
        if token not in operators:
            try:
                token = float(token)
            except ValueError:
                raise InputError('Invalid operator: {}'.format(token))
            stack.append(token)
        else:
            try:
                b, a = float(stack.pop()), float(stack.pop())
            except IndexError:
                raise InputError('Insufficient operands.')
            oper = operators[token]
            stack.append(oper(a, b))

    if len(stack) > 1:
        raise InputError('Too many operands.')
    try:
        return stack[0]
    except IndexError:
        raise InputError('No sequence given.')

if __name__ == '__main__':
    from sys import argv
    print(eval_rpn(' '.join(argv[1:])))
