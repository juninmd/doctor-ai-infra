with open("backend/app/graph.py", "r") as f:
    content = f.read()

# Auto-formatter
import autopep8
content = autopep8.fix_code(content, options={'max_line_length': 120})

with open("backend/app/graph.py", "w") as f:
    f.write(content)
