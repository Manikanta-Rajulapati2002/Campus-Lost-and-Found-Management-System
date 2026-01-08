from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.utils import timezone

from items.models import Item
from .models import Claim
from .forms import ClaimCreateForm, ClaimReviewForm
from users.models import Notification


def is_staff_or_admin(user):
    # superusers and staff always allowed
    if user.is_superuser or user.is_staff:
        return True
    # or based on our custom role
    return getattr(user, 'role', None) in ('staff', 'admin')


# ===============================================================
# CREATE CLAIM (Student manually claiming an item)
# ===============================================================
@login_required
def create_claim(request, item_id):
    if request.user.role == "admin":
        return HttpResponse("Admins cannot submit the claims.", status=403)

    item = get_object_or_404(Item, id=item_id, item_type='found')

    # Check for bypass from warning page
    bypass = request.GET.get("bypass", "no") == "yes"

    # STEP 1 — Check if user has a matching lost item
    similar_lost = Item.objects.filter(
        reported_by=request.user,
        item_type='lost',
        item_name__icontains=item.item_name,
        color__icontains=item.color,
        category__icontains=item.category
    )

    # STEP 2 — If user has NO similar lost report AND not bypassed → show warning page
    if not similar_lost.exists() and not bypass:
        return render(request, "claims/missing_lost_warning.html", {
            "item": item,
        })

    # STEP 3 — Create claim after user confirms
    if request.method == 'POST':
        form = ClaimCreateForm(request.POST)
        if form.is_valid():
            claim = form.save(commit=False)
            claim.item = item
            claim.claimed_by = request.user
            claim.matched_lost_exists = similar_lost.exists()
            claim.status = "pending"
            claim.save()
            return redirect('dashboard')
    else:
        form = ClaimCreateForm()

    return render(request, "claims/create_claim.html", {
        "item": item,
        "form": form
    })


# ===============================================================
# MY CLAIMS (Student view)
# ===============================================================
@login_required
def my_claims(request):
    claims = Claim.objects.filter(
        claimed_by=request.user
    ).select_related('item').order_by('-created_at')

    return render(request, 'claims/my_claims.html', {'claims': claims})


@login_required
def claim_confirmation(request, item_id):
    if request.user.role == "admin":
        return HttpResponse("Admins cannot submit claims.", status=403)
    item = get_object_or_404(Item, id=item_id, item_type='found')
    return render(request, 'claims/claim_confirmation.html', {
        'item': item
    })


# ===============================================================
# ADMIN — VIEW PENDING CLAIMS
# ===============================================================
@user_passes_test(is_staff_or_admin)
def pending_claims(request):
    claims = Claim.objects.filter(
        status='pending'
    ).select_related('item', 'claimed_by').order_by('created_at')

    return render(request, 'claims/pending_claims.html', {'claims': claims})


# ===============================================================
# ADMIN — REVIEW CLAIM (APPROVE / REJECT)
# ===============================================================
@login_required
def review_claim(request, claim_id):
    claim = get_object_or_404(Claim, id=claim_id)
    item = claim.item

    # Find matching lost items from the claimant
    matching_lost = Item.objects.filter(
        reported_by=claim.claimed_by,
        item_type='lost',
        item_name__icontains=item.item_name,
        color__icontains=item.color,
        category__icontains=item.category
    )

    if request.method == 'POST':
        decision = request.POST.get('decision')
        claim.admin_note = request.POST.get('admin_note', '')

        # =======================================================
        # APPROVE CLAIM
        # =======================================================
        if decision == 'approve':
            claim.status = 'approved'
            claim.save()

            # Mark found item as returned
            item.status = 'returned'
            item.save()

            other_claims = Claim.objects.filter(
                item = item
            ).exclude(id=claim.id)

            for other in other_claims:
                other.status = 'rejected'
                other.save()

                #Notify other users
                Notification.objects.create(
                    user=other.claimed_by,
                    message=f'Your claim for "{item.item_name}" was automatically rejected'
                )

            # Notify student
            Notification.objects.create(
                user=claim.claimed_by,
                message=f"Your claim for '{claim.item.item_name}' has been APPROVED 🎉"
            )

            return redirect('dashboard')

        # =======================================================
        # REJECT CLAIM
        # =======================================================
        elif decision == 'reject':
            claim.status = 'rejected'
            claim.save()

            # Put the item back into "unclaimed" pool
            item.status = "unclaimed"
            item.save()

            # Reset matched lost item (if any)
            if hasattr(item, "matched_lost_item") and item.matched_lost_item:
                lost = item.matched_lost_item
                lost.status = "unmatched"
                lost.save()
                item.matched_lost_item = None
                item.save()

            # Notify student
            Notification.objects.create(
                user=claim.claimed_by,
                message=f"Your claim for '{claim.item.item_name}' has been REJECTED ❌"
            )

            # Notify finder (optional)
            Notification.objects.create(
                user=item.reported_by,
                message=f"The item you found ('{item.item_name}') was not matched and is again visible in Found Items."
            )

            return redirect('dashboard')

    # RENDER CLAIM REVIEW PAGE
    return render(request, 'claims/review_claim.html', {
        'claim': claim,
        'item': item,
        'matching_lost': matching_lost,
    })

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from .models import Claim

def is_admin(user):
    return user.is_superuser or user.role in ["admin", "staff"]


@user_passes_test(is_admin)
def approved_claims(request):
    claims = Claim.objects.filter(status="approved").select_related("item", "claimed_by")
    return render(request, "claims/approved_claims.html", {"claims": claims})


@user_passes_test(is_admin)
def rejected_claims(request):
    claims = Claim.objects.filter(status="rejected").select_related("item", "claimed_by")
    return render(request, "claims/rejected_claims.html", {"claims": claims})

@user_passes_test(is_admin)
def approved_claims(request):
    claims = Claim.objects.filter(status="approved").select_related("item", "claimed_by")
    return render(request, "claims/approved_claims.html", {"claims": claims})


@user_passes_test(is_admin)
def rejected_claims(request):
    claims = Claim.objects.filter(status="rejected").select_related("item", "claimed_by")
    return render(request, "claims/rejected_claims.html", {"claims": claims})
