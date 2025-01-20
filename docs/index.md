# pytest-conda-solvers

This repository contains fundamentally two things, namely a set of tests for solvers for the conda ecosystem expressed as a set of yaml files with declarative test definitions, and a pytest plugin that can run these tests against any solver that is registered as a solver via the standard conda plugin system.

:::{warning}
This project is still in early stages of development. Don't use it in production (yet).
We do welcome feedback on what the expected behaviour should have been if something doesn't work!
:::

::::{grid} 1

:::{grid-item-card} 🏡 Getting started
The easiest to get started is using pixi.
To run all the tests against the classic solver, just run

:::{code}
pixi run test-classic-solver
:::
:::
::::


```{toctree}
:hidden:
conda-solver-tests
test-schema
```
