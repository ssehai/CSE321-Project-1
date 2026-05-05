# CSE321 Project #1: B-tree Index Structures

This repository contains a from-scratch Python implementation and experimental
evaluation of three database index structures:

- B-tree
- B*-tree
- B+-tree

The project follows the CSE321 2026 Project #1 manual, "Implementation and
Analysis of B-tree Index Structures".

## Files

- `btrees.py`: implementations of B-tree, B*-tree, and B+-tree.
- `experiments.py`: experiment runner for insertion, point search, range query,
  and deletion workloads.
- `student.csv`: input dataset containing 100,000 student records.

## Environment

- Language: Python
- Tested version: Python 3.13.5
- Required external dependencies: none

Only the Python standard library is used.

## How to Run the Experiments

Run all required experiments from the repository root:

```bash
python experiments.py
```

The script automatically:

1. Loads all records from `student.csv` into an in-memory array.
2. Uses `Student ID` as the index key.
3. Uses the array position of each record as the Record Identifier (RID).
4. Builds B-tree, B*-tree, and B+-tree indexes.
5. Prints the measured results for all required workloads.

## Experiment Configuration

The main experiment parameters are defined near the top of `experiments.py`:

```python
CSV_PATH = "student.csv"
TREE_ORDERS = [3, 5, 10]
SEARCH_SAMPLE = 10_000
DELETE_PROPORTIONS = [0.1, 0.2]
RANGE_LOW, RANGE_HIGH = 202000000, 202100000
```

The point search and range query experiments use trees built with:

```python
DEFAULT_D = 10
```

## Implemented Operations

### B-tree

The B-tree implementation supports:

- Search
- Insert
- Delete
- Range query helper for experimental comparison

Internal nodes may store key-RID pairs, and search may terminate at an internal
node.

### B*-tree

The B*-tree extends the B-tree behavior. Before splitting an overflowing node,
it first attempts redistribution with a sibling. If redistribution is not
possible, it applies a 2-to-3 split strategy.

The implementation supports:

- Search
- Insert
- Delete
- Range query helper for experimental comparison

### B+-tree

The B+-tree implementation stores only keys and child pointers in internal
nodes. All RIDs are stored in leaf nodes. Leaf nodes are connected with `next`
pointers to support efficient range scans.

The implementation supports:

- Search, always reaching a leaf node
- Insert
- Delete
- Range query using the linked leaf sequence

For B+-tree accounting:

- `total_records` counts actual leaf data entries with RIDs.
- `total_key_slots` counts occupied key slots across both internal nodes and
  leaf nodes.
- `node_utilization()` uses `total_key_slots`, so internal separator keys are
  included in the structural utilization metric.

## Required Workloads

Running `python experiments.py` performs the following workloads.

### 1. Insertion and Parameter Tuning

All 100,000 records are inserted into empty B-tree, B*-tree, and B+-tree
indexes. The experiment is repeated for tree orders:

- `d = 3`
- `d = 5`
- `d = 10`

For each tree and order, the script reports:

- total insertion time
- total number of node splits
- final node utilization

### 2. Point Search

The script randomly samples 10,000 Student IDs from the dataset and searches for
each key in the B-tree, B*-tree, and B+-tree. It reports total search time and
mean time per query.

### 3. Range Query

The script runs the same analytical query on all three trees:

```text
For Student IDs in [202000000, 202100000], calculate the average GPA and average
height of male students.
```

For each tree, the script reports:

- total range query time
- average GPA
- average height
- qualifying male-student count

### 4. Deletion and Structural Integrity

The script deletes randomly selected records using two deletion proportions:

- 10% of the dataset
- 20% of the dataset

For each tree and order, it reports:

- deletion time
- node utilization after deletion

The tree implementations handle underflow using redistribution and/or merging.
