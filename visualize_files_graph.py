import os
import sys
import logging
import yaml
import jinja2
import networkx as nx
from pyvis.network import Network
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

def generate_interactive_relationship_graph(directory, output_html):
    """Generates an interactive relationship graph using Pyvis and saves it as an HTML file."""
    logging.info(f"Starting to generate relationship graph from directory: {directory}")
    
    G = nx.DiGraph()

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
                    G.add_node(file_name, label=f"Jinja Template: {file_name}", type="jinja")
                    node_count += 1
                    for var in variables:
                        G.add_node(var, label=f"Variable: {var}", type="variable")
                        G.add_edge(file_name, var, key="uses", value=f"{var} used in {file_name}")
                        node_count += 1
                        edge_count += 1
            
            # Process YAML files
            elif file.endswith('.yml') or file.endswith('.yaml'):
                logging.info(f"Processing YAML file: {file_name}")
                relationships = extract_yaml_relationships(file_path)
                for key, sub_key, sub_value in relationships:
                    if not G.has_node(file_name):
                        G.add_node(file_name, label=f"YAML File: {file_name}", type="yaml")
                        node_count += 1
                    if sub_key is not None:
                        if isinstance(sub_key, list):
                            sub_key = str(sub_key)  # Convert the list to a string representation
                        if not G.has_node(sub_key):
                            G.add_node(sub_key, label=str(sub_key), type="yaml_key")
                        G.add_edge(file_name, sub_key, key=key, value=sub_value)
                        edge_count += 1

            # Process .ini files
            elif file.endswith('.ini'):
                logging.info(f"Processing INI file: {file_name}")
                relationships = extract_ini_properties(file_path)
                for section, key, value in relationships:
                    section_name = section if section else file_name
                    if not G.has_node(section_name):
                        G.add_node(section_name, label=f"INI File: {section_name}", type="ini")
                        node_count += 1
                    G.add_node(key, label=str(key), type="ini_key")
                    node_count += 1
                    G.add_edge(section_name, key, key=key, value=value)
                    edge_count += 1

            # Process .property or .properties files
            elif file.endswith('.property') or file.endswith('.properties'):
                logging.info(f"Processing Properties file: {file_name}")
                relationships = extract_properties_file(file_path)
                for section, key, value in relationships:
                    if not G.has_node(file_name):
                        G.add_node(file_name, label=f"Properties File: {file_name}", type="properties")
                        node_count += 1
                    G.add_node(key, label=str(key), type="property_key")
                    node_count += 1
                    G.add_edge(file_name, key, key=key, value=value)
                    edge_count += 1

    # Create an interactive graph using Pyvis
    net = Network(height="1000px", width="100%", directed=True)

    # Add nodes and edges from NetworkX graph to Pyvis graph
    color_map = {
        "yaml": "lightblue",
        "yaml_key": "lightgreen",
        "jinja": "orange",
        "variable": "yellow",
        "ini": "lightcoral",
        "ini_key": "salmon",
        "properties": "lightgrey",
        "property_key": "lightpink"
    }

    for node, data in G.nodes(data=True):
        node_type = data.get("type", "default")
        color = color_map.get(node_type, "lightblue")
        size = 15 if node_type in ["yaml", "jinja", "ini", "properties"] else 10  # Make file nodes larger
        net.add_node(str(node), title=str(data.get('label', node)), label=str(data.get('label', node)), color=color, size=size)

    for source, target, data in G.edges(data=True):
        net.add_edge(str(source), str(target), title=f"{data.get('key', '')} = {data.get('value', '')}")

    # Customize physics for less bouncing and better organization
    net.set_options("""
    var options = {
      "nodes": {
        "shape": "dot",
        "scaling": {
          "min": 10,
          "max": 30
        }
      },
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -30000,
          "springLength": 100,
          "springConstant": 0.04,
          "avoidOverlap": 1
        },
        "minVelocity": 0.75
      }
    }
    """)

    logging.info(f"Generating interactive graph and saving it to {output_html}")
    
    net.show(output_html, notebook=False)

    logging.info(f"Graph generation completed")
    logging.info(f"Nodes added: {node_count}")
    logging.info(f"Edges added: {edge_count}")
    logging.info(f"Output HTML file: {output_html}")

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Generate interactive relationship diagrams from YAML, Jinja, .ini, and .property/.properties files.")
    parser.add_argument("playbook_path", type=str, help="Path to the directory containing YAML, Jinja, .ini, and properties files.")
    parser.add_argument("output_html", type=str, help="Output path for the HTML file.")
    args = parser.parse_args()

    # Generate the interactive relationship graph
    generate_interactive_relationship_graph(args.playbook_path, args.output_html)
