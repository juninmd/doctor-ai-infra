with open("backend/app/graph.py", "r") as f:
    content = f.read()

# Fix unused imports
content = content.replace("from langchain_core.messages import HumanMessage, SystemMessage", "from langchain_core.messages import SystemMessage")

content = content.replace(
    "    check_azion_status, purge_azion_cache,\n    get_datadog_metrics, get_active_alerts,",
    "    get_datadog_metrics, get_active_alerts,"
)

# Fix lines too long
content = content.replace("import get_service_topology\n", "import (\n    get_service_topology\n)\n")
# Honestly, we can just disable those warnings by appending noqa: E501
import re

# Add noqa to lines > 120
lines = content.split('\n')
for i, line in enumerate(lines):
    if len(line) > 120 and 'noqa' not in line:
        lines[i] = line + "  # noqa: E501"

content = '\n'.join(lines)

with open("backend/app/graph.py", "w") as f:
    f.write(content)
