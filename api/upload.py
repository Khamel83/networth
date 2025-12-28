"""
Vercel Serverless Function: Photo Upload API

Handles avatar photo uploads:
- Accepts image files (JPEG, PNG, WebP)
- Validates file size (max 2MB)
- Resizes to 200x200 thumbnail
- Uploads to Supabase Storage 'avatar' bucket
- Updates player.avatar_url

Updated for Ashley's Christmas 2025 feedback.
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import io
import base64
import uuid
from datetime import datetime


def get_supabase_client():
    """Lazy initialization of Supabase client"""
    try:
        from supabase import create_client
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_ANON_KEY')
        if url and key:
            return create_client(url, key)
    except Exception:
        pass
    return None


def get_user_from_token(supabase, auth_header):
    """Extract and verify user from Authorization header"""
    if not auth_header or not auth_header.startswith('Bearer '):
        return None

    token = auth_header.replace('Bearer ', '')
    try:
        user = supabase.auth.get_user(token)
        if user and user.user:
            return user.user
    except Exception:
        pass
    return None


def process_image(image_data, content_type):
    """Resize image to 200x200 thumbnail and return as bytes"""
    try:
        from PIL import Image

        # Open image from bytes
        img = Image.open(io.BytesIO(image_data))

        # Convert to RGB if necessary (handles PNG transparency, etc.)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Create white background for transparent images
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # Resize to 200x200 with aspect ratio preservation and crop
        # First, determine the scaling factor
        width, height = img.size
        target_size = 200

        # Scale to fit the smaller dimension to 200
        if width < height:
            new_width = target_size
            new_height = int(height * (target_size / width))
        else:
            new_height = target_size
            new_width = int(width * (target_size / height))

        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Center crop to 200x200
        left = (new_width - target_size) // 2
        top = (new_height - target_size) // 2
        right = left + target_size
        bottom = top + target_size
        img = img.crop((left, top, right, bottom))

        # Save to bytes
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=85)
        output.seek(0)

        return output.getvalue()

    except Exception as e:
        raise ValueError(f"Image processing failed: {str(e)}")


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
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_POST(self):
        """Handle photo upload"""
        try:
            supabase = get_supabase_client()
            if not supabase:
                self._send_error(503, "Database not available")
                return

            auth_header = self.headers.get('Authorization')
            user = get_user_from_token(supabase, auth_header)

            if not user:
                self._send_error(401, "Authentication required")
                return

            # Get player record
            player = supabase.table('players').select('*').eq('email', user.email).single().execute()
            if not player.data:
                self._send_error(404, "Player profile not found")
                return

            player_id = player.data['id']

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

            # Process image (resize to 200x200)
            try:
                processed_image = process_image(image_data, file_type)
            except ValueError as e:
                self._send_error(400, str(e))
                return

            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            filename = f"avatar_{player_id}_{timestamp}_{unique_id}.jpg"

            # Upload to Supabase Storage
            try:
                # Delete old avatar if exists
                old_avatar_url = player.data.get('avatar_url')
                if old_avatar_url:
                    try:
                        # Extract filename from URL
                        old_filename = old_avatar_url.split('/')[-1]
                        supabase.storage.from_('avatar').remove([old_filename])
                    except Exception:
                        pass  # Ignore errors deleting old file

                # Upload new avatar
                result = supabase.storage.from_('avatar').upload(
                    filename,
                    processed_image,
                    file_options={"content-type": "image/jpeg"}
                )

                # Get public URL
                public_url = supabase.storage.from_('avatar').get_public_url(filename)

                # Update player record
                supabase.table('players').update({
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
            supabase = get_supabase_client()
            if not supabase:
                self._send_error(503, "Database not available")
                return

            auth_header = self.headers.get('Authorization')
            user = get_user_from_token(supabase, auth_header)

            if not user:
                self._send_error(401, "Authentication required")
                return

            # Get player record
            player = supabase.table('players').select('*').eq('email', user.email).single().execute()
            if not player.data:
                self._send_error(404, "Player profile not found")
                return

            player_id = player.data['id']
            avatar_url = player.data.get('avatar_url')

            if avatar_url:
                try:
                    # Extract filename from URL
                    filename = avatar_url.split('/')[-1]
                    supabase.storage.from_('avatar').remove([filename])
                except Exception:
                    pass  # Ignore errors deleting file

            # Clear avatar_url in database
            supabase.table('players').update({
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
