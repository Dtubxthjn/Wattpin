"""Frozen entry point shared by Linux and Windows."""
from powerglass.app import main

if __name__ == '__main__':
    raise SystemExit(main())
