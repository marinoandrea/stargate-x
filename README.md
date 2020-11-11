# Reactome-graph

The package is a python implementation of a bipartite directed multigraph extracted from the Reactome database. Its underlying implementation uses `networkx`.

The graph represents **reactions** and **physical entities** as nodes, edges are classified into 5 categories:

- input
- output
- catalyst
- positiveRegulator
- negativeRegulator

## Installation

```bash
git clone https://github.com/marinoandrea/reactome-graph.git
cd reactome-graph
pip install .
```

## Usage

```python
import reactome_graph as rg


# use pre-built graphs
hsa_graph = rg.load('Homo sapiens')
# or
hsa_graph = rg.load(rg.Species.HSA)

# build graph directly from Reactome Neo4j database
# this requires an active Neo4j instance with the Reactome database
# (defaults to 'bolt://localhost:7687')
hsa_graph = rg.build(rg.Species.HSA, options={'neo4j_uri': 'bolt://<YOUR_HOST>:<YOUR_PORT>'})
# or
hsa_graph = rg.build('Homo sapiens', options={'neo4j_uri': 'bolt://<YOUR_HOST>:<YOUR_PORT>'})

```

## Examples

Obtain a subgraph relative to a specific pathway:

```python
import reactome_graph as rg

hsa_graph = rg.load('Homo sapiens')
signal_transduction_subgraph = rg.get_pathway_subgraph(hsa_graph, 'R-HSA-162582')
```

or to a specific cellular compartment:

```python
import reactome_graph as rg

hsa_graph = rg.load('Homo sapiens')
plasma_membrane_subgraph = rg.get_compartment_subgraph(hsa_graph, 'GO:0005886')
```

## Authors

- **Andrea Marino** - ([marinoandrea](https://github.com/marinoandrea))

See also the list of [contributors](https://github.com/marinoandrea/reactome-graph/contributors) who participated in this project.
