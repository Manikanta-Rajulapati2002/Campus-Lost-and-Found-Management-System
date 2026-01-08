from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from users.models import User


class CustomUserCreationForm(UserCreationForm):
    # Basic user info
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)

    # Role
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, required=True)

    # Contact
    phone = forms.CharField(max_length=20, required=False)

    # Personal details
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    # Address details
    address_line1 = forms.CharField(max_length=255, required=True)
    address_line2 = forms.CharField(max_length=255, required=False)
    city = forms.CharField(max_length=100, required=True)
    state = forms.CharField(max_length=100, required=True)
    zip_code = forms.CharField(max_length=20, required=True)

    # Role-specific fields
    major = forms.CharField(max_length=100, required=False)          # For Students
    faculty_role = forms.CharField(max_length=100, required=False)   # For Faculty
    staff_role = forms.CharField(max_length=100, required=False)
    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'role',
            'phone',
            'date_of_birth',
            'address_line1',
            'address_line2',
            'city',
            'state',
            'zip_code',
            'major',
            'faculty_role',
            'staff_role',
            'password1',
            'password2',
        )

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')

        # Major required only for Students
        if role == 'student' and not cleaned_data.get('major'):
            self.add_error('major', "Major is required for students.")

        # Faculty role required only for Faculty
        if role == 'faculty' and not cleaned_data.get('faculty_role'):
            self.add_error('faculty_role', "Faculty role is required for faculty members.")
        
        # Staff role required only for Staff
        if role == 'staff' and not cleaned_data.get('staff_role'):
            self.add_error('staff_role', "Staff role is required for Staff members. ")

        return cleaned_data



class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label="Username", max_length=150)
    password = forms.CharField(label="Password", widget=forms.PasswordInput)
