import os
import re
import shutil

src_files = ['Audytor_Ultimate.py', 'Sensei.py', 'Nauczyciel.py', 'Skaner_Ekspercki.py', 'Audytor_Hybrid.py', 'koder.py']
target_dir = 'examples/agentic_workflows'

os.makedirs(target_dir, exist_ok=True)

patterns = [
    (r'GEMINI_API_KEY\s*=\s*\".*?\"', 'GEMINI_API_KEY = os.getenv(\"GEMINI_API_KEY\")'),
    (r'GROQ_API_KEY\s*=\s*\".*?\"', 'GROQ_API_KEY = os.getenv(\"GROQ_API_KEY\")')
]

for f in src_files:
    if not os.path.exists(f): 
        print(f"{f} not found!")
        continue
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    if 'import os' not in content:
        content = 'import os\n' + content
        
    for p, repl in patterns:
        content = re.sub(p, repl, content)
        
    target_path = os.path.join(target_dir, f)
    with open(target_path, 'w', encoding='utf-8') as file:
        file.write(content)
    print(f'Sanitized and copied {f} to {target_path}')
