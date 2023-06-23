RDFVR
======
**RDFVR** (**RDF** **V**alidation **R**eport) is a pure Python package to generate readable reports for the validation of RDF graphs against Shapes Constraint Language (SHACL) graphs.

## Installation
Install with *pip* (Python 3 pip installer `pip3`):
```bash
$ pip3 install rdfvr
```

## Command Line Use
```bash
$ rdfvr -f /path/to/rdf_graph -ff rdf_graph_format -s path/to/schema_of_rdf_graph -sf schema_of_rdf_graph_format -m path/to/mappings -o path/to/report -of report_format
```
Where
- `-f` is the path of the RDF graph file to be validated (also supports multiple files)
- `-ff` is the format of the RDF graph file (also supports multiple file formats when we have multiple RDF graph files)
- `-s` is the path of the the RDF graph's schema
- `-sf` is the format of the RDF graph's schema
- `-m` is the path of mappings to shorten the report
- `-o` is the path of the validation report (also supports multiple files when we have multiple RDF graph files)
- `-of` is the format of the validation report (also supports multiple file formats when we have multiple RDF graph files)

Full CLI Usage Options:
```bash
$ rdfvr -h
usage: rdfvr [-h] [--file FILE] [--schema SCHEMA] [--fileformat FILEFORMAT]
             [--schemaformat {xml,n3,turtle,nt,pretty-xml,trix,trig,nquads,json-ld,hext}]
             [--mappings MAPPINGS] [--output OUTPUT] [--outputformat OUTPUTFORMAT]

optional arguments:
  -h, --help            show this help message and exit
  --file FILE, -f FILE  File(s) of the RDF graph(s) to be validated (list[str] | str ): please use comma (no space) to split multiple file paths (e.g.
                        file1,file2,file3).
  --schema SCHEMA, -s SCHEMA
                        Schema of the RDF graph, i.e., Shapes Constraint Language (SHACL) graph (str): path of the file.
  --fileformat FILEFORMAT, -ff FILEFORMAT
                        File format(s) of the RDF graph(s) to be validated (list[str] | str ). Orders should be consistent with the input of --file. Default format is
                        json-ld. If all input files have the same format, only need to write once.
  --schemaformat {xml,n3,turtle,nt,pretty-xml,trix,trig,nquads,json-ld,hext}, -sf {xml,n3,turtle,nt,pretty-xml,trix,trig,nquads,json-ld,hext}
                        File format of the schema (str). Default format is ttl.
  --mappings MAPPINGS, -m MAPPINGS
                        File of the mappings to shorten the report (str): path of the JSON file, where the key is the original text and the value is the shorter text.
  --output OUTPUT, -o OUTPUT
                        File(s) of the output, validation report (list[str] | str ). If no value, then output will be a string. Please use comma (no space) to split
                        multiple file paths (e.g. file1,file2,file3).
  --outputformat OUTPUTFORMAT, -of OUTPUTFORMAT
                        File format(s) of the output, validation report (list[str] | str ). Orders should be consistent with the input of --output. Default format is
                        txt. Each item can only be one of {txt,png}. Please use comma (no space) to split multiple formats (e.g. format1,format2,format3). If all
                        output files have the same format, only need to write once.

```

## Python Module Use
You can call the `validation_report` function of the `rdfvr` module as follows:

```python
from rdfvr import validation_report
validation_report(file_path, file_format, schema, schema_format, output_path, output_format, mappings)
```

Where
- `file_path` is the file path (string) of a RDF graph
- `file_format` is the format (string) of the RDF graph file
- `schema` is the file path (string) of the RDF graph's schema
- `schema_format` is the format (string) of the schema file
- `output_path` is the file path (string) of the validation report
- `output_format` is the format (string) of the validation report, i.e., `txt` or `png`
- `mappings` is the mappings (dictionary) to shorten the report

The return value is `None`.

The output will be either a `txt` file, a `png` file, or a `string` print in Bash.

