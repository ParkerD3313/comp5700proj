import sys
from task1 import run_task1
from task2 import run_task2
from task3 import run_task3

def main():

    if len(sys.argv) < 3:
            print("Usage: python main.py <file1> <file2>")
            sys.exit(1)

    file1 = sys.argv[1]
    file2 = sys.argv[2]

    print("Running Task 1...")
    yaml1, yaml2 = run_task1(file1, file2)
    print("Running Task 2...")
    names_txt, reqs_txt = run_task2(yaml1, yaml2)
    print("Running Task 3...")
    run_task3(names_txt, reqs_txt)

if __name__ == "__main__":
    main()