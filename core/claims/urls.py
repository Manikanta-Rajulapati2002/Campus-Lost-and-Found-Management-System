from django.urls import path
from .views import (
    create_claim,
    my_claims,
    pending_claims,
    review_claim,
    claim_confirmation,
    approved_claims,
    rejected_claims,
)

urlpatterns = [
    path('create/<int:item_id>/', create_claim, name='create_claim'),
    path('my/', my_claims, name='my_claims'),
    path('pending/', pending_claims, name='pending_claims'),
    path('review/<int:claim_id>/', review_claim, name='review_claim'),
    path('confirm/<int:item_id>/', claim_confirmation, name= 'claim_confirmation'),
    path('approved/', approved_claims, name='approved_claims'),
    path('rejected/', rejected_claims, name='rejected_claims'),

]
