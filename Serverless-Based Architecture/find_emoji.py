#!/usr/bin/env python3
import argparse, os, sys

try:
    import emoji
except ImportError:
    print("Missing dependency: please run 'pip install emoji'")
    sys.exit(2)

SKIP_DIRS = {'.git','node_modules','__pycache__','venv','env','build','dist'}
TEXT_EXTS = None

def is_binary(path):
    try:
        with open(path,'rb') as f:
            chunk = f.read(2048)
            return b'\x00' in chunk
    except Exception:
        return True

def scan(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            path = os.path.join(dirpath, fname)
            if is_binary(path):
                continue
            try:
                with open(path, 'r', encoding='utf-8', errors='replace') as f:
                    for i, line in enumerate(f, 1):
                        ems = emoji.emoji_list(line)
                        if ems:
                            found = ''.join(e['emoji'] for e in ems)
                            print(f"{path}:{i}: {found} -> {line.strip()}")
            except Exception:
                continue

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('-p','--path', default='.', help='Root path to scan')
    args = p.parse_args()
    scan(os.path.abspath(args.path))
