#!/usr/bin/python3

from pyshacl import validate
from rdflib import Graph
import pygraphviz as pgv
import pandas as pd
import argparse, subprocess, json

def load_file(file_path, graph_format="json-ld"):
    """
    This function is to load a file with a given format as a RDF Graph object supported by RDFLib
    :param file_path: String. Path of the file
    :param graph_format: Defaults to json-ld. It could be one of {xml, n3, turtle, nt, pretty-xml, trix, trig, nquads, json-ld, hext}
    :return rdf_graph: a RDF Graph object supported by RDFLib
    """
    if graph_format not in {"xml", "n3", "turtle", "nt", "pretty-xml", "trix", "trig", "nquads", "json-ld", "hext"}:
        raise ValueError("RDFLib .parse() only supports {xml, n3, turtle, nt, pretty-xml, trix, trig, nquads, json-ld, hext}, but '" + str(format) + "' was given.")
    # Load the file (e.g., a JSON-LD file) as string
    with open(file_path) as fin:
        rdf_str = fin.read()
    # Parse string with RDFLib
    rdf_graph = Graph()
    rdf_graph.parse(data=rdf_str, format=graph_format)
    return rdf_graph

def validate_rdf(rdf, rdf_schema, data_graph_format="json-ld", shacl_graph_format="ttl"):
    """
    This function is validate the rdf_jsonld_graph with rdf_schema
    :param rdf: a RDF Graph object supported by RDFLib or a String
    :param rdf_schema: a RDF Graph object or a String
    :param data_graph_format: format of rdf, default value is json-ld
    :param shacl_graph_format: format of rdf_schema, default value is ttl
    :return results_graph: a RDF Graph object showing all errors
    """

    r = validate(data_graph=rdf,
            shacl_graph=rdf_schema,
            data_graph_format=data_graph_format,
            shacl_graph_format=shacl_graph_format,
            inference="rdfs",
            debug=False)
    conforms, results_graph, results_text = r

    return results_graph

def extract_errors(results_graph, mappings):
    """
    This function is to extract the most important errors
    Ideally, all errors will be fixed once solve these errors
    :param results_graph: a RDF Graph object showing all errors
    :return errors: a Pandas data frame with node, msg, and path columns
    """

    q = """
        PREFIX : <http://www.w3.org/ns/shacl#>

        SELECT ?focus ?msg ?path
        WHERE {
            ?curr_node :focusNode ?focus .
            ?curr_node :resultMessage ?msg .
            ?curr_node :resultPath ?path.
            OPTIONAL { ?curr_node :detail ?child_node. }
            FILTER (!bound(?child_node))
        }
    """
    rows = []
    for r in results_graph.query(q):
        rows.append(r)
    errors = pd.DataFrame(rows, columns=["node", "msg", "path"]).replace(mappings, regex=True).drop_duplicates()
    return errors

def process_graph(rdf_graph, mappings, errors):
    """
    This function is to process a RDF Graph object:
        (1) make the node name shorter
        (2) export as a Pandas data frame
        (3) add suggested nodes to be updated to the errors data frame
    :param rdf_graph: a RDF Graph object
    :param mappings: a dictionary used to make the node name shorter
    :param errors: a Pandas data frame with node, msg, and path columns
    :return rdf_graph_processed: a Pandas data frame
    :return errors_with_suggested_nodes: a Pandas data frame with node, msg, and target columns, where target column denotes suggested nodes to be updated
    """
    # Query the imported triples in rdf_graph
    q = """
            SELECT ?s ?p ?o
            WHERE {
                ?s ?p ?o
            }
        """
    rows = []
    for r in rdf_graph.query(q):
        rows.append(r)
    rdf_graph_processed = pd.DataFrame(rows, columns=["source", "label", "target"]).replace(mappings, regex=True)
    errors_with_suggested_nodes = errors.merge(rdf_graph_processed, how="left", left_on=["node", "path"], right_on=["source", "label"])[["node", "msg", "target"]]
    return rdf_graph_processed, errors_with_suggested_nodes

def visualize_graph_as_dot(rdf_graph_processed, errors_with_suggested_nodes):
    # Create a directed graph
    g_dot = pgv.AGraph(directed=True)
    # Add nodes and edges
    for _, row in rdf_graph_processed.iterrows():
        g_dot.add_node(row["source"], shape="box", style="filled, rounded", fillcolor="#b3e2cd")
        g_dot.add_node(row["target"], shape="box", style="filled, rounded", fillcolor="#b3e2cd")
        g_dot.add_edge(row["source"], row["target"], label=row["label"])
    for _, row in errors_with_suggested_nodes[["node", "msg"]].drop_duplicates().iterrows():
        g_dot.add_node(row["node"], shape="box", style="filled, rounded", fillcolor="#fdccac")
        g_dot.add_node(row["msg"], shape="box", style="filled, rounded, dashed", fillcolor="#fdccac")
        g_dot.add_edge(row["node"], row["msg"], label="ErrorMsg", style="dashed")
    # Suggested nodes to be updated
    for suggested_node in errors_with_suggested_nodes["target"].dropna().unique():
        g_dot.add_node(suggested_node, shape="box", style="filled, rounded", fillcolor="#cbd5e8")
    return g_dot

def report_graph_as_txt(errors_with_suggested_nodes):
    report_text = ""
    for _, row in errors_with_suggested_nodes.groupby(["node", "msg"])["target"].agg(list).reset_index().iterrows():
        report_text = report_text + "Node: {node} \nError Message: {msg}\nSuggested Node(s) to be Updated: {suggested_node}\n\n".format(node=row["node"], msg=row["msg"], suggested_node=", ".join(row["target"]))
    return report_text

def validation_report(file_path, file_format, schema_file, schema_format, output_path, output_format, mappings):
    # Load a file with a given format as a RDF Graph object supported by RDFLib
    rdf_graph = load_file(file_path, graph_format=file_format)
    # Validate the RDF graph
    results_graph = validate_rdf(rdf_graph, schema_file, data_graph_format=file_format, shacl_graph_format=schema_format)
    # Find the most important errors
    errors = extract_errors(results_graph, mappings)
    # Find the suggested error nodes
    (rdf_graph_processed, errors_with_suggested_nodes) = process_graph(rdf_graph, mappings, errors)
    # Output
    if output_format not in ["txt", "png"]:
        raise ValueError("The output file format can only be one of {txt, png}, but " + str(output_format) + " was given. Please check --outputformat.")
    
    if output_format == "png":
        g_dot = visualize_graph_as_dot(rdf_graph_processed, errors_with_suggested_nodes)
        dot_path = output_path + ".dot"
        g_dot.write(dot_path)
        subprocess.run(["dot", "-Tpng", dot_path, "-o", output_path])
    else:
        report_text = report_graph_as_txt(errors_with_suggested_nodes)
        if not output_path:
            # If NO --output, print a string
            print(report_text)
        else:
            with open(output_path, mode="w", encoding="utf-8") as fout:
                fout.write(report_text)
    return

def main():
    # Parse input
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", "-f", help="File(s) of the RDF graph(s) to be validated (list[str] | str ): please use comma (no space) to split multiple file paths (e.g. file1,file2,file3).")
    parser.add_argument("--schema", "-s", help="Schema of the RDF graph, i.e., Shapes Constraint Language (SHACL) graph (str): path of the file.")
    parser.add_argument("--fileformat", "-ff", help="File format(s) of the RDF graph(s) to be validated (list[str] | str ). Orders should be consistent with the input of --file. Default format is json-ld. If all input files have the same format, only need to write once.")
    parser.add_argument("--schemaformat", "-sf", default="ttl", choices=["xml", "n3", "turtle", "nt", "pretty-xml", "trix", "trig", "nquads", "json-ld", "hext"], help="File format of the schema (str). Default format is ttl.")
    parser.add_argument("--mappings", "-m", help="File of the mappings to shorten the report (str): path of the JSON file, where the key is the original text and the value is the shorter text.")
    parser.add_argument("--output", "-o", help="File(s) of the output, validation report (list[str] | str ). If no value, then output will be a string. Please use comma (no space) to split multiple file paths (e.g. file1,file2,file3).")
    parser.add_argument("--outputformat", "-of", help="File format(s) of the output, validation report (list[str] | str ).  Orders should be consistent with the input of --output. Default format is txt. Each item can only be one of {txt,png}. Please use comma (no space) to split multiple formats (e.g. format1,format2,format3). If all output files have the same format, only need to write once.")
    arg_file, arg_schema, arg_fileformat, arg_schemaformat, arg_mappings, arg_outputformat, arg_output = parser.parse_args().file, parser.parse_args().schema, parser.parse_args().fileformat, parser.parse_args().schemaformat, parser.parse_args().mappings, parser.parse_args().outputformat, parser.parse_args().output

    if not arg_file:
        parser.error("File(s) of the RDF graph(s) to be validated are missing. Please add: --file.")
    if not arg_schema:
        parser.error("Schema file is missing. Please add: --schema.")
    if arg_mappings:
        with open(arg_mappings, mode="r", encoding="utf-8") as fin:
            arg_mappings = json.loads(fin.read())
    file_paths = arg_file.split(",")
    num_files = len(file_paths)
    output_paths = [None] * num_files if not arg_output else arg_output.split(",")
    file_formats = ["json-ld"] * num_files if not arg_fileformat else arg_fileformat.split(",")
    output_formats = ["txt"] * num_files if not arg_outputformat else arg_outputformat.split(",")
    if len(file_formats) == 1:
        file_formats = file_formats * num_files
    if len(output_formats) == 1:
        output_formats = output_formats * num_files

    if num_files != len(file_formats) or num_files != len(output_formats) or num_files != len(output_paths):
        raise ValueError("Please make sure the number of input files (and input formats) equals to the number of output files (and output formats): check the value of --file, --fileformat, --output, --outputformat.")

    for file_path, file_format, output_path, output_format in zip(file_paths, file_formats, output_paths, output_formats):
        validation_report(file_path, file_format, arg_schema, arg_schemaformat, output_path, output_format, arg_mappings)

if __name__ == "__main__":
    main()
