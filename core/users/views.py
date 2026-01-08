from django.shortcuts import render,redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView 
from django.urls import reverse_lazy
from templates.users.forms import CustomUserCreationForm, CustomAuthenticationForm
from items.models import Item
from claims.models import Claim
from users.models import Notification, User

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        
        if form.is_valid():
            # Create user but don't save yet
            user = form.save(commit=False)

            # Assign normal Django user fields
            user.first_name = form.cleaned_data.get('first_name')
            user.last_name = form.cleaned_data.get('last_name')
            user.email = form.cleaned_data.get('email')

            # Assign role
            user.role = form.cleaned_data.get('role')

            # Personal details
            user.date_of_birth = form.cleaned_data.get('date_of_birth')
            user.phone = form.cleaned_data.get('phone')

            # Address details
            user.address_line1 = form.cleaned_data.get('address_line1')
            user.address_line2 = form.cleaned_data.get('address_line2')
            user.city = form.cleaned_data.get('city')
            user.state = form.cleaned_data.get('state')
            user.zip_code = form.cleaned_data.get('zip_code')

            # Role-specific fields
            if user.role == 'student':
                user.major = form.cleaned_data.get('major')
                user.faculty_role = None  # not needed for students
                user.staff_role = None
            elif user.role == 'faculty':
                user.faculty_role = form.cleaned_data.get('faculty_role')
                user.major = None  # faculty is not a student
                user.staff_role = None
            
            elif user.role == 'staff':
                user.staff_role = form.cleaned_data.get('staff_role')
                user.major = None
                user.faculty_role = None
            else:
                # Staff or Admin: no major / faculty role required
                user.major = None
                user.faculty_role = None
                user.staff_role = None

            user.save()  # Now save the user with updated fields

            # Auto-login user
            login(request, user)
            return redirect('dashboard')

    else:
        form = CustomUserCreationForm()

    return render(request, 'users/signup.html', {'form': form})


class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    authentication_form = CustomAuthenticationForm

    def get_success_url(self):
        return reverse_lazy('dashboard')


def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard_view(request):

    # If admin or superuser → redirect immediately to staff dashboard
    if request.user.role == "admin" or request.user.is_superuser:
        return redirect('staff_dashboard')

    # Fetch unread notifications for the logged-in user
    notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).order_by('-created_at')

    # Mark them as read after showing
    for note in notifications:
        note.is_read = True
        note.save()

    # Render student/staff dashboard
    return render(request, 'users/dashboard.html', {
        "notifications": notifications
    })



def is_staff_or_admin(user):
    if user.is_superuser or user.is_staff:
        return True
    return getattr(user, 'role', None) in ('staff', 'admin')


@login_required
@user_passes_test(is_staff_or_admin)
def staff_dashboard_view(request):
    total_lost = Item.objects.filter(item_type='lost').count()
    total_found = Item.objects.filter(item_type='found').count()

    unmatched_lost = Item.objects.filter(item_type='lost', status='unmatched').count()
    unmatched_found = Item.objects.filter(item_type='found', status='unmatched').count()

    pending_claims = Claim.objects.filter(status='pending').count()
    approved_claims = Claim.objects.filter(status='approved').count()
    rejected_claims = Claim.objects.filter(status='rejected').count()
    returned_items = Item.objects.filter(status='returned').count()

    context = {
        'total_lost': total_lost,
        'total_found': total_found,
        'unmatched_lost': unmatched_lost,
        'unmatched_found': unmatched_found,
        'pending_claims': pending_claims,
        'approved_claims': approved_claims,
        'rejected_claims': rejected_claims,
        'returned_items': returned_items,
    }
    return render(request, 'users/staff_dashboard.html', context)