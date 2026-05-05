"""
CSE321 Project #1 — Experiment Runner
Usage: python experiments.py
"""

import csv
import time
import random

from btrees import BTree, BStarTree, BPlusTree

CSV_PATH = "student.csv"
TREE_ORDERS = [3, 5, 10]
SEARCH_SAMPLE = 10_000
DELETE_PROPORTIONS = [0.1, 0.2]
RANGE_LOW, RANGE_HIGH = 202000000, 202100000
RANGE_SELECTIVITY_QUERIES = [
    ("Small", 202000000, 202010000),
    ("Medium", 202000000, 202050000),
    ("Large", 202000000, 202300000),
]


# ──────────────────────────────────────────────
# Data loading
# ──────────────────────────────────────────────

def load_records(path):
    records = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append({
                'student_id': int(row['Student ID']),
                'name':       row['Name'],
                'gender':     row['Gender'],
                'gpa':        float(row['GPA']),
                'height':     float(row['Height']),
                'weight':     float(row['Weight']),
            })
    return records


def build_trees(records, n):
    """Insert all records into fresh trees; return (btree, bstar, bplus)."""
    btree = BTree(n)
    bstar = BStarTree(n)
    bplus = BPlusTree(n)
    for rid, rec in enumerate(records):
        key = rec['student_id']
        btree.insert(key, rid)
        bstar.insert(key, rid)
        bplus.insert(key, rid)
    return btree, bstar, bplus


# ──────────────────────────────────────────────
# Experiment 1: Insertion & Parameter Tuning
# ──────────────────────────────────────────────

def exp_insertion(records, orders=TREE_ORDERS):
    print("=" * 60)
    print("Experiment 1: Insertion & Parameter Tuning")
    print("=" * 60)

    header = f"{'n':>4} | {'Tree':>8} | {'Time(s)':>10} | {'Splits':>8} | {'Utilization':>12}"
    print(header)
    print("-" * len(header))

    for n in orders:
        for name, TreeClass in [("B-tree", BTree), ("B*-tree", BStarTree), ("B+-tree", BPlusTree)]:
            tree = TreeClass(n)
            t0 = time.perf_counter()
            for rid, rec in enumerate(records):
                tree.insert(rec['student_id'], rid)
            elapsed = time.perf_counter() - t0

            splits = tree.split_count
            util = tree.node_utilization()
            print(f"{n:>4} | {name:>8} | {elapsed:>10.4f} | {splits:>8} | {util:>12.4f}")

    print()


# ──────────────────────────────────────────────
# Experiment 2: Point Search
# ──────────────────────────────────────────────

def exp_point_search(records, btree, bstar, bplus, n=SEARCH_SAMPLE):
    print("=" * 60)
    print(f"Experiment 2: Point Search  (n={n})")
    print("=" * 60)

    sample_keys = random.sample([r['student_id'] for r in records], n)

    for name, tree in [("B-tree", btree), ("B*-tree", bstar), ("B+-tree", bplus)]:
        t0 = time.perf_counter()
        for key in sample_keys:
            tree.search(key)
        elapsed = time.perf_counter() - t0
        mean_us = elapsed / n * 1e6
        print(f"  {name:>8}: total={elapsed:.4f}s  mean={mean_us:.4f}us/query")

    print()


# ──────────────────────────────────────────────
# Experiment 3: Range Query
# ──────────────────────────────────────────────

def exp_range_query(records, btree, bstar, bplus,
                    lo=RANGE_LOW, hi=RANGE_HIGH):
    """
    Analytical query: average GPA and height of MALE students
    whose Student ID is in [lo, hi].
    """
    print("=" * 60)
    print(f"Experiment 3: Range Query  [{lo}, {hi}]")
    print("=" * 60)

    for name, tree in [("B-tree", btree), ("B*-tree", bstar), ("B+-tree", bplus)]:
        t0 = time.perf_counter()

        if hasattr(tree, 'range_query'):
            # B+-tree: use linked-list leaf scan
            hits = tree.range_query(lo, hi)
            result_rids = [rid for _, rid in hits]
        else:
            # B-tree / B*-tree: sequential scan over range
            # (implement a range helper, or fall back to per-key search)
            result_rids = []
            for rec in records:
                key = rec['student_id']
                if lo <= key <= hi:
                    rid = tree.search(key)
                    if rid is not None:
                        result_rids.append(rid)

        # Aggregate using in-memory records
        male_gpas = []
        male_heights = []
        for rid in result_rids:
            rec = records[rid]
            if rec['gender'] == 'Male':
                male_gpas.append(rec['gpa'])
                male_heights.append(rec['height'])

        elapsed = time.perf_counter() - t0

        avg_gpa    = sum(male_gpas)    / len(male_gpas)    if male_gpas    else float('nan')
        avg_height = sum(male_heights) / len(male_heights) if male_heights else float('nan')

        print(f"  {name:>8}: time={elapsed:.4f}s  "
              f"avg_GPA={avg_gpa:.4f}  avg_height={avg_height:.4f}  "
              f"count={len(male_gpas)}")

    print()


# ──────────────────────────────────────────────
# Additional Experiment: Range Selectivity
# ──────────────────────────────────────────────

def exp_range_selectivity(records, btree, bstar, bplus,
                          ranges=RANGE_SELECTIVITY_QUERIES):
    """
    Compare range query time as the queried Student ID interval grows.
    """
    print("=" * 60)
    print("Additional Experiment: Range Selectivity")
    print("=" * 60)

    header = f"{'Range':>8} | {'Interval':>23} | {'Tree':>8} | {'Time(s)':>10} | {'Count':>8}"
    print(header)
    print("-" * len(header))

    for label, lo, hi in ranges:
        for name, tree in [("B-tree", btree), ("B*-tree", bstar), ("B+-tree", bplus)]:
            t0 = time.perf_counter()
            hits = tree.range_query(lo, hi)
            result_rids = [rid for _, rid in hits]

            male_count = 0
            for rid in result_rids:
                if records[rid]['gender'] == 'Male':
                    male_count += 1

            elapsed = time.perf_counter() - t0
            interval = f"[{lo}, {hi}]"
            print(f"{label:>8} | {interval:>23} | {name:>8} | {elapsed:>10.4f} | {male_count:>8}")

    print()


# ──────────────────────────────────────────────
# Experiment 4: Deletion & Structural Integrity
# ──────────────────────────────────────────────

def exp_deletion(records, orders=TREE_ORDERS, proportions=DELETE_PROPORTIONS):
    print("=" * 60)
    print("Experiment 4: Deletion & Structural Integrity")
    print("=" * 60)

    all_keys = [r['student_id'] for r in records]

    for proportion in proportions:
        n_delete = int(len(records) * proportion)
        delete_keys = random.sample(all_keys, n_delete)

        print(f"\n  Deleting {proportion*100:.0f}% ({n_delete} records)")
        header = f"  {'n':>4} | {'Tree':>8} | {'Time(s)':>10} | {'Utilization':>12}"
        print(header)
        print("  " + "-" * (len(header) - 2))

        for n in orders:
            btree, bstar, bplus = build_trees(records, n)
            for name, tree in [("B-tree", btree), ("B*-tree", bstar), ("B+-tree", bplus)]:
                t0 = time.perf_counter()
                for key in delete_keys:
                    tree.delete(key)
                elapsed = time.perf_counter() - t0
                util = tree.node_utilization()
                print(f"  {n:>4} | {name:>8} | {elapsed:>10.4f} | {util:>12.4f}")

    print()


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main():
    random.seed(42)

    print("Loading records...")
    records = load_records(CSV_PATH)
    print(f"  {len(records)} records loaded.\n")

    # Experiment 1 (builds its own trees internally for each d)
    exp_insertion(records)

    # Build trees with default order for experiments 2 & 3
    DEFAULT_D = 10
    print(f"Building trees with n={DEFAULT_D} for search/range/delete experiments...")
    btree, bstar, bplus = build_trees(records, DEFAULT_D)
    print()
    exp_point_search(records, btree, bstar, bplus)
    exp_range_query(records, btree, bstar, bplus)
    exp_range_selectivity(records, btree, bstar, bplus)
    exp_deletion(records)


if __name__ == '__main__':
    main()
