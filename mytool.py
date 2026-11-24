import sys

if len(sys.argv) < 3:
    print("usage: python3 mytool.py run <text>")
    sys.exit(1)

if sys.argv[1] == "run":
    text = " ".join(sys.argv[2:])
    print(text.upper())

