# interceptor/core/cert_manager.py
import os
import ssl
import socket
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from typing import Optional, Tuple


class CertificateManager:
    """Manages SSL certificates for HTTPS interception"""
    
    def __init__(self, cert_dir: str = "./certs"):
        self.cert_dir = cert_dir
        self.ca_key_file = os.path.join(cert_dir, "ca-key.pem")
        self.ca_cert_file = os.path.join(cert_dir, "ca-cert.pem")
        
        # Ensure cert directory exists
        os.makedirs(cert_dir, exist_ok=True)
        
        # Initialize CA if not exists
        if not self._ca_exists():
            self._generate_ca()
    
    def _ca_exists(self) -> bool:
        """Check if CA certificate and key exist"""
        return os.path.exists(self.ca_key_file) and os.path.exists(self.ca_cert_file)
    
    def _generate_ca(self):
        """Generate Certificate Authority"""
        # Generate private key
        ca_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Generate CA certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Interceptor Proxy"),
            x509.NameAttribute(NameOID.COMMON_NAME, "Interceptor CA"),
        ])
        
        ca_cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            ca_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=3650)  # 10 years
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
            ]),
            critical=False,
        ).add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        ).add_extension(
            x509.KeyUsage(
                key_cert_sign=True,
                crl_sign=True,
                digital_signature=False,
                key_agreement=False,
                key_encipherment=False,
                data_encipherment=False,
                content_commitment=False,
                encipher_only=False,
                decipher_only=False
            ),
            critical=True,
        ).sign(ca_key, hashes.SHA256())
        
        # Save CA key
        with open(self.ca_key_file, "wb") as f:
            f.write(ca_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Save CA certificate
        with open(self.ca_cert_file, "wb") as f:
            f.write(ca_cert.public_bytes(serialization.Encoding.PEM))
    
    def generate_server_cert(self, hostname: str) -> Tuple[str, str]:
        """Generate server certificate for given hostname"""
        cert_file = os.path.join(self.cert_dir, f"{hostname}.crt")
        key_file = os.path.join(self.cert_dir, f"{hostname}.key")
        
        if os.path.exists(cert_file) and os.path.exists(key_file):
            return cert_file, key_file
        
        # Load CA
        with open(self.ca_key_file, "rb") as f:
            ca_key = serialization.load_pem_private_key(f.read(), password=None)
        
        with open(self.ca_cert_file, "rb") as f:
            ca_cert = x509.load_pem_x509_certificate(f.read())
        
        # Generate server key
        server_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Generate server certificate
        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Interceptor Proxy"),
            x509.NameAttribute(NameOID.COMMON_NAME, hostname),
        ])
        
        server_cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            ca_cert.subject
        ).public_key(
            server_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(hostname),
            ]),
            critical=False,
        ).sign(ca_key, hashes.SHA256())
        
        # Save server key
        with open(key_file, "wb") as f:
            f.write(server_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Save server certificate
        with open(cert_file, "wb") as f:
            f.write(server_cert.public_bytes(serialization.Encoding.PEM))
        
        return cert_file, key_file
    
    def get_ca_cert_path(self) -> str:
        """Get CA certificate path for installation"""
        return self.ca_cert_file
