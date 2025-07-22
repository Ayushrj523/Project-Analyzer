import os
import pandas as pd

# test_project/test_app.py
def complex_function(a, b, c):
    """
    A function with multiple paths for complexity testing.
    """
    if a > 10:
        return "A" if b > 5 else "B"
    elif a == 5 and c < 3:
        return "C"
    else:
        return "D"

def main():
    """Main execution function."""
    print("Running test application.")
    result = complex_function(6, 4, 2)
    print(f"Result: {result}")

if __name__ == '__main__':
    main()