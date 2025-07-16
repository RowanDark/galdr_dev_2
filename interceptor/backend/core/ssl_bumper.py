# galdr/interceptor/backend/core/ssl_bumper.py
import asyncio
import ssl
import socket
import logging
from typing import Optional, Tuple, Dict
from datetime import datetime
import struct

from .cert_manager import CertificateManager


class SSLBumper:
    """Handles SSL bumping for HTTPS traffic interception"""
    
    def __init__(self, cert_manager: CertificateManager):
        self.cert_manager = cert_manager
        self.logger = logging.getLogger(__name__)
        self.active_connections: Dict[str, dict] = {}
        
    async def handle_connect_tunnel(self, 
                                   client_reader: asyncio.StreamReader,
                                   client_writer: asyncio.StreamWriter,
                                   target_host: str,
                                   target_port: int) -> bool:
        """Handle CONNECT tunnel for HTTPS traffic"""
        try:
            # Send 200 Connection Established to client
            response = b"HTTP/1.1 200 Connection Established\r\n\r\n"
            client_writer.write(response)
            await client_writer.drain()
            
            # Create SSL context for the fake server certificate
            server_ssl_context = self._create_server_ssl_context(target_host)
            
            # Start SSL handshake with client
            ssl_reader, ssl_writer = await asyncio.start_server(
                lambda r, w: self._handle_ssl_client(r, w, target_host, target_port),
                sock=client_writer.get_extra_info('socket'),
                ssl=server_ssl_context
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"SSL bumping error for {target_host}:{target_port}: {e}")
            return False
    
    def _create_server_ssl_context(self, hostname: str) -> ssl.SSLContext:
        """Create SSL context for server certificate"""
        try:
            # Generate or retrieve certificate for hostname
            cert_file, key_file = self.cert_manager.generate_server_cert(hostname)
            
            # Create SSL context
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(cert_file, key_file)
            
            # Configure for interception
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error creating SSL context for {hostname}: {e}")
            raise
    
    async def _handle_ssl_client(self,
                                reader: asyncio.StreamReader,
                                writer: asyncio.StreamWriter,
                                target_host: str,
                                target_port: int):
        """Handle SSL client connection after successful handshake"""
        connection_id = f"{target_host}:{target_port}:{id(writer)}"
        
        try:
            # Establish connection to real server
            target_reader, target_writer = await asyncio.open_connection(
                target_host, target_port, ssl=True
            )
            
            # Store connection info
            self.active_connections[connection_id] = {
                'client_reader': reader,
                'client_writer': writer,
                'target_reader': target_reader,
                'target_writer': target_writer,
                'start_time': datetime.now()
            }
            
            # Start bidirectional relay with interception
            await asyncio.gather(
                self._relay_client_to_server(reader, target_writer, connection_id),
                self._relay_server_to_client(target_reader, writer, connection_id),
                return_exceptions=True
            )
            
        except Exception as e:
            self.logger.error(f"SSL relay error for {connection_id}: {e}")
        finally:
            # Clean up connection
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]
            
            # Close connections
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass
    
    async def _relay_client_to_server(self,
                                     client_reader: asyncio.StreamReader,
                                     target_writer: asyncio.StreamWriter,
                                     connection_id: str):
        """Relay traffic from client to server with interception"""
        try:
            while True:
                data = await client_reader.read(8192)
                if not data:
                    break
                
                # Intercept and potentially modify data
                intercepted_data = await self._intercept_client_data(data, connection_id)
                
                # Forward to target server
                target_writer.write(intercepted_data)
                await target_writer.drain()
                
        except Exception as e:
            self.logger.error(f"Client->Server relay error for {connection_id}: {e}")
        finally:
            try:
                target_writer.close()
                await target_writer.wait_closed()
            except:
                pass
    
    async def _relay_server_to_client(self,
                                     target_reader: asyncio.StreamReader,
                                     client_writer: asyncio.StreamWriter,
                                     connection_id: str):
        """Relay traffic from server to client with interception"""
        try:
            while True:
                data = await target_reader.read(8192)
                if not data:
                    break
                
                # Intercept and potentially modify data
                intercepted_data = await self._intercept_server_data(data, connection_id)
                
                # Forward to client
                client_writer.write(intercepted_data)
                await client_writer.drain()
                
        except Exception as e:
            self.logger.error(f"Server->Client relay error for {connection_id}: {e}")
        finally:
            try:
                client_writer.close()
                await client_writer.wait_closed()
            except:
                pass
    
    async def _intercept_client_data(self, data: bytes, connection_id: str) -> bytes:
        """Intercept and process client data"""
        try:
            # Try to parse as HTTP request
            if data.startswith(b'GET ') or data.startswith(b'POST ') or \
               data.startswith(b'PUT ') or data.startswith(b'DELETE '):
                
                # Parse HTTP request
                request_str = data.decode('utf-8', errors='ignore')
                self.logger.debug(f"Intercepted HTTPS request: {request_str[:200]}...")
                
                # TODO: Create InterceptedRequest object and store
                # TODO: Apply request modification plugins
                
            return data
            
        except Exception as e:
            self.logger.error(f"Error intercepting client data: {e}")
            return data
    
    async def _intercept_server_data(self, data: bytes, connection_id: str) -> bytes:
        """Intercept and process server data"""
        try:
            # Try to parse as HTTP response
            if data.startswith(b'HTTP/'):
                response_str = data.decode('utf-8', errors='ignore')
                self.logger.debug(f"Intercepted HTTPS response: {response_str[:200]}...")
                
                # TODO: Create InterceptedResponse object and store
                # TODO: Apply response modification plugins
                
            return data
            
        except Exception as e:
            self.logger.error(f"Error intercepting server data: {e}")
            return data
    
    def get_active_connections(self) -> Dict[str, dict]:
        """Get information about active SSL connections"""
        return {
            conn_id: {
                'start_time': conn['start_time'].isoformat(),
                'duration': (datetime.now() - conn['start_time']).total_seconds()
            }
            for conn_id, conn in self.active_connections.items()
        }
