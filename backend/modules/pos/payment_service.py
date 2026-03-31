"""Payment integration services for M-Pesa and Paystack Kenya."""

import base64
import logging
import httpx
from datetime import datetime
from typing import Optional

from backend.settings import settings

logger = logging.getLogger("erp.payments")


class MpesaService:
    """M-Pesa Daraja API integration for STK Push payments."""

    SANDBOX_URL = "https://sandbox.safaricom.co.ke"
    PRODUCTION_URL = "https://api.safaricom.co.ke"

    def __init__(self):
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.shortcode = settings.MPESA_SHORTCODE
        self.passkey = settings.MPESA_PASSKEY
        self.callback_url = settings.MPESA_CALLBACK_URL
        self.base_url = self.SANDBOX_URL if not settings.is_production else self.PRODUCTION_URL

    async def _get_access_token(self) -> str:
        """Authenticate with Daraja API and return an access token."""
        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        credentials = base64.b64encode(
            f"{self.consumer_key}:{self.consumer_secret}".encode()
        ).decode()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Basic {credentials}"}
            )
            response.raise_for_status()
            return response.json()["access_token"]

    def _generate_password(self) -> tuple[str, str]:
        """Generate the STK Push password and timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        raw = f"{self.shortcode}{self.passkey}{timestamp}"
        password = base64.b64encode(raw.encode()).decode()
        return password, timestamp

    async def initiate_stk_push(
        self,
        phone_number: str,
        amount: float,
        order_reference: str,
        description: str = "Payment"
    ) -> dict:
        """
        Initiate an M-Pesa STK Push to the customer's phone.
        
        Args:
            phone_number: Customer phone in format 254XXXXXXXXX
            amount: Amount in KES (whole number)
            order_reference: Unique order reference
            description: Transaction description
        
        Returns:
            Daraja API response with CheckoutRequestID
        """
        token = await self._get_access_token()
        password, timestamp = self._generate_password()

        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": round(amount),
            "PartyA": phone_number,
            "PartyB": self.shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": self.callback_url,
            "AccountReference": order_reference,
            "TransactionDesc": description
        }

        url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            )
            result = response.json()
            logger.info(f"M-Pesa STK Push response: {result}")
            return result

    async def query_stk_status(self, checkout_request_id: str) -> dict:
        """Query the status of an STK Push request."""
        token = await self._get_access_token()
        password, timestamp = self._generate_password()

        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id
        }

        url = f"{self.base_url}/mpesa/stkpushquery/v1/query"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            )
            return response.json()

    @staticmethod
    def parse_callback(data: dict) -> dict:
        """Parse M-Pesa callback data into a clean dict."""
        body = data.get("Body", {}).get("stkCallback", {})
        result = {
            "merchant_request_id": body.get("MerchantRequestID"),
            "checkout_request_id": body.get("CheckoutRequestID"),
            "result_code": body.get("ResultCode"),
            "result_desc": body.get("ResultDesc"),
        }

        # Extract metadata if payment was successful
        if body.get("ResultCode") == 0:
            metadata = body.get("CallbackMetadata", {}).get("Item", [])
            for item in metadata:
                name = item.get("Name", "")
                value = item.get("Value")
                if name == "Amount":
                    result["amount"] = value
                elif name == "MpesaReceiptNumber":
                    result["mpesa_receipt"] = value
                elif name == "TransactionDate":
                    result["transaction_date"] = value
                elif name == "PhoneNumber":
                    result["phone_number"] = value

        return result


class PaystackService:
    """Paystack payment integration for card payments in Kenya."""

    BASE_URL = "https://api.paystack.co"

    def __init__(self):
        self.secret_key = settings.PAYSTACK_SECRET_KEY
        self.public_key = settings.PAYSTACK_PUBLIC_KEY

    async def initialize_transaction(
        self,
        email: str,
        amount: float,
        reference: str,
        callback_url: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> dict:
        """
        Initialize a Paystack transaction.
        
        Args:
            email: Customer email address
            amount: Amount in KES (will be converted to kobo — smallest unit)
            reference: Unique transaction reference
            callback_url: URL to redirect after payment
            metadata: Additional metadata
        
        Returns:
            Paystack response with authorization_url
        """
        # Paystack amounts are in the smallest currency unit (cents for KES)
        amount_in_cents = int(amount * 100)

        payload = {
            "email": email,
            "amount": amount_in_cents,
            "reference": reference,
            "currency": "KES",
            "callback_url": callback_url,
            "metadata": metadata or {}
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/transaction/initialize",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.secret_key}",
                    "Content-Type": "application/json"
                }
            )
            result = response.json()
            logger.info(f"Paystack initialize response: {result}")
            return result

    async def verify_transaction(self, reference: str) -> dict:
        """
        Verify a Paystack transaction by reference.
        
        Returns:
            Paystack verification response with status
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/transaction/verify/{reference}",
                headers={
                    "Authorization": f"Bearer {self.secret_key}",
                    "Content-Type": "application/json"
                }
            )
            result = response.json()
            logger.info(f"Paystack verify response: {result}")
            return result


# Singleton instances
mpesa_service = MpesaService()
paystack_service = PaystackService()
