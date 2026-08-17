with open("backend/app/graph.py", "r") as f:
    content = f.read()

content = content.replace("from .tools.azion import list_edge_applications, purge_azion_cache, check_azion_status, get_azion_metrics", "from .tools.azion import list_edge_applications, check_azion_status, get_azion_metrics")
content = content.replace("        \"Topology_Specialist\", \"Planner_Specialist\", \"FinOps_Specialist\", \"Chaos_Specialist\", \n", "        \"Topology_Specialist\", \"Planner_Specialist\", \"FinOps_Specialist\", \"Chaos_Specialist\",\n")

# Exception handling issue
content = content.replace("    except Exception as e:", "    except Exception:")

with open("backend/app/graph.py", "w") as f:
    f.write(content)
