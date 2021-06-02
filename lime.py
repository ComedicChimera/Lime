import sys
from colorama import init, Fore

from lime import LimeError
from lime.interpret import LimeInterpreter

if __name__ == '__main__':
    init()

    if len(sys.argv) == 2:
        try:
            with open(sys.argv[1]) as file:
                interp = LimeInterpreter(file)
                interp.interpret()
        except FileNotFoundError:
            print(Fore.RED + f"unable to open file: `{sys.argv[1]}`")
        except RecursionError:
            print(Fore.RED + "maximum recursion depth exceeded")
        except ValueError as ve:
            print(Fore.RED + "cast error:", str(ve).replace("float", "number"))
        except LimeError as e:
            if e.line == -1:
                print(Fore.RED + f"{e.kind} error: {e.message}")
            else:
                print(Fore.RED + f"{e.kind} error: {e.message} at (ln: {e.line}, col: {e.col})")
    else:
        print(Fore.RED + "lime requires exactly one argument: a file name")