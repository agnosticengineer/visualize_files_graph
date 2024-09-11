import os
import sys
import logging
import yaml
import jinja2
import networkx as nx
import matplotlib.pyplot as plt
from networkx.drawing.nx_agraph import to_agraph
import configparser
import argparse

# Set up logging and print immediately to console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler(sys.stdout)])

def extract_ini_properties(file_path):
    """Extract key-value pairs from .ini files."""
    logging.info(f"Extracting INI properties from {file_path}")
    config = configparser.ConfigParser()
    config.read(file_path)
    relationships = []
    for section in config.sections():
        for key, value in config.items(section):
            relationships.append((section, key, value))
    return relationships

def extract_properties_file(file_path):
    """Extract key-value pairs from .property or .properties files."""
    logging.info(f"Extracting properties from {file_path}")
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
    logging.info(f"Extracting Jinja variables from {file_path}")
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
        logging.error(f"Error processing Jinja template {file_path}: {e}")
        return []

def extract_yaml_relationships(file_path):
    """Extract key-value relationships from a YAML file."""
    logging.info(f"Extracting YAML relationships from {file_path}")
    with open(file_path, 'r') as stream:
        try:
            data = yaml.safe_load(stream)
            relationships = []

            # Check if the data is a dictionary (key-value pairs)
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            relationships.append((key, sub_key, sub_value))
                    elif isinstance(value, list):
                        # Handle list values by creating a string or processing each element
                        relationships.append((key, str(value), None))
                    else:
                        relationships.append((key, value, None))

            # Check if the data is a list
            elif isinstance(data, list):
                for index, item in enumerate(data):
                    if isinstance(item, dict):
                        for key, value in item.items():
                            relationships.append((f"ListItem{index}", key, value))
                    else:
                        relationships.append((f"ListItem{index}", None, item))

            return relationships
        
        except yaml.YAMLError as exc:
            logging.error(f"Error processing file {file_path}: {exc}")
            return []
        
def generate_relationship_graph(directory, output_svg, output_png):
    """Generates a relationship graph from all YAML, Jinja, .ini, .property, and .properties files and saves it as SVG and PNG."""
    logging.info(f"Starting to generate relationship graph from directory: {directory}")
    
    G = nx.DiGraph()

    # Ensure output directories exist
    svg_dir = os.path.dirname(output_svg)
    png_dir = os.path.dirname(output_png)

    if not os.path.exists(svg_dir):
        os.makedirs(svg_dir)
        logging.info(f"Created directory for SVG output: {svg_dir}")

    if not os.path.exists(png_dir):
        os.makedirs(png_dir)
        logging.info(f"Created directory for PNG output: {png_dir}")

    node_count = 0
    edge_count = 0

    logging.info(f"Scanning directory {directory} for files")
    
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_name = os.path.basename(file_path)
            
            # Log every found file
            logging.info(f"Found file: {file_name}")

            # Process Jinja templates
            if file.endswith('.j2') or 'jinja' in file:
                logging.info(f"Processing Jinja file: {file_name}")
                variables = extract_jinja_variables(file_path)
                if variables:
                    G.add_node(file_name, label=f"Jinja Template: {file_name}")
                    node_count += 1
                    for var in variables:
                        G.add_node(var, label=f"Variable: {var}")
                        G.add_edge(file_name, var, key="uses", value=f"{var} used in {file_name}")
                        node_count += 1
                        edge_count += 1
            
            # Process YAML files
            elif file.endswith('.yml') or file.endswith('.yaml'):
                logging.info(f"Processing YAML file: {file_name}")
                relationships = extract_yaml_relationships(file_path)
                for key, sub_key, sub_value in relationships:
                    if not G.has_node(file_name):
                        G.add_node(file_name, label=f"YAML File: {file_name}")
                        node_count += 1
                    if sub_key is not None:
                        if isinstance(sub_key, list):
                            sub_key = str(sub_key)  # Convert the list to a string representation
                        if not G.has_node(sub_key):
                            G.add_node(sub_key, label=sub_key)
                        G.add_edge(file_name, sub_key, key=key, value=sub_value)
                        edge_count += 1

            # Process .ini files
            elif file.endswith('.ini'):
                logging.info(f"Processing INI file: {file_name}")
                relationships = extract_ini_properties(file_path)
                for section, key, value in relationships:
                    section_name = section if section else file_name
                    if not G.has_node(section_name):
                        G.add_node(section_name, label=f"INI File: {section_name}")
                        node_count += 1
                    G.add_node(key, label=key)
                    node_count += 1
                    G.add_edge(section_name, key, key=key, value=value)
                    edge_count += 1

            # Process .property or .properties files
            elif file.endswith('.property') or file.endswith('.properties'):
                logging.info(f"Processing Properties file: {file_name}")
                relationships = extract_properties_file(file_path)
                for section, key, value in relationships:
                    if not G.has_node(file_name):
                        G.add_node(file_name, label=f"Properties File: {file_name}")
                        node_count += 1
                    G.add_node(key, label=key)
                    node_count += 1
                    G.add_edge(file_name, key, key=key, value=value)
                    edge_count += 1

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

    logging.info(f"Drawing the graph and saving it to {output_svg} and {output_png}")

    # Save the graph as SVG and PNG with higher resolution
    A.layout(prog='dot')  # Still using 'dot' layout for better rendering of hierarchical graphs
    A.draw(output_svg)

    # Save PNG with higher DPI, increase bitmap memory size
    A.draw(output_png, args="-Gdpi=600 -Gsize=48,48!")  # High DPI and larger canvas to improve PNG resolution

    # Also display the graph using matplotlib with increased figure size and DPI
    pos = nx.spring_layout(G)
    plt.figure(figsize=(48, 48), dpi=600)  # Even larger figure size and higher DPI to avoid scaling warnings
    nx.draw(G, pos, with_labels=True, node_size=3000, node_color='skyblue', font_size=10, font_color='black', font_weight='bold')
    plt.savefig(output_png, dpi=600)  # Save PNG with higher DPI to improve resolution
    plt.show()

    logging.info(f"Graph generation completed")
    logging.info(f"Nodes added: {node_count}")
    logging.info(f"Edges added: {edge_count}")
    logging.info(f"Output SVG file: {output_svg}")
    logging.info(f"Output PNG file: {output_png}")

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Generate relationship diagrams from YAML, Jinja, .ini, and .property/.properties files.")
    parser.add_argument("playbook_path", type=str, help="Path to the directory containing YAML, Jinja, .ini, and properties files.")
    parser.add_argument("output_svg", type=str, help="Output path for the SVG file.")
    parser.add_argument("output_png", type=str, help="Output path for the PNG file.")
    args = parser.parse_args()

    # Generate the relationship graph
    generate_relationship_graph(args.playbook_path, args.output_svg, args.output_png)
