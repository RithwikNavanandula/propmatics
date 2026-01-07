"""
Contentful CMA Integration for Propmatics
Syncs properties from Django to Contentful when they are created/published.
"""

import os
import time
import logging
import contentful_management
from django.conf import settings

logger = logging.getLogger(__name__)

# Contentful credentials from environment (MUST be set in .env or Render dashboard)
CONTENTFUL_SPACE_ID = os.getenv('CONTENTFUL_SPACE_ID', '')
CONTENTFUL_CMA_TOKEN = os.getenv('CONTENTFUL_CMA_TOKEN', '')
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


def get_contentful_client():
    """Get Contentful Management API client."""
    return contentful_management.Client(CONTENTFUL_CMA_TOKEN)


def geocode_location(location_name):
    """Convert location name to lat/lon coordinates."""
    if not location_name:
        return {'lat': 17.385, 'lon': 78.4867}  # Default to Hyderabad
    
    lower = location_name.lower()
    for city, coords in CITY_COORDS.items():
        if city in lower:
            return coords
    
    return {'lat': 17.385, 'lon': 78.4867}  # Default


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
                    {
                        'nodeType': 'text',
                        'value': para.strip(),
                        'marks': [],
                        'data': {}
                    }
                ]
            })
    
    if not content:
        content = [{
            'nodeType': 'paragraph',
            'data': {},
            'content': [{'nodeType': 'text', 'value': 'No description', 'marks': [], 'data': {}}]
        }]
    
    return {
        'nodeType': 'document',
        'data': {},
        'content': content
    }


def upload_image_to_contentful(image_file, title="Property Image"):
    """
    Upload an image file to Contentful and return the published asset.
    
    Args:
        image_file: Django UploadedFile or file path
        title: Title for the asset
    
    Returns:
        Asset ID if successful, None otherwise
    """
    try:
        client = get_contentful_client()
        space = client.spaces().find(CONTENTFUL_SPACE_ID)
        environment = space.environments().find(CONTENTFUL_ENVIRONMENT)
        
        # Read file content
        if hasattr(image_file, 'read'):
            # Django UploadedFile
            content = image_file.read()
            filename = getattr(image_file, 'name', 'image.jpg')
            content_type = getattr(image_file, 'content_type', 'image/jpeg')
        else:
            # File path
            with open(image_file, 'rb') as f:
                content = f.read()
            filename = os.path.basename(image_file)
            content_type = 'image/jpeg'
        
        # Create upload
        upload = environment.uploads().create(content)
        
        # Create asset
        asset = environment.assets().create(None, {
            'fields': {
                'title': {'en-US': title},
                'file': {
                    'en-US': {
                        'contentType': content_type,
                        'fileName': filename,
                        'uploadFrom': {
                            'sys': {
                                'type': 'Link',
                                'linkType': 'Upload',
                                'id': upload.id
                            }
                        }
                    }
                }
            }
        })
        
        # Process asset
        asset.process()
        time.sleep(3)  # Wait for processing
        
        # Refresh and publish
        asset = environment.assets().find(asset.id)
        asset.publish()
        
        logger.info(f"Uploaded image to Contentful: {asset.id}")
        return asset.id
        
    except Exception as e:
        logger.error(f"Failed to upload image to Contentful: {e}")
        return None


def sync_property_to_contentful(property_instance, developer_id=None):
    """
    Sync a Django Property instance to Contentful.
    
    Args:
        property_instance: Django Property model instance
        developer_id: Optional Contentful developer entry ID
    
    Returns:
        Contentful entry ID if successful, None otherwise
    """
    try:
        client = get_contentful_client()
        space = client.spaces().find(CONTENTFUL_SPACE_ID)
        environment = space.environments().find(CONTENTFUL_ENVIRONMENT)
        
        # Prepare location
        location = geocode_location(property_instance.city or property_instance.location)
        
        # Build rich text description
        description = build_rich_text(property_instance.description)
        
        # Prepare fields
        fields = {
            'title': {'en-US': property_instance.title},
            'slug': {'en-US': property_instance.slug},
            'propertyType': {'en-US': property_instance.property_type},
            'location': {'en-US': location},
            'price': {'en-US': property_instance.price},
            'city': {'en-US': property_instance.city or ''},
            'description': {'en-US': description},
        }
        
        # Optional fields
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
        
        # Upload image if exists
        if property_instance.image:
            image_path = property_instance.image.path
            if os.path.exists(image_path):
                asset_id = upload_image_to_contentful(image_path, property_instance.title)
                if asset_id:
                    fields['image'] = {
                        'en-US': {
                            'sys': {
                                'type': 'Link',
                                'linkType': 'Asset',
                                'id': asset_id
                            }
                        }
                    }
        
        # Link developer if provided
        if developer_id:
            fields['developer'] = {
                'en-US': {
                    'sys': {
                        'type': 'Link',
                        'linkType': 'Entry',
                        'id': developer_id
                    }
                }
            }
        
        # Create entry
        entry = environment.entries().create(None, {
            'content_type_id': 'property',
            'fields': fields
        })
        
        # Publish entry
        entry.publish()
        
        logger.info(f"Synced property to Contentful: {entry.id} - {property_instance.title}")
        return entry.id
        
    except Exception as e:
        logger.error(f"Failed to sync property to Contentful: {e}")
        return None


def get_contentful_developers():
    """Fetch all developers from Contentful."""
    try:
        client = get_contentful_client()
        space = client.spaces().find(CONTENTFUL_SPACE_ID)
        environment = space.environments().find(CONTENTFUL_ENVIRONMENT)
        
        entries = environment.entries().all({'content_type': 'developer'})
        
        developers = []
        for entry in entries:
            name = entry.fields().get('name', {}).get('en-US', 'Unknown')
            developers.append({
                'id': entry.id,
                'name': name
            })
        
        return developers
        
    except Exception as e:
        logger.error(f"Failed to fetch developers from Contentful: {e}")
        return []
