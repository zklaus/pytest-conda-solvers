# Conda solver tests

The solver tests are expressed in yaml files.
The formal json schema can be seen [here](test-schema)
Each yaml file has a top-level `tests` entry, under which a list of individual tests follows.
Each test can take one of four possible forms, targeting four different aspects of the solver interface.
All tests share some common structure, such as general identifying information, and solver configuration like used channels and the prior state of the environment.
Additionally, each type of test has its own test information, such as the expected final solution for solver tests, or the expected error condition for unsatisfiable requests.

## Common test structure

All tests share the following fields:

:::{table} Common test definition fields
|field|description|
|-|-|
|name|a descriptive name, often derived from the originating test function name|
|id|a unique id composed of a single letter and a three digit number for easy reference|
|provenance|information about the provenance of this test, usually referring to a prior test in another code base|
|kind|one of the four possible test types: `solve`, `solve_for_diff`, `unsatisfiable`, or `determine_constricting_specs`|
|input|the general test input as described below|
:::

:::{table} Test input
|field|description|
|-|-|
|specs_to_add|a list of `MatchSpecs` that should be added to the environment|
|prefix|a list of packages that are installed in the environment prior to the solving|
|history_specs|a list of `MatchSpecs` that were installed previously|
|add_pip|whether to add pip as an automatic dependency|
|
:::
