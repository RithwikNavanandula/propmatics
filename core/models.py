from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from django.urls import reverse


class User(AbstractUser):
    """Custom User model with roles."""
    ROLE_CHOICES = [
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
        ('agent', 'Agent'),
        ('document_writer', 'Document Writer'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='buyer')
    phone = models.CharField(max_length=20, blank=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Developer(models.Model):
    """Property Developer/Builder."""
    name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='developers/', blank=True, null=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Property(models.Model):
    """Real Estate Property Listing."""
    PROPERTY_TYPES = [
        ('independent_villa', 'Independent Villa'),
        ('standalone_apartment', 'Standalone Apartment'),
        ('towers', 'Towers'),
        ('gated_community', 'Gated Community'),
    ]
    
    LOAN_APPROVED_BY = [
        ('sbi', 'State Bank Of India'),
        ('pnb', 'Punjab National Bank'),
        ('icici', 'ICICI Bank'),
        ('hdfc', 'HDFC Bank'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=350, unique=True, blank=True)
    property_type = models.CharField(max_length=30, choices=PROPERTY_TYPES, default='standalone_apartment')
    developer = models.ForeignKey(Developer, on_delete=models.SET_NULL, null=True, blank=True, related_name='properties')
    
    # Location
    city = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=300, blank=True, help_text="Full address or area name")
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    
    # Pricing
    price = models.PositiveIntegerField(help_text="Price in INR")
    
    # Property Details
    carpet_area = models.PositiveIntegerField(help_text="Carpet area in sq.ft", null=True, blank=True)
    floor_number = models.PositiveIntegerField(null=True, blank=True)
    total_floors = models.PositiveIntegerField(null=True, blank=True)
    possession_date = models.DateField(null=True, blank=True)
    loan_approved_by = models.CharField(max_length=20, choices=LOAN_APPROVED_BY, blank=True)
    
    # Description
    description = models.TextField(blank=True)
    
    # Media
    image = models.ImageField(upload_to='properties/', blank=True, null=True)
    video = models.FileField(upload_to='properties/videos/', blank=True, null=True, help_text="Property walkthrough video")
    
    # Metadata
    is_published = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Contact Info (for user-submitted properties)
    contact_name = models.CharField(max_length=100, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    user_type = models.CharField(max_length=50, blank=True, help_text="Buyer/Seller/Agent")

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            self.slug = f"{base_slug}-{self.pk or 'new'}"
        super().save(*args, **kwargs)
        if 'new' in self.slug:
            self.slug = f"{slugify(self.title)}-{self.pk}"
            super().save(update_fields=['slug'])

    def get_absolute_url(self):
        return reverse('property_detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Properties"
        ordering = ['-created_at']


class PropertyImage(models.Model):
    """Additional images for a property."""
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='properties/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Image for {self.property.title}"


class PropertyVideo(models.Model):
    """Additional videos for a property."""
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='videos')
    video = models.FileField(upload_to='properties/videos/')
    title = models.CharField(max_length=200, blank=True, help_text="Video title (e.g., 'Living Room Tour')")
    caption = models.CharField(max_length=500, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Video: {self.title or 'Untitled'} for {self.property.title}"


class Blog(models.Model):
    """Blog posts."""
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=350, unique=True, blank=True)
    content = models.TextField()
    excerpt = models.TextField(max_length=500, blank=True)
    image = models.ImageField(upload_to='blogs/', blank=True, null=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog_detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']


class Notification(models.Model):
    """Site notifications/announcements."""
    title = models.CharField(max_length=300)
    subject = models.CharField(max_length=500, blank=True)
    document = models.FileField(upload_to='notifications/', blank=True, null=True)
    date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-date']


class Contact(models.Model):
    """Contact form submissions."""
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject or 'No Subject'}"

    class Meta:
        ordering = ['-created_at']


class Service(models.Model):
    """Services offered."""
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    description = models.TextField()
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")
    image = models.ImageField(upload_to='services/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order', 'name']
