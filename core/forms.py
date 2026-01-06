from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Property, Contact


class RegisterForm(UserCreationForm):
    """User registration form."""
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=False)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'role', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data.get('phone', '')
        user.role = self.cleaned_data['role']
        if commit:
            user.save()
        return user


class PropertyForm(forms.ModelForm):
    """Property submission form."""
    class Meta:
        model = Property
        fields = [
            'title', 'property_type', 'developer', 'city', 'location',
            'price', 'carpet_area', 'floor_number', 'total_floors',
            'possession_date', 'loan_approved_by', 'description', 'image',
            'contact_name', 'contact_email', 'contact_phone', 'user_type'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'possession_date': forms.DateInput(attrs={'type': 'date'}),
        }


class ContactForm(forms.ModelForm):
    """Contact form."""
    class Meta:
        model = Contact
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5}),
        }
