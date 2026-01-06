from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q

from .models import Property, Blog, Notification, Contact, Service, Developer, User
from .forms import RegisterForm, PropertyForm, ContactForm


def home(request):
    """Home page with featured properties and notifications."""
    featured_properties = Property.objects.filter(is_published=True, featured=True)[:6]
    notifications = Notification.objects.filter(is_active=True)[:10]
    services = Service.objects.filter(is_active=True)[:6]
    
    context = {
        'featured_properties': featured_properties,
        'notifications': notifications,
        'services': services,
    }
    return render(request, 'core/home.html', context)


def property_list(request):
    """List all properties with search and filters."""
    properties = Property.objects.filter(is_published=True)
    
    # Search
    query = request.GET.get('q', '')
    if query:
        properties = properties.filter(
            Q(title__icontains=query) |
            Q(city__icontains=query) |
            Q(location__icontains=query) |
            Q(description__icontains=query)
        )
    
    # Filter by type
    property_type = request.GET.get('type', '')
    if property_type:
        properties = properties.filter(property_type=property_type)
    
    # Pagination
    paginator = Paginator(properties, 12)
    page = request.GET.get('page', 1)
    properties = paginator.get_page(page)
    
    context = {
        'properties': properties,
        'query': query,
        'property_type': property_type,
        'property_types': Property.PROPERTY_TYPES,
    }
    return render(request, 'core/property_list.html', context)


def property_detail(request, slug):
    """Single property detail page."""
    property = get_object_or_404(Property, slug=slug, is_published=True)
    related = Property.objects.filter(is_published=True, city=property.city).exclude(pk=property.pk)[:4]
    
    context = {
        'property': property,
        'related_properties': related,
    }
    return render(request, 'core/property_detail.html', context)


def post_property(request):
    """Form to submit a new property."""
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES)
        if form.is_valid():
            property = form.save(commit=False)
            property.is_published = False  # Needs admin approval
            property.save()
            
            # Send email notification
            try:
                send_mail(
                    subject=f"New Property Submission: {property.title}",
                    message=f"A new property has been submitted.\n\nTitle: {property.title}\nBy: {property.contact_name}\nEmail: {property.contact_email}\nPhone: {property.contact_phone}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.EMAIL_HOST_USER],
                    fail_silently=True,
                )
            except Exception:
                pass
            
            messages.success(request, 'Property submitted successfully! It will be reviewed and published soon.')
            return redirect('home')
    else:
        form = PropertyForm()
    
    developers = Developer.objects.all()
    context = {
        'form': form,
        'developers': developers,
    }
    return render(request, 'core/post_property.html', context)


def blog_list(request):
    """List all blog posts."""
    blogs = Blog.objects.filter(is_published=True)
    paginator = Paginator(blogs, 10)
    page = request.GET.get('page', 1)
    blogs = paginator.get_page(page)
    
    return render(request, 'core/blog_list.html', {'blogs': blogs})


def blog_detail(request, slug):
    """Single blog post."""
    blog = get_object_or_404(Blog, slug=slug, is_published=True)
    return render(request, 'core/blog_detail.html', {'blog': blog})


def services(request):
    """Services page."""
    services = Service.objects.filter(is_active=True)
    return render(request, 'core/services.html', {'services': services})


def contact(request):
    """Contact form."""
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
            except Exception:
                pass
            
            messages.success(request, 'Thank you for contacting us! We will get back to you soon.')
            return redirect('contact')
    else:
        form = ContactForm()
    
    return render(request, 'core/contact.html', {'form': form})


def register(request):
    """User registration."""
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
    """Search properties."""
    query = request.GET.get('q', '')
    properties = Property.objects.filter(is_published=True)
    
    if query:
        properties = properties.filter(
            Q(title__icontains=query) |
            Q(city__icontains=query) |
            Q(location__icontains=query)
        )
    
    return render(request, 'core/search.html', {'properties': properties, 'query': query})
