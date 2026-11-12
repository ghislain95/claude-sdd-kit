"""Copies top-level TypeScript declarations, with their doc comments, from one file into another.

Usage: extract.py SOURCE NAME [NAME ...]  (prints the declarations, in the order they appear in SOURCE)
A declaration ends at the first line, at column 0, that closes it ('}', '})', ']', ')', '}>' ...),
or on its own line when it does not open a block.
"""
import re
import sys

source, names = sys.argv[1], set(sys.argv[2:])
lines = open(source).read().split('\n')
head = re.compile(r'^(?:export\s+)?(?:async\s+)?(?:function|type|const|let|interface)\s+([A-Za-z_][A-Za-z0-9_]*)')
out = []
found = set()
index = 0
while index < len(lines):
    line = lines[index]
    match = head.match(line)
    if match is None or match.group(1) not in names:
        index += 1
        continue
    start = index
    while start > 0 and (lines[start - 1].startswith('/**') or lines[start - 1].startswith(' *') or lines[start - 1].startswith('//')):
        start -= 1
    end = index
    opens = line.rstrip().endswith(('{', '[', '(', '=', '=>', '<')) or (line.count('{') > line.count('}'))
    if opens:
        end = index + 1
        while end < len(lines) and not re.match(r'^[}\])][}\])>;,]*\s*$', lines[end]):
            end += 1
    out.append('\n'.join(lines[start:end + 1]))
    found.add(match.group(1))
    index = end + 1
missing = names - found
if missing:
    sys.stderr.write(f'missing: {sorted(missing)}\n')
print('\n\n'.join(out))
