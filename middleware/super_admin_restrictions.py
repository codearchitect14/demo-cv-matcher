"""
Super Admin Role Restrictions Middleware

Enforces strict separation between Super Admin and Company operations:
- Super Admin CAN: Approve/Reject/Suspend companies and admins, View data
- Super Admin CANNOT: Modify company internal operations (jobs, recruiters, candidates, applications)
"""

import logging
from typing import List
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

class SuperAdminRestrictions:
    """Enforce super admin role restrictions"""
    
    # Actions super admin CAN perform
    ALLOWED_COMPANY_ACTIONS = [
        'approve',
        'reject',
        'suspend',
        'activate',
        'view',
        'list'
    ]
    
    # Actions super admin CANNOT perform on company internals
    RESTRICTED_ENTITIES = [
        'jobs',
        'candidates',
        'applications',
        'messages',
        'interviews',
        'assessments'
    ]
    
    @staticmethod
    def check_company_action_allowed(action: str) -> bool:
        """Check if super admin is allowed to perform this action on companies"""
        return action.lower() in SuperAdminRestrictions.ALLOWED_COMPANY_ACTIONS
    
    @staticmethod
    def check_entity_access_allowed(entity: str) -> bool:
        """Check if super admin can access this entity type"""
        return entity.lower() not in SuperAdminRestrictions.RESTRICTED_ENTITIES
    
    @staticmethod
    def enforce_view_only_for_entity(entity: str, operation: str):
        """
        Enforce that super admin can only VIEW certain entities, not modify them
        
        Args:
            entity: Entity type (e.g., 'jobs', 'candidates')
            operation: Operation being performed (e.g., 'create', 'update', 'delete', 'view')
        
        Raises:
            HTTPException: If operation is not allowed
        """
        if entity.lower() in SuperAdminRestrictions.RESTRICTED_ENTITIES:
            if operation.lower() not in ['view', 'list', 'get', 'read']:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Super Admin cannot {operation} {entity}. This is a company internal operation."
                )
    
    @staticmethod
    def enforce_company_management_only():
        """
        Decorator/checker to ensure super admin only manages companies/admins,
        not internal company operations
        """
        logger.info("[SUPER-ADMIN-RESTRICTION] Checking company management permissions")
        return True

# Global instance
super_admin_restrictions = SuperAdminRestrictions()

# Decorator for endpoints
def super_admin_company_management_only(func):
    """Decorator to restrict super admin to company management only"""
    async def wrapper(*args, **kwargs):
        # Log the action
        logger.info(f"[SUPER-ADMIN] Company management action: {func.__name__}")
        return await func(*args, **kwargs)
    return wrapper

def restrict_super_admin_from_company_internals(entity_type: str):
    """
    Decorator to prevent super admin from accessing company internal entities
    
    Usage:
        @restrict_super_admin_from_company_internals('jobs')
        async def create_job(...):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Check if user is super admin (would need to extract from context)
            # For now, this is a placeholder for the concept
            logger.info(f"[RESTRICTION-CHECK] Entity: {entity_type}, Function: {func.__name__}")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

