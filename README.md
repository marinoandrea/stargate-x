# Stargate-X

[![DOI](https://zenodo.org/badge/281791887.svg)](https://zenodo.org/badge/latestdoi/281791887)

The package is a python implementation of a bipartite directed multigraph extracted from the Reactome database. Its underlying implementation uses `networkx`.

The graph represents **reactions** and **physical entities** as nodes. Edges are instead classified into 5 categories:

- input
- output
- catalyst
- positiveRegulator
- negativeRegulator

The package provides a wrapper for the `networkx.MultiDiGraph` class: the `ReactomeGraph`. Each graph instance is associated with a certain species and can either be:

- loaded from pre-built binaries shipped alongside the package
- built directly from a Neo4j instance running on the user’s machine

> NOTE: the user may prefer the latter option in order to control which specific version of Reactome’s database is used to generate the graphs. The latest supported version for this package will be periodically updated.

When building from a Neo4j instance, the package extracts data from the [Reactome graph database](https://reactome.org/download-data).

## Installation

```bash
git clone https://github.com/marinoandrea/stargate-x.git
cd stargate-x
pip install .
```

## Usage

In order to use the pre-built graphs, just call the `load` method passing the species as an argument:

```python
from stargate_x import ReactomeGraph, Species

hsa_graph = ReactomeGraph.load('Homo sapiens')
# or
hsa_graph = ReactomeGraph.load(Species.HSA)
```

In order to build a graph directly from Reactome's database, an active Neo4j instance is required.
The connection URI can be specified in the `options` (it defaults to `bolt://localhost:7687`):

```python
from stargate_x import ReactomeGraph, Species

hsa_graph = ReactomeGraph.build('Homo sapiens', options={'neo4j_uri': 'bolt://<YOUR_HOST>:<YOUR_PORT>'})
# or
hsa_graph = ReactomeGraph.build(Species.HSA, options={'neo4j_uri': 'bolt://<YOUR_HOST>:<YOUR_PORT>'})

```

## API Reference

### ReactomeGraph

Represents a graph for a certain species.

| PROPERTY             | TYPE                    | DESCRIPTION                                                |
| -------------------- | ----------------------- | ---------------------------------------------------------- |
| `event_nodes`        | `Set[str]`              | Set containing all the event nodes identifiers.            |
| `entity_nodes`       | `Set[str]`              | Set containing all the entity nodes identifiers.           |
| `compartments`       | `Iterable[Compartment]` | List of all cellular compartments for this graph instance. |
| `pathways`           | `Iterable[Pathway]`     | List of all pathways for this graph instance.              |
| `top_level_pathways` | `Iterable[Pathway]`     | List of all top level pathways for this graph instance.    |

---

| METHOD                     | ARGUMENTS                                                       | RETURNS       | DESCRIPTION                                                                                          |
| -------------------------- | --------------------------------------------------------------- | ------------- | ---------------------------------------------------------------------------------------------------- |
| `get_pathway_subgraph`     | pathway: `str` - pathway identifier                             | ReactomeGraph | Generate subgraph using nodes from the given pathway.                                                |
| `get_compartment_subgraph` | compartment: `str` - compartment GO identifier (eg: GO:0005886) | ReactomeGraph | Generate subgraph using nodes from the given compartment.                                            |
| `load`                     | species: `Union[Species, str]` - species name or enumeration    | ReactomeGraph | Factory method, builds a Reactome graph from a pickled python object.                                |
| `build`                    | species: `Union[Species, str]` - species name or enumeration    | ReactomeGraph | Factory method, builds a Reactome graph. Requires a working Neo4j instance containing Reactome data. |

### Species

Enumeration with valid Reactome species ([source](https://github.com/marinoandrea/reactome-graph/blob/master/stargate_x/species.py)).

### Pathway

Dataclass containing basic pathway information.

| PROPERTY       | TYPE   | DESCRIPTION                                 |
| -------------- | ------ | ------------------------------------------- |
| `id`           | `str`  | Reactome pathway identifier.                |
| `name`         | `str`  | Reactome display name.                      |
| `is_top_level` | `bool` | Whether the pathway is a top level pathway. |
| `in_disease`   | `bool` | Whether the pathway is part of a disease.   |

### Compartment

Dataclass containing basic cellulare compartment information.

| PROPERTY | TYPE  | DESCRIPTION                                      |
| -------- | ----- | ------------------------------------------------ |
| `id`     | `str` | GO compartment identifier (starting with 'GO:'). |
| `name`   | `str` | Reactome display name.                           |

## Examples

Obtain a subgraph relative to a specific pathway:

```python
from stargate_x import ReactomeGraph

hsa_graph = ReactomeGraph.load('Homo sapiens')
signal_transduction_subgraph = hsa_graph.get_pathway_subgraph('R-HSA-162582')
```

or to a specific cellular compartment:

```python
from stargate_x import ReactomeGraph

hsa_graph = ReactomeGraph.load('Homo sapiens')
plasma_membrane_subgraph = hsa_graph.get_compartment_subgraph('GO:0005886')
```

Here is an example where we obtain centrality measures for all nodes in a specific pathway:

```python
import networkx as nx

import stargate_x as sx

signal_transduction_subgraph = sx.ReactomeGraph\
    .load("Homo sapiens")
    .get_pathway_subgraph("R-HSA-162582")

# calculate different centrality measures for every node in the subgraph
lapl = sx.laplacian_centrality(signal_transduction_subgraph, deg_type="out_degree")
hidx = sx.h_index_centrality(signal_transduction_subgraph, deg_type="out_degree")
levr = sx.leverage_centrality(signal_transduction_subgraph, deg_type="out_degree")
```

Here is an example where we analyze the connectivity features of a single node in a specific compartment and pathway:

```python
import networkx as nx

import stargate_x as sx

# select the cytosol compartment subgraph in the nucleotides metabolism pathway
cytosol_nucleotides_metabolism_subgraph = sx.ReactomeGraph\
    .load("Homo sapiens")\
    .get_pathway_subgraph("R-HSA-15869")\
    .get_compartment_subgraph("GO:0005829")

# find all nodes reachable from ATP using standard networkx functionalities
reachable_nodes_from_atp = nx.descendants(cytosol_nucleotides_metabolism_subgraph, "R-ALL-113592")
```

Here is an example of how to obtain participating compounds given a reaction node:

```python
import stargate_x as sx

signal_transduction_graph = sx.ReactomeGraph\
    .load("Homo sapiens")
    .get_pathway_subgraph("R-HSA-9709957")

# find all compounds participating in the Phosphorylation of complexed TSC2 by PKB
# within the Signal Transduction top-level pathway
compounds = signal_transduction_graph.neighbors("R-HSA-165182")
```

## Authors

- **Andrea Marino** - ([marinoandrea](https://github.com/marinoandrea))

See also the list of [contributors](https://github.com/marinoandrea/reactome-graph/contributors) who participated in this project.
