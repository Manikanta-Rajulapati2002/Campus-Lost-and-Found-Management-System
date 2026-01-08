from django import forms
from .models import Item



class LostItemForm(forms.ModelForm):

    # Make it NOT required, default to "unknown"
    time_choice = forms.ChoiceField(
        choices=[
            ("unknown", "I don't know the time"),
            ("exact", "I know the exact time"),
            ("range", "I know the time range"),
        ],
        required=False,
        initial="unknown",
        label="Lost Time Information"
    )

    class Meta:
        model = Item
        fields = [
            'item_name',
            'description',
            'category',
            'color',
            'location',

            # NEW LOST FIELDS
            'date_lost',
            'time_lost_exact',
            'time_lost_from',
            'time_lost_to',

            'image',
        ]

        widgets = {
            "date_lost": forms.DateInput(attrs={'type': 'date'}),
            "time_lost_exact": forms.TimeInput(attrs={'type': 'time'}),
            "time_lost_from": forms.TimeInput(attrs={'type': 'time'}),
            "time_lost_to": forms.TimeInput(attrs={'type': 'time'}),
        }

    def clean(self):
        cleaned = super().clean()
        # If the field is missing from POST, treat as "unknown"
        choice = cleaned.get("time_choice") or "unknown"

        exact = cleaned.get("time_lost_exact")
        t_from = cleaned.get("time_lost_from")
        t_to = cleaned.get("time_lost_to")

        # CASE 1 → UNKNOWN TIME (clear all time fields)
        if choice == "unknown":
            cleaned["time_lost_exact"] = None
            cleaned["time_lost_from"] = None
            cleaned["time_lost_to"] = None

        # CASE 2 → EXACT TIME REQUIRED
        elif choice == "exact":
            if not exact:
                raise forms.ValidationError("Please enter the exact time.")
            cleaned["time_lost_from"] = None
            cleaned["time_lost_to"] = None

        # CASE 3 → RANGE REQUIRED
        elif choice == "range":
            if not t_from or not t_to:
                raise forms.ValidationError("Please enter a valid time range.")
            if t_from >= t_to:
                raise forms.ValidationError("Start time must be earlier than end time.")
            cleaned["time_lost_exact"] = None

        return cleaned



class FoundItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = [
            'item_name',
            'description',
            'category',
            'color',
            'location',

            # FOUND FIELDS
            'date_found',
            'time_found',

            'image',
        ]

        widgets = {
            "date_found": forms.DateInput(attrs={'type': 'date'}),
            "time_found": forms.TimeInput(attrs={'type': 'time'}),
        }

    # Make image required ONLY for found items
    def clean_image(self):
        image = self.cleaned_data.get("image")

        if not image:
            raise forms.ValidationError("You must upload an image for a FOUND item.")

        return image




class ItemSearchForm(forms.Form):
    keyword = forms.CharField(required=False, label="Keyword (name/description)")
    category = forms.CharField(required=False, label="Category")
    color = forms.CharField(required=False, label="Color")
    location = forms.CharField(required=False, label="Location")

    item_type = forms.ChoiceField(
        required=False,
        choices=(('', 'Any'),) + Item.ITEM_TYPE_CHOICES,
        label="Type (Lost/Found)"
    )

    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="From date"
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="To date"
    )

class FoundFromLostItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['location', 'date_found', 'time_found', 'description', 'image']

        widgets = {
            "date_found": forms.DateInput(attrs={'type': 'date'}),
            "time_found": forms.TimeInput(attrs={'type': 'time'}),
        }

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if not image:
            raise forms.ValidationError("An image is required when reporting a found item.")
        return image
