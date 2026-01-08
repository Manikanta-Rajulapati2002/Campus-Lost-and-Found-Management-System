# items/matching.py

from datetime import timedelta

from django.db.models import Q

from .models import Item


def score_lost_found_pair(lost_item, found_item):
    """
    Return an integer score (0–100) for how well a lost_item matches a found_item.
    Higher = better match.
    """
    score = 0

    # 1) Category – strong signal
    if lost_item.category and found_item.category:
        if lost_item.category == found_item.category:
            score += 30
        else:
            # totally different category → very weak match
            score -= 20

    # 2) Color – medium signal
    if lost_item.color and found_item.color:
        if lost_item.color.lower().strip() == found_item.color.lower().strip():
            score += 15

    # 3) Location – medium signal (only if both given)
    if lost_item.location and found_item.location:
        loc_l = lost_item.location.lower()
        loc_f = found_item.location.lower()
        if loc_l in loc_f or loc_f in loc_l:
            score += 20

    # 4) Date proximity – important
    if lost_item.date_lost_or_found and found_item.date_lost_or_found:
        diff = abs(lost_item.date_lost_or_found - found_item.date_lost_or_found)
        if diff <= timedelta(days=1):
            score += 20
        elif diff <= timedelta(days=3):
            score += 10
        elif diff <= timedelta(days=7):
            score += 5
        else:
            # far apart in time → small penalty
            score -= 5

    # 5) Name / description keyword overlap – soft signal
    name_l = (lost_item.item_name or "").lower()
    name_f = (found_item.item_name or "").lower()
    desc_l = (lost_item.description or "").lower()
    desc_f = (found_item.description or "").lower()

    # very simple shared keyword logic
    keywords = []

    for text in [name_l, desc_l]:
        for word in text.replace(",", " ").replace(".", " ").split():
            w = word.strip()
            if len(w) >= 4:  # ignore tiny words like "a", "of"
                keywords.append(w)

    shared = 0
    for w in set(keywords):
        if w in name_f or w in desc_f:
            shared += 1

    if shared >= 3:
        score += 20
    elif shared == 2:
        score += 12
    elif shared == 1:
        score += 5

    # 6) Special rules for money & critical items
    cat = (lost_item.category or "").lower()

    # Money
    if "money" in cat or "cash" in name_l or "cash" in desc_l:
        # money is tricky: amount is often in name or description.
        # Here we just boost if everything else is close
        score += 5  # small extra weight because category is sensitive

    # Wallet / ID / Phone / Laptop – critical assets
    critical_keywords = ["wallet", "id", "card", "passport", "license",
                         "phone", "iphone", "android", "laptop", "macbook", "keys", "keychain"]
    if any(kw in name_l or kw in desc_l for kw in critical_keywords):
        score += 5  # small global boost for critical items

    # Clamp score to [0, 100]
    if score < 0:
        score = 0
    if score > 100:
        score = 100

    return score


def find_matching_lost_for_found(found_item, min_score=30, limit=10):
    """
    Given a FOUND item, search for LOST items that might match.
    Returns a list of dicts: {"lost_item": <Item>, "score": int, "confidence": "high/medium/low"}
    """
    candidates = Item.objects.filter(
        item_type="lost",
        status="unclaimed"
    )

    matches = []

    for lost in candidates:
        s = score_lost_found_pair(lost, found_item)
        if s >= min_score:
            if s >= 70:
                confidence = "high"
            elif s >= 50:
                confidence = "medium"
            else:
                confidence = "low"

            matches.append({
                "lost_item": lost,
                "score": s,
                "confidence": confidence,
            })

    # sort best first
    matches.sort(key=lambda m: m["score"], reverse=True)

    # return top N
    return matches[:limit]
