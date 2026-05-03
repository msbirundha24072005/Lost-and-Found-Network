import qrcode
import io
import base64

def generate_qr_code(data):
    """Generate QR code and return as base64 string - SIMPLE VERSION"""
    # Generate QR code directly
    qr = qrcode.make(data)
    
    # Convert to bytes
    img_bytes = io.BytesIO()
    qr.save(img_bytes)  # No format parameter needed
    img_bytes.seek(0)
    
    # Convert to base64
    img_base64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
    
    return img_base64