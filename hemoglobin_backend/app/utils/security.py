"""
Security utilities for PHI protection and data encryption.
"""
import uuid
import hashlib
from cryptography.fernet import Fernet
from pathlib import Path
from typing import Optional
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def generate_scan_id() -> str:
    """
    Generate a unique, anonymous scan ID.
    
    Returns:
        UUID4 string
    """
    return str(uuid.uuid4())


def hash_identifier(identifier: str) -> str:
    """
    Create a one-way hash of an identifier (e.g., user ID).
    
    Args:
        identifier: Original identifier
        
    Returns:
        SHA256 hash (hex string)
    """
    return hashlib.sha256(identifier.encode()).hexdigest()


class FileEncryption:
    """Handle file encryption/decryption for stored images."""
    
    def __init__(self):
        if settings.enable_encryption:
            # In production, load from secure key management service
            self.cipher = Fernet(settings.encryption_key.encode())
        else:
            self.cipher = None
    
    def encrypt_file(self, file_path: Path) -> Path:
        """
        Encrypt a file in place.
        
        Args:
            file_path: Path to file to encrypt
            
        Returns:
            Path to encrypted file (.enc extension)
        """
        if not self.cipher:
            return file_path
        
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            encrypted_data = self.cipher.encrypt(data)
            encrypted_path = file_path.with_suffix(file_path.suffix + '.enc')
            
            with open(encrypted_path, 'wb') as f:
                f.write(encrypted_data)
            
            # Remove original
            file_path.unlink()
            logger.info(f"Encrypted file: {file_path.name}")
            return encrypted_path
            
        except Exception as e:
            logger.error(f"Encryption failed for {file_path}: {e}")
            return file_path
    
    def decrypt_file(self, encrypted_path: Path) -> bytes:
        """
        Decrypt a file and return contents.
        
        Args:
            encrypted_path: Path to encrypted file
            
        Returns:
            Decrypted file contents
        """
        if not self.cipher:
            with open(encrypted_path, 'rb') as f:
                return f.read()
        
        try:
            with open(encrypted_path, 'rb') as f:
                encrypted_data = f.read()
            
            return self.cipher.decrypt(encrypted_data)
            
        except Exception as e:
            logger.error(f"Decryption failed for {encrypted_path}: {e}")
            raise


# Global encryption handler
file_encryption = FileEncryption()
