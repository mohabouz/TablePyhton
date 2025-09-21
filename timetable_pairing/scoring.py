from typing import Dict
from .models import Teacher
from .constants import DAYS


def score_pair(a: Teacher, b: Teacher) -> Dict[str, int]:
    total = min(len(a.slots), len(b.slots))
    overlap = sum(1 for i in range(total) if a.slots[i] == 1 and b.slots[i] == 1)
    xor_slots = sum(1 for i in range(total) if a.slots[i] ^ b.slots[i])
    both_off = total - (overlap + xor_slots)
    coverage = total - both_off
    return {"overlap": overlap, "xor": xor_slots, "both_off": both_off, "coverage": coverage}


def per_day_breakdown(a: Teacher, b: Teacher):
    out = []
    total = min(len(a.slots), len(b.slots))
    slots_per_day = total // len(DAYS) if total % len(DAYS) == 0 else 8
    for d in range(len(DAYS)):
        start = d * slots_per_day
        end = start + slots_per_day
        aa = a.slots[start:end]
        bb = b.slots[start:end]
        overlap = sum(1 for k in range(len(aa)) if aa[k] == 1 and bb[k] == 1)
        xor_slots = sum(1 for k in range(len(aa)) if aa[k] ^ bb[k])
        both_off = len(aa) - (overlap + xor_slots)
        out.append({"day": d, "overlap": overlap, "xor": xor_slots, "both_off": both_off})
    return out
