"""
Contentful Integration for Propmatics
- Content Delivery API (CDA): Fetching data FROM Contentful
- Content Management API (CMA): Syncing data TO Contentful
"""

import os
import time
import logging
import contentful
import contentful_management
from django.conf import settings

logger = logging.getLogger(__name__)

# ================== CREDENTIALS ==================
# MUST be set in .env or Render dashboard
CONTENTFUL_SPACE_ID = os.getenv('CONTENTFUL_SPACE_ID', '')
CONTENTFUL_ACCESS_TOKEN = os.getenv('CONTENTFUL_ACCESS_TOKEN', '')  # For READING
CONTENTFUL_CMA_TOKEN = os.getenv('CONTENTFUL_CMA_TOKEN', '')  # For WRITING
CONTENTFUL_ENVIRONMENT = 'master'

# City coordinates for geocoding
CITY_COORDS = {
    'hyderabad': {'lat': 17.385, 'lon': 78.4867},
    'mumbai': {'lat': 19.076, 'lon': 72.8777},
    'bangalore': {'lat': 12.9716, 'lon': 77.5946},
    'delhi': {'lat': 28.6139, 'lon': 77.209},
    'chennai': {'lat': 13.0827, 'lon': 80.2707},
    'pune': {'lat': 18.5204, 'lon': 73.8567},
    'kolkata': {'lat': 22.5726, 'lon': 88.3639},
}


# ================== DELIVERY API (READING) ==================

def get_delivery_client():
    """Get Contentful Delivery API client for READING data."""
    if not CONTENTFUL_SPACE_ID or not CONTENTFUL_ACCESS_TOKEN:
        logger.warning("Contentful credentials not configured")
        return None
    return contentful.Client(CONTENTFUL_SPACE_ID, CONTENTFUL_ACCESS_TOKEN)


def fetch_properties():
    """Fetch all properties from Contentful (matches propnz fetchProperties)."""
    try:
        client = get_delivery_client()
        if not client:
            return []
        
        entries = client.entries({
            'content_type': 'property',
            'order': '-sys.createdAt',
        })
        
        properties = []
        for entry in entries:
            properties.append(parse_property_entry(entry))
        
        return properties
    except Exception as e:
        logger.error(f"Error fetching properties from Contentful: {e}")
        return []


def fetch_property_by_slug(slug):
    """Fetch single property by slug from Contentful (matches propnz fetchPropertyBySlug)."""
    try:
        client = get_delivery_client()
        if not client:
            return None
        
        entries = client.entries({
            'content_type': 'property',
            'fields.slug': slug,
            'limit': 1,
        })
        
        if entries:
            return parse_property_entry(entries[0])
        return None
    except Exception as e:
        logger.error(f"Error fetching property {slug} from Contentful: {e}")
        return None


def fetch_blogs():
    """Fetch all blog posts from Contentful (matches propnz fetchBlogs)."""
    try:
        client = get_delivery_client()
        if not client:
            return []
        
        entries = client.entries({
            'content_type': 'blogPost',
            'order': '-sys.createdAt',
        })
        
        blogs = []
        for entry in entries:
            blogs.append(parse_blog_entry(entry))
        
        return blogs
    except Exception as e:
        logger.error(f"Error fetching blogs from Contentful: {e}")
        return []


def fetch_blog_by_slug(slug):
    """Fetch single blog post by slug from Contentful."""
    try:
        client = get_delivery_client()
        if not client:
            return None
        
        entries = client.entries({
            'content_type': 'blogPost',
            'fields.slug': slug,
            'limit': 1,
        })
        
        if entries:
            return parse_blog_entry(entries[0])
        return None
    except Exception as e:
        logger.error(f"Error fetching blog {slug} from Contentful: {e}")
        return None


def fetch_notifications(limit=10):
    """Fetch notifications from Contentful (matches propnz fetchNotifications)."""
    try:
        client = get_delivery_client()
        if not client:
            return []
        
        entries = client.entries({
            'content_type': 'notification',
            'order': '-fields.date',
            'limit': limit,
        })
        
        notifications = []
        for entry in entries:
            notifications.append(parse_notification_entry(entry))
        
        return notifications
    except Exception as e:
        logger.error(f"Error fetching notifications from Contentful: {e}")
        return []


def fetch_developers():
    """Fetch all developers from Contentful."""
    try:
        client = get_delivery_client()
        if not client:
            return []
        
        entries = client.entries({
            'content_type': 'developer',
        })
        
        developers = []
        for entry in entries:
            developers.append({
                'id': entry.sys.get('id', ''),
                'name': getattr(entry, 'name', 'Unknown'),
                'logo': get_asset_url(getattr(entry, 'logo', None)),
            })
        
        return developers
    except Exception as e:
        logger.error(f"Error fetching developers from Contentful: {e}")
        return []


# ================== PARSING HELPERS ==================

def get_asset_url(asset):
    """Extract URL from Contentful asset."""
    if not asset:
        return None
    try:
        if hasattr(asset, 'url'):
            url = asset.url()
            return f"https:{url}" if url.startswith('//') else url
        if hasattr(asset, 'fields') and 'file' in asset.fields():
            file_info = asset.fields()['file']
            url = file_info.get('url', '')
            return f"https:{url}" if url.startswith('//') else url
    except:
        pass
    return None


def parse_rich_text(rich_text):
    """Convert Contentful Rich Text to plain text."""
    if not rich_text:
        return ""
    
    try:
        if isinstance(rich_text, str):
            return rich_text
        
        # Extract text from rich text document
        if hasattr(rich_text, 'content'):
            content = rich_text.content
        elif isinstance(rich_text, dict) and 'content' in rich_text:
            content = rich_text['content']
        else:
            return str(rich_text)
        
        text_parts = []
        for node in content:
            if isinstance(node, dict):
                if node.get('nodeType') == 'paragraph':
                    for child in node.get('content', []):
                        if child.get('nodeType') == 'text':
                            text_parts.append(child.get('value', ''))
            elif hasattr(node, 'content'):
                for child in node.content:
                    if hasattr(child, 'value'):
                        text_parts.append(child.value)
        
        return '\n'.join(text_parts)
    except Exception as e:
        logger.warning(f"Error parsing rich text: {e}")
        return str(rich_text) if rich_text else ""


def parse_property_entry(entry):
    """Parse Contentful property entry to dict."""
    try:
        # Get image URL
        image_url = None
        if hasattr(entry, 'image') and entry.image:
            image_url = get_asset_url(entry.image)
        
        # Get location
        location = getattr(entry, 'location', None)
        lat, lon = 17.385, 78.4867  # Default Hyderabad
        if location:
            if hasattr(location, 'lat'):
                lat = location.lat
                lon = location.lon
            elif isinstance(location, dict):
                lat = location.get('lat', lat)
                lon = location.get('lon', lon)
        
        # Get developer
        developer = None
        if hasattr(entry, 'developer') and entry.developer:
            dev = entry.developer
            developer = {
                'id': dev.sys.get('id', '') if hasattr(dev, 'sys') else '',
                'name': getattr(dev, 'name', 'Unknown'),
            }
        
        return {
            'id': entry.sys.get('id', ''),
            'title': getattr(entry, 'title', ''),
            'slug': getattr(entry, 'slug', ''),
            'property_type': getattr(entry, 'propertyType', ''),
            'price': getattr(entry, 'price', 0),
            'city': getattr(entry, 'city', ''),
            'location': {'lat': lat, 'lon': lon},
            'description': parse_rich_text(getattr(entry, 'description', '')),
            'carpet_area': getattr(entry, 'carpetArea', None),
            'floor_number': getattr(entry, 'floorNumber', None),
            'total_floors': getattr(entry, 'totalNoOfFloors', None),
            'possession_date': getattr(entry, 'pocessionByDate', None),
            'loan_approved_by': getattr(entry, 'loanApprovedBy', ''),
            'image_url': image_url,
            'developer': developer,
            'created_at': entry.sys.get('createdAt', ''),
        }
    except Exception as e:
        logger.error(f"Error parsing property entry: {e}")
        return {'title': 'Error', 'slug': ''}


def parse_blog_entry(entry):
    """Parse Contentful blog entry to dict."""
    try:
        image_url = None
        if hasattr(entry, 'image') and entry.image:
            image_url = get_asset_url(entry.image)
        
        return {
            'id': entry.sys.get('id', ''),
            'title': getattr(entry, 'title', ''),
            'slug': getattr(entry, 'slug', ''),
            'content': parse_rich_text(getattr(entry, 'content', '')),
            'excerpt': getattr(entry, 'excerpt', ''),
            'image_url': image_url,
            'author': getattr(entry, 'author', 'Admin'),
            'created_at': entry.sys.get('createdAt', ''),
        }
    except Exception as e:
        logger.error(f"Error parsing blog entry: {e}")
        return {'title': 'Error', 'slug': ''}


def parse_notification_entry(entry):
    """Parse Contentful notification entry to dict."""
    try:
        doc_url = None
        if hasattr(entry, 'document') and entry.document:
            doc_url = get_asset_url(entry.document)
        
        return {
            'id': entry.sys.get('id', ''),
            'title': getattr(entry, 'title', ''),
            'subject': getattr(entry, 'subject', ''),
            'date': getattr(entry, 'date', ''),
            'document_url': doc_url,
        }
    except Exception as e:
        logger.error(f"Error parsing notification entry: {e}")
        return {'title': 'Error'}


# ================== MANAGEMENT API (WRITING) ==================

def get_management_client():
    """Get Contentful Management API client for WRITING data."""
    if not CONTENTFUL_CMA_TOKEN:
        logger.warning("Contentful CMA token not configured")
        return None
    return contentful_management.Client(CONTENTFUL_CMA_TOKEN)


def geocode_location(location_name):
    """Convert location name to lat/lon coordinates."""
    if not location_name:
        return {'lat': 17.385, 'lon': 78.4867}
    
    lower = location_name.lower()
    for city, coords in CITY_COORDS.items():
        if city in lower:
            return coords
    
    return {'lat': 17.385, 'lon': 78.4867}


def build_rich_text(text):
    """Convert plain text to Contentful Rich Text format."""
    if not text:
        text = "No description provided."
    
    paragraphs = text.split('\n')
    content = []
    
    for para in paragraphs:
        if para.strip():
            content.append({
                'nodeType': 'paragraph',
                'data': {},
                'content': [
                    {'nodeType': 'text', 'value': para.strip(), 'marks': [], 'data': {}}
                ]
            })
    
    if not content:
        content = [{'nodeType': 'paragraph', 'data': {}, 'content': [
            {'nodeType': 'text', 'value': 'No description', 'marks': [], 'data': {}}
        ]}]
    
    return {'nodeType': 'document', 'data': {}, 'content': content}


def upload_image_to_contentful(image_file, title="Property Image"):
    """Upload an image file to Contentful."""
    try:
        client = get_management_client()
        if not client:
            return None
        
        space = client.spaces().find(CONTENTFUL_SPACE_ID)
        environment = space.environments().find(CONTENTFUL_ENVIRONMENT)
        
        if hasattr(image_file, 'read'):
            content = image_file.read()
            filename = getattr(image_file, 'name', 'image.jpg')
            content_type = getattr(image_file, 'content_type', 'image/jpeg')
        else:
            with open(image_file, 'rb') as f:
                content = f.read()
            filename = os.path.basename(image_file)
            content_type = 'image/jpeg'
        
        upload = environment.uploads().create(content)
        asset = environment.assets().create(None, {
            'fields': {
                'title': {'en-US': title},
                'file': {
                    'en-US': {
                        'contentType': content_type,
                        'fileName': filename,
                        'uploadFrom': {'sys': {'type': 'Link', 'linkType': 'Upload', 'id': upload.id}}
                    }
                }
            }
        })
        
        asset.process()
        time.sleep(3)
        asset = environment.assets().find(asset.id)
        asset.publish()
        
        logger.info(f"Uploaded image to Contentful: {asset.id}")
        return asset.id
    except Exception as e:
        logger.error(f"Failed to upload image: {e}")
        return None


def sync_property_to_contentful(property_instance, developer_id=None):
    """Sync a Django Property instance TO Contentful."""
    try:
        client = get_management_client()
        if not client:
            return None
        
        space = client.spaces().find(CONTENTFUL_SPACE_ID)
        environment = space.environments().find(CONTENTFUL_ENVIRONMENT)
        
        location = geocode_location(property_instance.city or property_instance.location)
        description = build_rich_text(property_instance.description)
        
        fields = {
            'title': {'en-US': property_instance.title},
            'slug': {'en-US': property_instance.slug},
            'propertyType': {'en-US': property_instance.property_type},
            'location': {'en-US': location},
            'price': {'en-US': property_instance.price},
            'city': {'en-US': property_instance.city or ''},
            'description': {'en-US': description},
        }
        
        if property_instance.carpet_area:
            fields['carpetArea'] = {'en-US': property_instance.carpet_area}
        if property_instance.floor_number:
            fields['floorNumber'] = {'en-US': property_instance.floor_number}
        if property_instance.total_floors:
            fields['totalNoOfFloors'] = {'en-US': property_instance.total_floors}
        if property_instance.possession_date:
            fields['pocessionByDate'] = {'en-US': str(property_instance.possession_date)}
        if property_instance.loan_approved_by:
            fields['loanApprovedBy'] = {'en-US': property_instance.loan_approved_by}
        
        if property_instance.image and os.path.exists(property_instance.image.path):
            asset_id = upload_image_to_contentful(property_instance.image.path, property_instance.title)
            if asset_id:
                fields['image'] = {'en-US': {'sys': {'type': 'Link', 'linkType': 'Asset', 'id': asset_id}}}
        
        if developer_id:
            fields['developer'] = {'en-US': {'sys': {'type': 'Link', 'linkType': 'Entry', 'id': developer_id}}}
        
        entry = environment.entries().create(None, {'content_type_id': 'property', 'fields': fields})
        entry.publish()
        
        logger.info(f"Synced property to Contentful: {entry.id}")
        return entry.id
    except Exception as e:
        logger.error(f"Failed to sync property: {e}")
        return None
