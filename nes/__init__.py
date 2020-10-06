#!/usr/bin/env python


def main():
    import sys

    if len(sys.argv) == 1:
        exit("Usage: nes file")
    print(sys.argv[1])


if __name__ == "__main__":
    main()
