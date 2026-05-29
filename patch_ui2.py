from pathlib import Path
path = Path('ui.py')
text = path.read_text(encoding='utf-8')
pattern = '""".strip()\n\ndef print_simulation_snapshot'
if pattern not in text:
    idx = text.find('""".strip()')
    if idx == -1:
        raise RuntimeError('Did not find the triple-quote strip marker in ui.py')
    start = max(0, idx - 20)
    end = min(len(text), idx + 80)
    print('context:', repr(text[start:end]))
    raise RuntimeError('Pattern not found for replacement')
text = text.replace(pattern, '""".strip()\n    )\n\ndef print_simulation_snapshot', 1)
path.write_text(text, encoding='utf-8')
print('patched')
