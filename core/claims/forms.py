from django import forms
from .models import Claim


class ClaimCreateForm(forms.ModelForm):
    where_lost = forms.CharField(
        required=True,
        label="Where did you lose this item?",
        widget=forms.TextInput(attrs={'placeholder': 'e.g., Library second floor'})
    )

    when_lost = forms.DateField(
        required=True,
        label="When did you lose this item?",
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    identifying_marks = forms.CharField(
        required=True,
        label="Describe identifying marks or details",
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'e.g., My wallet has initials inside'})
    )

    class Meta:
        model = Claim
        fields = ['message', 'where_lost', 'when_lost', 'identifying_marks']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Explain why this item belongs to you'})
        }


class ClaimReviewForm(forms.Form):
    decision = forms.ChoiceField(
        choices=(
            ('approve', 'Approve'),
            ('reject', 'Reject'),
            ('returned', 'Mark as Returned (item given back)'),
        ),
        widget=forms.RadioSelect
    )
    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text="Optional note about your decision."
    )
