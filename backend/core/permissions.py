"""RBAC permission system.

Permissions follow the format: module.resource.action
Example: sales.order.create, contacts.contact.view
"""

from enum import Enum
from functools import wraps
from typing import List

from fastapi import Depends, HTTPException, status


class Permission(str, Enum):
    """All permissions in the system, organized by module."""

    # Auth
    AUTH_USERS_VIEW = "auth.users.view"
    AUTH_USERS_CREATE = "auth.users.create"
    AUTH_USERS_EDIT = "auth.users.edit"
    AUTH_USERS_DELETE = "auth.users.delete"
    AUTH_ROLES_MANAGE = "auth.roles.manage"

    # Contacts
    CONTACTS_VIEW = "contacts.contact.view"
    CONTACTS_CREATE = "contacts.contact.create"
    CONTACTS_EDIT = "contacts.contact.edit"
    CONTACTS_DELETE = "contacts.contact.delete"

    # CRM
    CRM_LEADS_VIEW = "crm.leads.view"
    CRM_LEADS_CREATE = "crm.leads.create"
    CRM_LEADS_EDIT = "crm.leads.edit"
    CRM_LEADS_DELETE = "crm.leads.delete"
    CRM_PIPELINE_MANAGE = "crm.pipeline.manage"

    # Sales
    SALES_ORDERS_VIEW = "sales.orders.view"
    SALES_ORDERS_CREATE = "sales.orders.create"
    SALES_ORDERS_EDIT = "sales.orders.edit"
    SALES_ORDERS_DELETE = "sales.orders.delete"
    SALES_ORDERS_CONFIRM = "sales.orders.confirm"

    # Products
    PRODUCTS_VIEW = "products.product.view"
    PRODUCTS_CREATE = "products.product.create"
    PRODUCTS_EDIT = "products.product.edit"
    PRODUCTS_DELETE = "products.product.delete"

    # Invoicing
    INVOICING_VIEW = "invoicing.invoice.view"
    INVOICING_CREATE = "invoicing.invoice.create"
    INVOICING_EDIT = "invoicing.invoice.edit"
    INVOICING_DELETE = "invoicing.invoice.delete"
    INVOICING_SEND = "invoicing.invoice.send"
    INVOICING_PAYMENTS = "invoicing.payments.manage"


# Default role templates
DEFAULT_ROLES = {
    "admin": list(Permission),  # All permissions
    "manager": [
        Permission.CONTACTS_VIEW,
        Permission.CONTACTS_CREATE,
        Permission.CONTACTS_EDIT,
        Permission.CRM_LEADS_VIEW,
        Permission.CRM_LEADS_CREATE,
        Permission.CRM_LEADS_EDIT,
        Permission.SALES_ORDERS_VIEW,
        Permission.SALES_ORDERS_CREATE,
        Permission.SALES_ORDERS_EDIT,
        Permission.SALES_ORDERS_CONFIRM,
        Permission.PRODUCTS_VIEW,
        Permission.PRODUCTS_CREATE,
        Permission.PRODUCTS_EDIT,
        Permission.INVOICING_VIEW,
        Permission.INVOICING_CREATE,
        Permission.INVOICING_EDIT,
        Permission.INVOICING_SEND,
        Permission.INVOICING_PAYMENTS,
    ],
    "user": [
        Permission.CONTACTS_VIEW,
        Permission.CRM_LEADS_VIEW,
        Permission.CRM_LEADS_CREATE,
        Permission.CRM_LEADS_EDIT,
        Permission.SALES_ORDERS_VIEW,
        Permission.SALES_ORDERS_CREATE,
        Permission.PRODUCTS_VIEW,
        Permission.INVOICING_VIEW,
    ],
}


def require_permission(*permissions: Permission):
    """FastAPI dependency that enforces permission checks.

    Usage:
        @router.get("/contacts")
        async def list_contacts(
            user = Depends(require_permission(Permission.CONTACTS_VIEW))
        ):
            ...
    """
    from backend.core.dependencies import get_current_user

    async def _check_permissions(current_user=Depends(get_current_user)):
        # Superusers bypass all permission checks
        if current_user.is_superuser:
            return current_user

        user_permissions = set()
        for role in current_user.roles:
            for perm in role.permissions:
                user_permissions.add(perm.permission)

        required = {p.value for p in permissions}
        if not required.issubset(user_permissions):
            missing = required - user_permissions
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permissions: {', '.join(missing)}",
            )
        return current_user

    return _check_permissions
