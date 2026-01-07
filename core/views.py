"""
Views for Propmatics - Contentful-Primary Architecture
- Static content (properties, blogs, notifications): FROM CONTENTFUL
- User data (auth, profiles, preferences): FROM DATABASE
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings

from .models import User, Contact
from .forms import RegisterForm, ContactForm
from . import contentful_service as cf


def home(request):
    """Home page with featured properties and notifications from Contentful."""
    # Fetch from Contentful
    all_properties = cf.fetch_properties()
    notifications = cf.fetch_notifications(limit=10)
    
    # Get first 6 as featured (Contentful doesn't have featured flag by default)
    featured_properties = all_properties[:6]
    
    context = {
        'featured_properties': featured_properties,
        'notifications': notifications,
    }
    return render(request, 'core/home.html', context)


def property_list(request):
    """List all properties from Contentful with search and filters."""
    properties = cf.fetch_properties()
    
    # Search filter
    query = request.GET.get('q', '').lower()
    if query:
        properties = [
            p for p in properties 
            if query in p.get('title', '').lower() 
            or query in p.get('city', '').lower()
            or query in p.get('description', '').lower()
        ]
    
    # Type filter
    property_type = request.GET.get('type', '')
    if property_type:
        properties = [p for p in properties if p.get('property_type') == property_type]
    
    # Property types for filter dropdown
    property_types = [
        ('apartment', 'Apartment'),
        ('villa', 'Villa'),
        ('plot', 'Plot'),
        ('commercial', 'Commercial'),
        ('independent_house', 'Independent House'),
    ]
    
    context = {
        'properties': properties,
        'query': query,
        'property_type': property_type,
        'property_types': property_types,
    }
    return render(request, 'core/property_list.html', context)


def property_detail(request, slug):
    """Single property detail from Contentful."""
    property_data = cf.fetch_property_by_slug(slug)
    
    if not property_data:
        messages.error(request, 'Property not found.')
        return redirect('property_list')
    
    # Get related properties (same city)
    all_properties = cf.fetch_properties()
    related = [
        p for p in all_properties 
        if p.get('city') == property_data.get('city') 
        and p.get('slug') != slug
    ][:4]
    
    context = {
        'property': property_data,
        'related_properties': related,
    }
    return render(request, 'core/property_detail.html', context)


def post_property(request):
    """Submit property directly to Contentful (like propnz)."""
    if request.method == 'POST':
        # Get form data
        title = request.POST.get('title', '')
        property_type = request.POST.get('property_type', 'apartment')
        city = request.POST.get('city', '')
        location = request.POST.get('location', '')
        price = int(request.POST.get('price', 0) or 0)
        carpet_area = int(request.POST.get('carpet_area', 0) or 0)
        floor_number = int(request.POST.get('floor_number', 0) or 0)
        total_floors = int(request.POST.get('total_floors', 1) or 1)
        possession_date = request.POST.get('possession_date', '')
        loan_approved_by = request.POST.get('loan_approved_by', '')
        description = request.POST.get('description', '')
        developer_id = request.POST.get('developer_id', '')
        
        # Contact info
        contact_name = request.POST.get('contact_name', '')
        contact_email = request.POST.get('contact_email', '')
        contact_phone = request.POST.get('contact_phone', '')
        user_type = request.POST.get('user_type', 'buyer')
        
        # Image
        image = request.FILES.get('image')
        
        if not title or not contact_name or not contact_email:
            messages.error(request, 'Please fill in all required fields.')
        else:
            try:
                # Submit directly to Contentful
                entry_id = cf.submit_property_to_contentful(
                    title=title,
                    property_type=property_type,
                    city=city,
                    location=location,
                    price=price,
                    carpet_area=carpet_area,
                    floor_number=floor_number,
                    total_floors=total_floors,
                    possession_date=possession_date,
                    loan_approved_by=loan_approved_by,
                    description=f"{description}\n\nContact: {contact_name} ({contact_phone})",
                    developer_id=developer_id,
                    image=image,
                )
                
                if entry_id:
                    # Send email notification
                    try:
                        send_mail(
                            subject=f"New Property Submission: {title}",
                            message=f"A new property has been submitted to Contentful.\n\nTitle: {title}\nBy: {contact_name}\nEmail: {contact_email}\nPhone: {contact_phone}\nContentful Entry: {entry_id}",
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[settings.EMAIL_HOST_USER],
                            fail_silently=True,
                        )
                    except:
                        pass
                    
                    messages.success(request, 'Property submitted successfully!')
                    return redirect('home')
                else:
                    messages.error(request, 'Failed to submit property. Please try again.')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
    
    # Fetch developers from Contentful
    developers = cf.fetch_developers()
    
    context = {
        'developers': developers,
    }
    return render(request, 'core/post_property.html', context)


def blog_list(request):
    """List all blog posts from Contentful."""
    blogs = cf.fetch_blogs()
    
    return render(request, 'core/blog_list.html', {'blogs': blogs})


def blog_detail(request, slug):
    """Single blog post from Contentful."""
    blog = cf.fetch_blog_by_slug(slug)
    
    if not blog:
        messages.error(request, 'Blog post not found.')
        return redirect('blog_list')
    
    return render(request, 'core/blog_detail.html', {'blog': blog})


def services(request):
    """Services page - static content."""
    services_list = [
        {
            'name': 'Buy Property',
            'description': 'Find your dream home from our curated listings with transparent pricing.',
            'icon': 'fa-home',
        },
        {
            'name': 'Sell Property',
            'description': 'List your property and reach thousands of genuine buyers.',
            'icon': 'fa-hand-holding-usd',
        },
        {
            'name': 'Documentation',
            'description': 'Expert assistance with property registration and legal verification.',
            'icon': 'fa-file-signature',
        },
    ]
    return render(request, 'core/services.html', {'services': services_list})


def contact(request):
    """Contact form - saves to database."""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save()
            
            # Send email
            try:
                send_mail(
                    subject=f"Contact Form: {contact.subject or 'No Subject'}",
                    message=f"Name: {contact.name}\nEmail: {contact.email}\nPhone: {contact.phone}\n\nMessage:\n{contact.message}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.EMAIL_HOST_USER],
                    fail_silently=True,
                )
            except:
                pass
            
            messages.success(request, 'Thank you for contacting us!')
            return redirect('contact')
    else:
        form = ContactForm()
    
    return render(request, 'core/contact.html', {'form': form})


def register(request):
    """User registration - saves to database."""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('home')
    else:
        form = RegisterForm()
    
    return render(request, 'core/register.html', {'form': form})


def user_login(request):
    """User login."""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'core/login.html')


def user_logout(request):
    """User logout."""
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('home')


def search(request):
    """Search properties from Contentful."""
    query = request.GET.get('q', '').lower()
    properties = cf.fetch_properties()
    
    if query:
        properties = [
            p for p in properties 
            if query in p.get('title', '').lower() 
            or query in p.get('city', '').lower()
        ]
    
    return render(request, 'core/search.html', {'properties': properties, 'query': query})


@login_required
def dashboard(request):
    """User dashboard - profile and saved properties."""
    context = {
        'user': request.user,
    }
    return render(request, 'core/dashboard.html', context)
