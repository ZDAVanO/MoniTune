import os

assets_dir = 'src/assets'
qrc_path = 'src/resources.qrc'

files = []
for root, dirs, filenames in os.walk(assets_dir):
    for f in filenames:
        if f.endswith('.psd'):
            continue
        full_path = os.path.join(root, f)
        rel_path = os.path.relpath(full_path, 'src')
        # Replace backslashes with forward slashes for Qt resource paths
        rel_path = rel_path.replace('\\', '/')
        files.append(rel_path)

qrc_content = '<RCC>\n  <qresource prefix="/">\n'
for f in files:
    qrc_content += f'    <file>{f}</file>\n'
qrc_content += '  </qresource>\n</RCC>\n'

with open(qrc_path, 'w', encoding='utf-8') as out:
    out.write(qrc_content)

print(f"Generated {qrc_path} with {len(files)} resources.")
