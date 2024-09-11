import os
import sys
import yaml
import jinja2
import networkx as nx
import matplotlib.pyplot as plt
from networkx.drawing.nx_agraph import to_agraph
import configparser
import argparse

def extract_ini_properties(file_path):
    """Extract key-value pairs from .ini files."""
    config = configparser.ConfigParser()
    config.read(file_path)
    relationships = []
    for section in config.sections():
        for key, value in config.items(section):
            relationships.append((section, key, value))
    return relationships

def extract_properties_file(file_path):
    """Extract key-value pairs from .property or .properties files."""
    relationships = []
    with open(file_path, 'r') as f:
        for line in f:
            if '=' in line:
                key, value = line.split('=', 1)
                key, value = key.strip(), value.strip()
                relationships.append((None, key, value))
    return relationships

def extract_jinja_variables(file_path):
    """Extract variables from a Jinja template file."""
    try:
        with open(file_path, 'r') as template_file:
            template_content = template_file.read()
        # Parse the Jinja template
        env = jinja2.Environment()
        parsed_content = env.parse(template_content)
        # Extract undeclared variables in the template
        variables = jinja2.meta.find_undeclared_variables(parsed_content)
        return variables
    except Exception as e:
        print(f"Error processing Jinja template {file_path}: {e}")
        return []

def extract_yaml_relationships(file_path):
    """Extract key-value relationships from a YAML file."""
    with open(file_path, 'r') as stream:
        try:
            data = yaml.safe_load(stream)
            relationships = []
            for key, value in data.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        relationships.append((key, sub_key, sub_value))
            return relationships
        except yaml.YAMLError as exc:
            print(f"Error processing file {file_path}: {exc}")
            return []

def generate_relationship_graph(directory, output_svg, output_png):
    """Generates a relationship graph from all YAML, Jinja, .ini, .property, and .properties files and saves it as SVG and PNG."""
    G = nx.DiGraph()

    # Traverse the directory recursively to find YAML, Jinja, .ini, and .property/.properties files
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_name = os.path.basename(file_path)
            
            # Process Jinja templates
            if file.endswith('.j2') or 'jinja' in file:
                variables = extract_jinja_variables(file_path)
                if variables:
                    G.add_node(file_name, label=f"Jinja Template: {file_name}")
                    for var in variables:
                        G.add_node(var, label=f"Variable: {var}")
                        G.add_edge(file_name, var, key="uses", value=f"{var} used in {file_name}")
            
            # Process YAML files
            elif file.endswith('.yml') or file.endswith('.yaml'):
                relationships = extract_yaml_relationships(file_path)
                for key, sub_key, sub_value in relationships:
                    if not G.has_node(file_name):
                        G.add_node(file_name, label=f"YAML File: {file_name}")
                    if not G.has_node(sub_key):
                        G.add_node(sub_key, label=sub_key)
                    G.add_edge(file_name, sub_key, key=key, value=sub_value)

            # Process .ini files
            elif file.endswith('.ini'):
                relationships = extract_ini_properties(file_path)
                for section, key, value in relationships:
                    section_name = section if section else file_name
                    if not G.has_node(section_name):
                        G.add_node(section_name, label=f"INI File: {section_name}")
                    G.add_node(key, label=key)
                    G.add_edge(section_name, key, key=key, value=value)

            # Process .property or .properties files
            elif file.endswith('.property') or file.endswith('.properties'):
                relationships = extract_properties_file(file_path)
                for section, key, value in relationships:
                    if not G.has_node(file_name):
                        G.add_node(file_name, label=f"Properties File: {file_name}")
                    G.add_node(key, label=key)
                    G.add_edge(file_name, key, key=key, value=value)

    # Create a graph using pygraphviz to render it as SVG and PNG
    A = to_agraph(G)

    # Enhance nodes and edges with properties
    for node in G.nodes(data=True):
        node_label = f"{node[1]['label']}\n"
        node_data = []
        for n in G[node[0]]:
            node_data.append(f"{n}: {G[node[0]][n]['key']} = {G[node[0]][n]['value']}")
        node_label += "\n".join(node_data)
        A.get_node(node[0]).attr["label"] = node_label

    for edge in G.edges(data=True):
        edge_label = f"{edge[2]['key']} = {edge[2]['value']}"
        A.get_edge(edge[0], edge[1]).attr["label"] = edge_label

    A.layout(prog='dot')  # Using 'dot' layout for a hierarchical graph structure
    A.draw(output_svg)
    A.draw(output_png)

    # Also display the graph using matplotlib
    pos = nx.spring_layout(G)
    plt.figure(figsize=(12, 12))
    nx.draw(G, pos, with_labels=True, node_size=3000, node_color='skyblue', font_size=10, font_color='black', font_weight='bold')
    plt.savefig(output_png)
    plt.show()

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Generate relationship diagrams from YAML, Jinja, .ini, and .property/.properties files.")
    parser.add_argument("playbook_path", type=str, help="Path to the directory containing YAML, Jinja, .ini, and properties files.")
    parser.add_argument("output_svg", type=str, help="Output path for the SVG file.")
    parser.add_argument("output_png", type=str, help="Output path for the PNG file.")
    args = parser.parse_args()

    # Generate the relationship graph
    generate_relationship_graph(args.playbook_path, args.output_svg, args.output_png)

