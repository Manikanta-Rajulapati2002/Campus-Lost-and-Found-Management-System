from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.http import HttpResponse

from .forms import (
    LostItemForm,
    FoundItemForm,
    ItemSearchForm,
    FoundFromLostItemForm,
)

from .models import Item
from users.models import Notification
from claims.models import Claim   # ✅ IMPORTANT: import Claim for auto-claims


# ---------------------------------------------------------
# ADMIN CHECK
# ---------------------------------------------------------
def is_admin(user):
    return user.is_superuser or getattr(user, "role", None) in ["admin", "staff"]


@user_passes_test(is_admin)
def delete_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    item.delete()
    return redirect("list_found_items")


# ---------------------------------------------------------
# REPORT LOST ITEM
# ---------------------------------------------------------
@login_required
def report_lost_item(request):
    if request.method == "POST":
        form = LostItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.item_type = "lost"
            item.reported_by = request.user
            item.status = "unclaimed"
            item.save()
            return redirect("dashboard")
    else:
        form = LostItemForm()

    return render(request, "items/report_lost.html", {"form": form})


# ---------------------------------------------------------
# REPORT FOUND ITEM (NORMAL WORKFLOW)
# ---------------------------------------------------------
@login_required
def report_found_item(request):
    if request.method == "POST":
        form = FoundItemForm(request.POST, request.FILES)

        if form.is_valid():
            found_item = form.save(commit=False)
            found_item.item_type = "found"
            found_item.reported_by = request.user
            found_item.status = "unclaimed"
            found_item.save()
            return redirect("dashboard")

    else:
        form = FoundItemForm()

    return render(request, "items/report_found.html", {"form": form})


# ---------------------------------------------------------
# LIST LOST ITEMS (for everyone)
# ---------------------------------------------------------
def list_lost_items(request):
    items = (
        Item.objects.filter(item_type="lost", status="unclaimed")
        .order_by("-date_reported")
    )

    return render(request, "items/list_lost_items.html", {"items": items})


# ---------------------------------------------------------
# MY LOST ITEMS (User A)
# ---------------------------------------------------------
@login_required
def my_lost_items(request):
    items = (
        Item.objects.filter(item_type="lost", reported_by=request.user)
        .order_by("-date_reported")
    )

    return render(request, "items/my_lost_items.html", {"items": items})


# ---------------------------------------------------------
# STEP 1: FOUND-FROM-LOST (“I FOUND THIS” BUTTON)
# ---------------------------------------------------------
@login_required
def found_from_lost(request, item_id):
    """
    User B sees User A's lost item and clicks "I found this item".

    Behaviour:
    - Create a FOUND item linked to this LOST item (matched_lost_item)
    - Mark both as potential_match
    - 🔥 Auto-create a Claim for User A (created_by_system=True)
    - Show it in Pending Claims for admin review
    """

    lost_item = get_object_or_404(Item, id=item_id, item_type="lost")

    # Prevent user from marking their own item
    if lost_item.reported_by == request.user:
        return HttpResponse("You cannot mark your own item as found.", status=403)

    if request.method == "POST":
        form = FoundFromLostItemForm(request.POST, request.FILES)

        if form.is_valid():
            found_item = form.save(commit=False)

            # Copy essential fields from LOST item (name, category, color)
            found_item.item_type = "found"
            found_item.item_name = lost_item.item_name
            found_item.category = lost_item.category
            found_item.color = lost_item.color

            found_item.reported_by = request.user       # User B
            found_item.status = "potential_match"
            found_item.matched_lost_item = lost_item

            # Lost item also becomes potential_match
            lost_item.status = "potential_match"

            # Save both
            found_item.save()
            lost_item.save()

            # 🔥 AUTO-CREATE CLAIM for User A (system-generated)
            Claim.objects.create(
                item=lost_item,                     # The lost item being claimed
                claimed_by=lost_item.reported_by,   # User A
                matched_found_item=found_item,      # The found item from User B
                created_by_system=True,             # Mark as system-created
                matched_lost_exists=True,           # There IS a lost report
                status="pending",                   # Goes to pending_claims
                message=(
                    "System auto-created this claim because another user "
                    "reported a found item matching your lost report."
                ),
            )

            # Notify User A (owner of lost item)
            Notification.objects.create(
                user=lost_item.reported_by,
                message=(
                    f"A possible match has been found for your lost item "
                    f"'{lost_item.item_name}'. Please visit the Lost & Found Desk to confirm."
                ),
            )

            # Optional: Notify User B (finder)
            Notification.objects.create(
                user=request.user,
                message=(
                    f"Thank you! Your found item report for '{lost_item.item_name}' "
                    f"is pending confirmation by the owner and admin."
                ),
            )

            return redirect("dashboard")

    else:
        form = FoundFromLostItemForm()

    return render(
        request,
        "items/found_from_lost_form.html",
        {"lost_item": lost_item, "form": form},
    )


# ---------------------------------------------------------
# VIEW FOUND ITEMS (for students, standard claim flow)
# ---------------------------------------------------------
def list_found_items(request):
    items = (
        Item.objects.filter(item_type="found", status="unclaimed")
        .order_by("-date_reported")
    )

    return render(request, "items/list_found_items.html", {"items": items})


# ---------------------------------------------------------
# SEARCH ITEMS
# ---------------------------------------------------------
def search_items(request):
    form = ItemSearchForm(request.GET or None)
    items = Item.objects.all().order_by("-date_reported")

    if form.is_valid():
        keyword = form.cleaned_data.get("keyword")
        category = form.cleaned_data.get("category")
        color = form.cleaned_data.get("color")
        location = form.cleaned_data.get("location")
        item_type = form.cleaned_data.get("item_type")
        start_date = form.cleaned_data.get("start_date")
        end_date = form.cleaned_data.get("end_date")

        if keyword:
            items = items.filter(
                Q(item_name__icontains=keyword) | Q(description__icontains=keyword)
            )

        if category:
            items = items.filter(category__icontains=category)

        if color:
            items = items.filter(color__icontains=color)

        if location:
            items = items.filter(location__icontains=location)

        if item_type:
            items = items.filter(item_type=item_type)

        # Correct date filter for separated lost/found dates
        if start_date:
            items = items.filter(
                Q(date_lost__gte=start_date) | Q(date_found__gte=start_date)
            )

        if end_date:
            items = items.filter(
                Q(date_lost__lte=end_date) | Q(date_found__lte=end_date)
            )

    return render(
        request,
        "items/search_items.html",
        {"form": form, "items": items},
    )


# ---------------------------------------------------------
# ADMIN — PENDING MATCHES PAGE
# ---------------------------------------------------------
@user_passes_test(is_admin)
def pending_matches(request):
    matches = (
        Item.objects.filter(item_type="found", status="potential_match")
        .select_related("matched_lost_item")
    )

    return render(
        request,
        "items/pending_matches.html",
        {"matches": matches},
    )


# ---------------------------------------------------------
# ADMIN — APPROVE MATCH
# ---------------------------------------------------------
@user_passes_test(is_admin)
def approve_match(request, item_id):
    found_item = get_object_or_404(Item, id=item_id, item_type="found")
    lost_item = found_item.matched_lost_item

    found_item.status = "matched"
    lost_item.status = "matched"

    found_item.save()
    lost_item.save()

    # Notify owner
    Notification.objects.create(
        user=lost_item.reported_by,
        message=(
            f"Match confirmed! Your item '{lost_item.item_name}' has been found. "
            f"Please visit the Lost & Found desk."
        ),
    )

    # Notify finder
    Notification.objects.create(
        user=found_item.reported_by,
        message="The item you reported as found has been confirmed by the owner!",
    )

    return redirect("pending_matches")


# ---------------------------------------------------------
# ADMIN — REJECT MATCH
# ---------------------------------------------------------
@user_passes_test(is_admin)
def reject_match(request, item_id):
    found_item = get_object_or_404(Item, id=item_id, item_type="found")
    lost_item = found_item.matched_lost_item

    # Revert statuses
    found_item.status = "unclaimed"
    found_item.matched_lost_item = None

    lost_item.status = "unmatched"

    found_item.save()
    lost_item.save()

    Notification.objects.create(
        user=lost_item.reported_by,
        message="The found item did NOT match your lost item.",
    )

    Notification.objects.create(
        user=found_item.reported_by,
        message="Your reported found item did not match the lost report.",
    )

    return redirect("pending_matches")
