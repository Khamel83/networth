/**
 * Avatar Image Processing and Upload
 *
 * Processes avatar images using Canvas API before uploading.
 * This eliminates the need for server-side Pillow (PIL) processing.
 *
 * Features:
 * - Validates file type (JPEG, PNG, WebP)
 * - Validates file size (max 2MB)
 * - Center-crops to square
 * - Resizes to 200x200
 * - Converts to JPEG at 85% quality
 * - Uploads to server
 */

/**
 * Process and upload avatar image using Canvas API
 * @param {File} file - The image file from file input
 * @param {string} sessionToken - Session token for authentication
 * @returns {Promise<string>} - Returns the avatar URL
 */
export async function processAndUploadAvatar(file, sessionToken) {
    // Validate file type
    if (!file.type.match(/image\/(jpeg|jpg|png|webp)/)) {
        throw new Error('Please upload a JPEG, PNG, or WebP image');
    }

    // Validate file size (max 2MB)
    if (file.size > 2 * 1024 * 1024) {
        throw new Error('Image must be under 2MB');
    }

    // Load image
    const img = await loadImage(file);

    // Calculate crop dimensions (center crop to square)
    const size = Math.min(img.width, img.height);
    const startX = (img.width - size) / 2;
    const startY = (img.height - size) / 2;

    // Create canvas and resize to 200x200
    const canvas = document.createElement('canvas');
    canvas.width = 200;
    canvas.height = 200;
    const ctx = canvas.getContext('2d');

    // Fill white background (for transparent images)
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, 200, 200);

    // Draw cropped and resized image
    ctx.drawImage(
        img,
        startX, startY, size, size,  // Source crop
        0, 0, 200, 200              // Destination
    );

    // Convert to blob (JPEG at 85% quality)
    const blob = await new Promise(resolve => {
        canvas.toBlob(resolve, 'image/jpeg', 0.85);
    });

    // Upload to server
    const formData = new FormData();
    formData.append('file', blob, `avatar_${Date.now()}.jpg`);

    const response = await fetch('/api/upload', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${sessionToken}`
        },
        body: formData
    });

    const data = await response.json();
    if (!data.success) {
        throw new Error(data.error || 'Upload failed');
    }

    return data.avatar_url;
}

/**
 * Load an image from a File object
 * @param {File} file - The image file
 * @returns {Promise<HTMLImageElement>} - Returns the loaded image element
 */
function loadImage(file) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = () => reject(new Error('Failed to load image'));
        img.src = URL.createObjectURL(file);
    });
}

/**
 * Get a preview URL for an avatar image before upload
 * @param {File} file - The image file
 * @returns {Promise<string>} - Returns a blob URL for preview
 */
export async function getAvatarPreview(file) {
    const img = await loadImage(file);

    // Calculate crop dimensions (center crop to square)
    const size = Math.min(img.width, img.height);
    const startX = (img.width - size) / 2;
    const startY = (img.height - size) / 2;

    // Create canvas and resize to 200x200
    const canvas = document.createElement('canvas');
    canvas.width = 200;
    canvas.height = 200;
    const ctx = canvas.getContext('2d');

    // Fill white background
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, 200, 200);

    // Draw cropped and resized image
    ctx.drawImage(
        img,
        startX, startY, size, size,
        0, 0, 200, 200
    );

    // Return blob URL for preview
    return new Promise(resolve => {
        canvas.toBlob(blob => {
            resolve(URL.createObjectURL(blob));
        }, 'image/jpeg', 0.85);
    });
}
