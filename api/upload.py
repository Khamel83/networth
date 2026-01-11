"""
Vercel Serverless Function: Photo Upload API

Handles avatar photo uploads:
- Accepts pre-processed image files (200x200 JPEG from frontend)
- Validates file size (max 2MB)
- Uploads to Supabase Storage 'avatar' bucket via REST API
- Updates player.avatar_url

Image processing moved to frontend (Canvas API) for faster builds.
Uses Supabase REST API (no Python storage client).
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import io
import base64
import uuid
import httpx
from datetime import datetime


def get_player_by_email(email):
    """Get player from database by email (password-based auth)"""
    from api.supabase_http import table

    if not email:
        return None

    try:
        result = table('players').select('*').eq('email', email.lower()).single().execute()
        if result.data:
            return result.data[0] if isinstance(result.data, list) else result.data
    except Exception:
        pass
    return None


def get_supabase_config():
    """Get Supabase URL and key from environment"""
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_ANON_KEY')
    return url, key


def get_storage_url(path=''):
    """Get Supabase Storage URL"""
    base_url, _ = get_supabase_config()
    return f'{base_url}/storage/v1/object/{path}'


def get_storage_headers():
    """Get headers for Storage API requests"""
    _, key = get_supabase_config()
    return {
        'apikey': key,
        'Authorization': f'Bearer {key}',
    }


def upload_to_storage(filename, image_data, content_type='image/jpeg'):
    """Upload file to Supabase Storage via REST API"""
    url = get_storage_url(f'avatar/{filename}')
    headers = get_storage_headers()
    headers['Content-Type'] = content_type

    response = httpx.put(url, headers=headers, content=image_data)
    if response.status_code not in (200, 201):
        raise Exception(f"Storage upload failed: {response.text}")
    return response


def delete_from_storage(filename):
    """Delete file from Supabase Storage via REST API"""
    url = get_storage_url(f'avatar/{filename}')
    headers = get_storage_headers()

    response = httpx.delete(url, headers=headers)
    # Ignore errors if file doesn't exist
    return response


def get_public_url(filename):
    """Get public URL for a storage file"""
    base_url, _ = get_supabase_config()
    return f'{base_url}/storage/v1/object/public/avatar/{filename}'


def parse_multipart_form(body, content_type):
    """Parse multipart/form-data to extract file"""
    # Extract boundary from content type
    boundary = None
    for part in content_type.split(';'):
        part = part.strip()
        if part.startswith('boundary='):
            boundary = part[9:].strip('"')
            break

    if not boundary:
        raise ValueError("No boundary found in multipart form data")

    # Split by boundary
    boundary_bytes = f'--{boundary}'.encode()
    parts = body.split(boundary_bytes)

    for part in parts:
        if b'Content-Disposition' not in part:
            continue

        # Parse headers and content
        if b'\r\n\r\n' in part:
            headers_raw, content = part.split(b'\r\n\r\n', 1)
        elif b'\n\n' in part:
            headers_raw, content = part.split(b'\n\n', 1)
        else:
            continue

        headers_str = headers_raw.decode('utf-8', errors='ignore')

        # Check if this is the file field
        if 'name="file"' in headers_str or 'name="avatar"' in headers_str or 'name="photo"' in headers_str:
            # Extract content type
            file_content_type = 'image/jpeg'
            for line in headers_str.split('\n'):
                if 'Content-Type:' in line:
                    file_content_type = line.split(':', 1)[1].strip()
                    break

            # Remove trailing boundary markers
            content = content.rstrip(b'\r\n-')

            return content, file_content_type

    raise ValueError("No file found in form data")


def parse_json_base64(body):
    """Parse JSON body with base64-encoded image"""
    data = json.loads(body)

    if 'image' not in data:
        raise ValueError("No image field in JSON body")

    image_data = data['image']
    content_type = data.get('content_type', 'image/jpeg')

    # Handle data URL format
    if image_data.startswith('data:'):
        # Format: data:image/jpeg;base64,/9j/4AAQ...
        header, encoded = image_data.split(',', 1)
        if 'image/' in header:
            content_type = header.split(';')[0].split(':')[1]
        image_bytes = base64.b64decode(encoded)
    else:
        # Plain base64
        image_bytes = base64.b64decode(image_data)

    return image_bytes, content_type


class handler(BaseHTTPRequestHandler):
    # Max file size: 2MB
    MAX_FILE_SIZE = 2 * 1024 * 1024

    # Allowed content types
    ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/jpg']

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_POST(self):
        """Handle photo upload"""
        try:
            from api.supabase_http import table

            # Get email from Authorization header
            auth_header = self.headers.get('Authorization', '')
            email = None

            if auth_header.startswith('Bearer '):
                token_or_email = auth_header.replace('Bearer ', '')
                if '@' in token_or_email:
                    email = token_or_email.lower()
                else:
                    self._send_error(401, "Please provide your email in Authorization header")
                    return

            if not email:
                email = self.headers.get('X-Player-Email', '').lower()

            if not email:
                self._send_error(401, "Authentication required")
                return

            # Get player record
            player = get_player_by_email(email)
            if not player:
                self._send_error(404, "Player profile not found")
                return

            player_id = player['id']

            # Read body
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > self.MAX_FILE_SIZE:
                self._send_error(413, "File too large. Maximum size is 2MB")
                return

            body = self.rfile.read(content_length)
            content_type = self.headers.get('Content-Type', '')

            # Parse the request based on content type
            try:
                if 'multipart/form-data' in content_type:
                    image_data, file_type = parse_multipart_form(body, content_type)
                elif 'application/json' in content_type:
                    image_data, file_type = parse_json_base64(body.decode('utf-8'))
                else:
                    # Assume raw image data
                    image_data = body
                    file_type = content_type if content_type in self.ALLOWED_TYPES else 'image/jpeg'
            except ValueError as e:
                self._send_error(400, str(e))
                return

            # Validate file type
            if file_type not in self.ALLOWED_TYPES:
                self._send_error(400, f"Invalid file type. Allowed: JPEG, PNG, WebP")
                return

            # Validate file size
            if len(image_data) > self.MAX_FILE_SIZE:
                self._send_error(413, "File too large. Maximum size is 2MB")
                return

            # Image processing is now done on frontend (Canvas API)
            # Upload as-is
            processed_image = image_data

            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            filename = f"avatar_{player_id}_{timestamp}_{unique_id}.jpg"

            # Upload to Supabase Storage via REST API
            try:
                # Delete old avatar if exists
                old_avatar_url = player.get('avatar_url')
                if old_avatar_url:
                    try:
                        # Extract filename from URL
                        old_filename = old_avatar_url.split('/')[-1]
                        delete_from_storage(old_filename)
                    except Exception:
                        pass  # Ignore errors deleting old file

                # Upload new avatar
                upload_to_storage(filename, processed_image, 'image/jpeg')

                # Get public URL
                public_url = get_public_url(filename)

                # Update player record
                table('players').update({
                    'avatar_url': public_url
                }).eq('id', player_id).execute()

                self._send_success({
                    "message": "Photo uploaded successfully",
                    "avatar_url": public_url
                })

            except Exception as e:
                self._send_error(500, f"Storage upload failed: {str(e)}")
                return

        except Exception as e:
            self._send_error(500, str(e))

    def do_DELETE(self):
        """Remove avatar photo"""
        try:
            from api.supabase_http import table

            # Get email from Authorization header
            auth_header = self.headers.get('Authorization', '')
            email = None

            if auth_header.startswith('Bearer '):
                token_or_email = auth_header.replace('Bearer ', '')
                if '@' in token_or_email:
                    email = token_or_email.lower()
                else:
                    self._send_error(401, "Please provide your email in Authorization header")
                    return

            if not email:
                email = self.headers.get('X-Player-Email', '').lower()

            if not email:
                self._send_error(401, "Authentication required")
                return

            # Get player record
            player = get_player_by_email(email)
            if not player:
                self._send_error(404, "Player profile not found")
                return

            player_id = player['id']
            avatar_url = player.get('avatar_url')

            if avatar_url:
                try:
                    # Extract filename from URL
                    filename = avatar_url.split('/')[-1]
                    delete_from_storage(filename)
                except Exception:
                    pass  # Ignore errors deleting file

            # Clear avatar_url in database
            table('players').update({
                'avatar_url': None
            }).eq('id', player_id).execute()

            self._send_success({
                "message": "Photo removed successfully"
            })

        except Exception as e:
            self._send_error(500, str(e))

    def _send_success(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"success": True, **data}).encode())

    def _send_error(self, status, message):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"success": False, "error": message}).encode())
