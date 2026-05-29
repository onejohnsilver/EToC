from pathlib import Path
path = Path('ui.py')
text = path.read_text(encoding='utf-8')
lines = text.splitlines()
changed = False
for i, line in enumerate(lines):
    if line.strip() == '""".strip()' and i + 1 < len(lines) and lines[i + 1].startswith('def print_simulation_snapshot'):
        lines[i] = line + '    )'
        changed = True
        break
if not changed:
    raise RuntimeError('Pattern not found in ui.py')
path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('patched')
