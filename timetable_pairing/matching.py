from typing import Dict, FrozenSet, List, Optional, Set, Tuple

try:
    import networkx as nx  # type: ignore
except Exception:  # pragma: no cover
    nx = None

from .models import Teacher
from .scoring import score_pair


def balanced_bottleneck_matching(
    teachers: List[Teacher],
    forbidden: Optional[Set[FrozenSet[str]]] = None,
    forced_pairs: Optional[Set[FrozenSet[str]]] = None,
) -> List[Tuple[int, int, Dict[str, int]]]:
    if nx is None:
        raise RuntimeError("Balanced objective requires networkx. Please install it (pip install networkx).")

    n = len(teachers)
    if n < 2:
        return []

    name_to_idx: Dict[str, int] = {t.name: i for i, t in enumerate(teachers)}

    forced_edges_idx: List[Tuple[int, int, Dict[str, int]]] = []
    used_nodes: Set[int] = set()
    min_forced_xor: Optional[int] = None
    if forced_pairs:
        for ff in forced_pairs:
            a_name, b_name = tuple(ff)
            if a_name not in name_to_idx or b_name not in name_to_idx:
                raise RuntimeError(f"Forced pair contains unknown teacher: {a_name}, {b_name}")
            i = name_to_idx[a_name]
            j = name_to_idx[b_name]
            if i == j:
                raise RuntimeError("Forced pair has identical teacher names")
            if i in used_nodes or j in used_nodes:
                raise RuntimeError("Teacher appears in more than one forced pair")
            s = score_pair(teachers[i], teachers[j])
            forced_edges_idx.append((min(i, j), max(i, j), s))
            used_nodes.add(i); used_nodes.add(j)
            min_forced_xor = s["xor"] if min_forced_xor is None else min(min_forced_xor, s["xor"])

    remaining_nodes = [idx for idx in range(n) if idx not in used_nodes]
    target_remaining = len(remaining_nodes) // 2

    pairs: List[Tuple[int, int, Dict[str, int]]] = []
    xors: List[int] = []
    for x in range(len(remaining_nodes)):
        i = remaining_nodes[x]
        for y in range(x + 1, len(remaining_nodes)):
            j = remaining_nodes[y]
            if forbidden and frozenset({teachers[i].name, teachers[j].name}) in forbidden:
                continue
            s = score_pair(teachers[i], teachers[j])
            pairs.append((i, j, s))
            xors.append(s["xor"])

    unique_xors = sorted(set(xors))
    if not unique_xors:
        return forced_edges_idx

    def can_match_with_threshold(th: int) -> bool:
        G = nx.Graph()
        G.add_nodes_from(remaining_nodes)
        for i, j, s in pairs:
            if s["xor"] >= th:
                G.add_edge(i, j)
        matching = nx.algorithms.matching.max_weight_matching(G, maxcardinality=True)
        return len(matching) >= target_remaining

    lo, hi = 0, len(unique_xors) - 1
    if min_forced_xor is not None:
        capped_hi = hi
        for k in range(len(unique_xors) - 1, -1, -1):
            if unique_xors[k] <= min_forced_xor:
                capped_hi = k
                break
        hi = min(hi, capped_hi)
    best_th = unique_xors[0]
    while lo <= hi:
        mid = (lo + hi) // 2
        th = unique_xors[mid]
        if can_match_with_threshold(th):
            best_th = th
            lo = mid + 1
        else:
            hi = mid - 1

    G = nx.Graph()
    G.add_nodes_from(remaining_nodes)
    for i, j, s in pairs:
        if s["xor"] >= best_th:
            weight = s["xor"] * 100 - s["overlap"]
            G.add_edge(i, j, weight=weight)

    mwm = nx.algorithms.matching.max_weight_matching(G, maxcardinality=True, weight="weight")

    chosen: List[Tuple[int, int, Dict[str, int]]] = []
    used = set()
    metrics: Dict[Tuple[int, int], Dict[str, int]] = {}
    for i, j, s in pairs:
        metrics[(i, j)] = s
    for u, v in mwm:
        i, j = (u, v) if u < v else (v, u)
        chosen.append((i, j, metrics[(i, j)]))
        used.add(i); used.add(j)

    if len(chosen) < target_remaining:
        remaining = [idx for idx in remaining_nodes if idx not in used]
        cand: List[Tuple[int, int, int]] = []
        for a in range(len(remaining)):
            i = remaining[a]
            for b in range(a + 1, len(remaining)):
                j = remaining[b]
                s = score_pair(teachers[i], teachers[j])
                if s["xor"] >= best_th:
                    weight = s["xor"] * 100 - s["overlap"]
                    cand.append((i, j, weight))
        cand.sort(key=lambda x: -x[2])
        used_local = set()
        for i, j, _ in cand:
            if i in used or j in used or i in used_local or j in used_local:
                continue
            chosen.append((i, j, score_pair(teachers[i], teachers[j])))
            used_local.add(i); used_local.add(j)
            if len(chosen) >= target_remaining:
                break

    return list(forced_edges_idx) + chosen
