"""
Authentication module for Foodikal NY Backend
Uses hashlib PBKDF2 for password verification (Pyodide-compatible)
"""
import hashlib
import hmac
from typing import Optional


class AuthenticationError(Exception):
    """Custom exception for authentication failures"""
    def __init__(self, message: str = "Unauthorized"):
        self.message = message
        super().__init__(self.message)


def hash_password(password: str, salt: bytes = None, iterations: int = 100000) -> str:
    """
    Generate PBKDF2 hash for a password

    Args:
        password: Plain text password
        salt: Salt bytes (generated if None)
        iterations: Number of iterations (default 100000)

    Returns:
        Hash in format: salt$iterations$hash (hex encoded)
    """
    if salt is None:
        salt = hashlib.sha256(password.encode('utf-8')).digest()[:16]

    hash_obj = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        iterations
    )

    # Format: salt$iterations$hash
    return f"{salt.hex()}${iterations}${hash_obj.hex()}"


def verify_password(provided_password: str, stored_hash: str) -> bool:
    """
    Verify password against PBKDF2 hash using constant-time comparison

    Args:
        provided_password: Plain text password from user
        stored_hash: Hash string (format: salt$iterations$hash)

    Returns:
        True if password matches, False otherwise
    """
    try:
        # Parse stored hash
        parts = stored_hash.split('$')
        if len(parts) != 3:
            print("Invalid hash format")
            return False

        salt_hex, iterations_str, expected_hash = parts
        salt = bytes.fromhex(salt_hex)
        iterations = int(iterations_str)

        # Generate hash from provided password
        hash_obj = hashlib.pbkdf2_hmac(
            'sha256',
            provided_password.encode('utf-8'),
            salt,
            iterations
        )

        provided_hash = hash_obj.hex()

        # Constant-time comparison
        return hmac.compare_digest(provided_hash, expected_hash)

    except Exception as e:
        print(f"Password verification error: {str(e)}")
        return False


def extract_bearer_token(auth_header: Optional[str]) -> Optional[str]:
    """
    Extract password/token from Authorization header

    Args:
        auth_header: Authorization header value (e.g., "Bearer mypassword")

    Returns:
        Extracted password or None if invalid format
    """
    if not auth_header:
        return None

    if not auth_header.startswith("Bearer "):
        return None

    # Extract password after "Bearer "
    password = auth_header.replace("Bearer ", "", 1).strip()

    return password if password else None


def authenticate_request(auth_header: Optional[str], admin_password_hash: str) -> bool:
    """
    Authenticate a request by verifying the Authorization header

    Args:
        auth_header: Authorization header from request
        admin_password_hash: Stored password hash from env.ADMIN_PASSWORD_HASH

    Returns:
        True if authenticated, False otherwise
    """
    password = extract_bearer_token(auth_header)

    if not password:
        return False

    return verify_password(password, admin_password_hash)


# Example usage for generating admin password hash:
if __name__ == "__main__":
    # Run this script to generate a password hash for admin
    import sys

    if len(sys.argv) > 1:
        password = sys.argv[1]
        hashed = hash_password(password)
        print(f"\nPassword hash for '{password}':")
        print(hashed)
        print(f"\nTo set this as admin password, run:")
        print(f"wrangler secret put ADMIN_PASSWORD_HASH")
        print(f"Then paste the hash above when prompted.\n")
    else:
        print("Usage: python auth.py <password>")
        print("Example: python auth.py mySecurePassword123")
