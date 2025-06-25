"""
MFI Service Manager for handling external service configurations and routing.
"""

import httpx
import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from cryptography.fernet import Fernet

from app.models.mfi_config import (
    MFIInstitution, ExternalServiceConfig, ServiceEndpoint,
    ServiceCallLog, ServiceType, ServiceStatus
)
from app.models.user import User
from app.config import settings

logger = logging.getLogger(__name__)

class MFIServiceManager:
    """Manages external service configurations and calls per MFI."""
    
    def __init__(self):
        """Initialize the service manager."""
        self.encryption_key = settings.SERVICE_ENCRYPTION_KEY.encode() if hasattr(settings, 'SERVICE_ENCRYPTION_KEY') else Fernet.generate_key()
        self.fernet = Fernet(self.encryption_key)
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_service_config(
        self,
        institution_code: str,
        service_type: ServiceType,
        session: AsyncSession
    ) -> Optional[ExternalServiceConfig]:
        """Get active service configuration for an institution and service type."""
        try:
            stmt = (
                select(ExternalServiceConfig)
                .join(MFIInstitution)
                .where(
                    MFIInstitution.code == institution_code,
                    ExternalServiceConfig.service_type == service_type.value,
                    ExternalServiceConfig.status == ServiceStatus.ACTIVE,
                    ExternalServiceConfig.is_primary == True
                )
            )
            result = await session.execute(stmt)
            return result.scalar()
        except Exception as e:
            logger.error(f"Failed to get service config: {str(e)}")
            return None
    
    async def call_external_service(
        self,
        institution_code: str,
        service_type: ServiceType,
        endpoint_name: str,
        payload: Dict[str, Any],
        user_id: Optional[str] = None,
        application_id: Optional[str] = None,
        session: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Make a call to an external service."""
        
        # Get service configuration
        service_config = await self.get_service_config(institution_code, service_type, session)
        if not service_config:
            raise ValueError(f"No active {service_type.value} service configured for {institution_code}")
        
        # Get endpoint configuration
        endpoint = await self._get_endpoint(service_config.id, endpoint_name, session)
        if not endpoint:
            raise ValueError(f"Endpoint {endpoint_name} not found for service {service_config.service_name}")
        
        # Prepare request
        request_url = f"{service_config.api_url.rstrip('/')}{endpoint.endpoint_path}"
        headers = self._prepare_headers(service_config)
        request_payload = self._prepare_payload(payload, endpoint.request_template)
        
        # Create call log
        call_log = ServiceCallLog(
            service_config_id=service_config.id,
            endpoint_id=endpoint.id,
            user_id=user_id,
            application_id=application_id,
            request_method=endpoint.http_method,
            request_url=request_url,
            request_headers=headers,
            request_payload=request_payload,
            business_context={
                "service_type": service_type.value,
                "endpoint_name": endpoint_name,
                "institution_code": institution_code
            }
        )
        
        if session:
            session.add(call_log)
            await session.flush()
        
        try:
            # Make the API call
            start_time = datetime.utcnow()
            
            if endpoint.http_method.upper() == "GET":
                response = await self.client.get(
                    request_url,
                    headers=headers,
                    params=request_payload,
                    timeout=service_config.timeout_seconds
                )
            else:
                response = await self.client.request(
                    endpoint.http_method.upper(),
                    request_url,
                    headers=headers,
                    json=request_payload,
                    timeout=service_config.timeout_seconds
                )
            
            end_time = datetime.utcnow()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Update call log with response
            call_log.response_status_code = response.status_code
            call_log.response_headers = dict(response.headers)
            call_log.response_time_ms = response_time_ms
            call_log.completed_at = end_time
            
            if response.status_code == 200:
                response_data = response.json()
                call_log.response_payload = response_data
                call_log.success = True
                
                # Update service statistics
                await self._update_service_stats(service_config.id, True, response_time_ms, session)
                
                # Map response according to endpoint configuration
                mapped_response = self._map_response(response_data, endpoint.response_mapping)
                return mapped_response
            
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                call_log.error_message = error_msg
                call_log.success = False
                
                # Update service statistics
                await self._update_service_stats(service_config.id, False, response_time_ms, session)
                
                raise Exception(error_msg)
        
        except httpx.TimeoutException:
            call_log.error_message = "Request timeout"
            call_log.success = False
            call_log.completed_at = datetime.utcnow()
            
            await self._update_service_stats(service_config.id, False, 0, session)
            raise Exception("Service request timed out")
        
        except httpx.RequestError as e:
            call_log.error_message = str(e)
            call_log.success = False
            call_log.completed_at = datetime.utcnow()
            
            await self._update_service_stats(service_config.id, False, 0, session)
            raise Exception(f"Service request failed: {str(e)}")
        
        except Exception as e:
            call_log.error_message = str(e)
            call_log.success = False
            call_log.completed_at = datetime.utcnow()
            
            if session:
                await session.commit()
            
            raise
    
    async def health_check_service(
        self,
        service_config: ExternalServiceConfig,
        session: AsyncSession
    ) -> bool:
        """Perform health check on a service."""
        try:
            health_url = f"{service_config.api_url.rstrip('/')}/health"
            headers = self._prepare_headers(service_config)
            
            response = await self.client.get(
                health_url,
                headers=headers,
                timeout=5.0  # Quick health check
            )
            
            is_healthy = response.status_code == 200
            
            # Update service health status
            service_config.last_health_check = datetime.utcnow()
            if is_healthy:
                service_config.last_successful_call = datetime.utcnow()
                if service_config.status == ServiceStatus.ERROR:
                    service_config.status = ServiceStatus.ACTIVE
            else:
                service_config.error_count += 1
                if service_config.error_count >= 5:
                    service_config.status = ServiceStatus.ERROR
            
            if session:
                await session.commit()
            
            return is_healthy
        
        except Exception as e:
            logger.warning(f"Health check failed for service {service_config.service_name}: {str(e)}")
            service_config.last_health_check = datetime.utcnow()
            service_config.error_count += 1
            service_config.last_error = str(e)
            
            if service_config.error_count >= 5:
                service_config.status = ServiceStatus.ERROR
            
            if session:
                await session.commit()
            
            return False
    
    async def get_service_metrics(
        self,
        institution_code: str,
        service_type: Optional[ServiceType] = None,
        days: int = 7,
        session: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Get service metrics for an institution."""
        try:
            # Build query for service call logs
            stmt = (
                select(ServiceCallLog)
                .join(ExternalServiceConfig)
                .join(MFIInstitution)
                .where(
                    MFIInstitution.code == institution_code,
                    ServiceCallLog.started_at >= datetime.utcnow() - timedelta(days=days)
                )
            )
            
            if service_type:
                stmt = stmt.where(ExternalServiceConfig.service_type == service_type.value)
            
            result = await session.execute(stmt)
            logs = result.scalars().all()
            
            # Calculate metrics
            total_calls = len(logs)
            successful_calls = sum(1 for log in logs if log.success)
            failed_calls = total_calls - successful_calls
            
            if total_calls > 0:
                success_rate = (successful_calls / total_calls) * 100
                avg_response_time = sum(log.response_time_ms or 0 for log in logs if log.response_time_ms) / total_calls
            else:
                success_rate = 0
                avg_response_time = 0
            
            # Service breakdown
            service_breakdown = {}
            for log in logs:
                service_name = log.service_config.service_name
                if service_name not in service_breakdown:
                    service_breakdown[service_name] = {
                        "total": 0,
                        "successful": 0,
                        "failed": 0,
                        "avg_response_time": 0
                    }
                
                service_breakdown[service_name]["total"] += 1
                if log.success:
                    service_breakdown[service_name]["successful"] += 1
                else:
                    service_breakdown[service_name]["failed"] += 1
            
            # Calculate success rates for each service
            for service_name, metrics in service_breakdown.items():
                if metrics["total"] > 0:
                    metrics["success_rate"] = (metrics["successful"] / metrics["total"]) * 100
                else:
                    metrics["success_rate"] = 0
            
            return {
                "institution_code": institution_code,
                "period_days": days,
                "total_calls": total_calls,
                "successful_calls": successful_calls,
                "failed_calls": failed_calls,
                "success_rate": success_rate,
                "avg_response_time_ms": avg_response_time,
                "service_breakdown": service_breakdown
            }
        
        except Exception as e:
            logger.error(f"Failed to get service metrics: {str(e)}")
            raise
    
    def encrypt_credential(self, credential: str) -> str:
        """Encrypt a credential for storage."""
        return self.fernet.encrypt(credential.encode()).decode()
    
    def decrypt_credential(self, encrypted_credential: str) -> str:
        """Decrypt a stored credential."""
        return self.fernet.decrypt(encrypted_credential.encode()).decode()
    
    def _prepare_headers(self, service_config: ExternalServiceConfig) -> Dict[str, str]:
        """Prepare headers for API request."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"MFI-Platform/{settings.VERSION}"
        }
        
        # Add authentication headers
        if service_config.api_key:
            decrypted_key = self.decrypt_credential(service_config.api_key)
            headers["Authorization"] = f"Bearer {decrypted_key}"
        
        # Add custom headers from configuration
        if service_config.headers:
            headers.update(service_config.headers)
        
        return headers
    
    def _prepare_payload(self, data: Dict[str, Any], template: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare request payload using template."""
        if not template:
            return data
        
        # Simple template substitution
        # In production, you might want more sophisticated templating
        payload = {}
        for key, value in template.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                # Template variable like ${customer_data.income}
                var_path = value[2:-1].split(".")
                payload_value = data
                for path_part in var_path:
                    if isinstance(payload_value, dict) and path_part in payload_value:
                        payload_value = payload_value[path_part]
                    else:
                        payload_value = None
                        break
                payload[key] = payload_value
            else:
                payload[key] = value
        
        return payload
    
    def _map_response(self, response: Dict[str, Any], mapping: Optional[Dict[str, str]]) -> Dict[str, Any]:
        """Map service response to standard format."""
        if not mapping:
            return response
        
        mapped = {}
        for target_field, source_path in mapping.items():
            source_value = response
            for path_part in source_path.split("."):
                if isinstance(source_value, dict) and path_part in source_value:
                    source_value = source_value[path_part]
                else:
                    source_value = None
                    break
            mapped[target_field] = source_value
        
        return mapped
    
    async def _get_endpoint(
        self,
        service_config_id: str,
        endpoint_name: str,
        session: AsyncSession
    ) -> Optional[ServiceEndpoint]:
        """Get endpoint configuration."""
        stmt = select(ServiceEndpoint).where(
            ServiceEndpoint.service_config_id == service_config_id,
            ServiceEndpoint.endpoint_name == endpoint_name
        )
        result = await session.execute(stmt)
        return result.scalar()
    
    async def _update_service_stats(
        self,
        service_config_id: str,
        success: bool,
        response_time_ms: int,
        session: AsyncSession
    ):
        """Update service statistics."""
        try:
            stmt = select(ExternalServiceConfig).where(ExternalServiceConfig.id == service_config_id)
            result = await session.execute(stmt)
            service_config = result.scalar()
            
            if service_config:
                service_config.total_calls += 1
                if success:
                    service_config.successful_calls += 1
                    service_config.last_successful_call = datetime.utcnow()
                    # Reset error count on success
                    service_config.error_count = 0
                else:
                    service_config.error_count += 1
                
                # Update average response time (simple moving average)
                if response_time_ms > 0:
                    service_config.avg_response_time_ms = (
                        (service_config.avg_response_time_ms + response_time_ms) // 2
                    )
                
                if session:
                    await session.commit()
        
        except Exception as e:
            logger.error(f"Failed to update service stats: {str(e)}")

# Global service manager instance
mfi_service_manager = MFIServiceManager()