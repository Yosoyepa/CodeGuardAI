import os
import socket


def terrible_function():
    # Performance: Triple nested loop (O(n^3)) -> CRITICAL
    for i in range(10):
        for j in range(10):
            for k in range(10):
                print(i, j, k)

    # Security: Eval usage -> CRITICAL
    user_input = "print('hacked')"
    eval(user_input)

    # Performance: Resource leak (no with) -> HIGH
    f = open("test.txt", "w")
    f.write("data")
    # No close()

    # Performance: N+1 Query simulation
    items = [1, 2, 3]
    for item in items:
        # Simulating DB call inside loop
        execute("SELECT * FROM table WHERE id = " + str(item))


def execute(query):
    pass
