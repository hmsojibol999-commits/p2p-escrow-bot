"""
Database Models Central Registry.
Imports all SQLAlchemy models to expose them under a single namespace 
and ensure proper metadata collection for migrations and schema creation.
"""

from database.models.user import User
from database.models.wallet import Wallet, WalletStatus
from database.models.product import Product, ProductType, ProductStatus, DeliveryMode
from database.models.category import Category
from database.models.order import Order, OrderStatus
from database.models.order_item import OrderItem
from database.models.escrow import Escrow, EscrowStatus
from database.models.product_file import ProductFile
from database.models.delivery import Delivery
from database.models.dispute import Dispute, DisputeStatus
from database.models.review import Review
from database.models.user_pin import UserPin
from database.models.transaction import Transaction, TransactionType, TransactionStatus
from database.models.deposit import Deposit, DepositStatus
from database.models.withdraw import Withdraw, WithdrawStatus
from database.models.transfer import Transfer, TransferStatus
from database.models.referral import Referral, ReferralStatus
from database.models.support_ticket import SupportTicket, TicketStatus, TicketPriority

__all__ = [
    # Core User & Security
    "User",
    "UserPin",
    # Financial Core
    "Wallet",
    "WalletStatus",
    "Transaction",
    "TransactionType",
    "TransactionStatus",
    "Deposit",
    "DepositStatus",
    "Withdraw",
    "WithdrawStatus",
    "Transfer",
    "TransferStatus",
    # Marketplace Core
    "Product",
    "ProductType",
    "ProductStatus",
    "DeliveryMode",
    "Category",
    "ProductFile",
    # Orders & Escrow
    "Order",
    "OrderStatus",
    "OrderItem",
    "Escrow",
    "EscrowStatus",
    "Delivery",
    # Dispute & Review
    "Dispute",
    "DisputeStatus",
    "Review",
    # Growth & Support
    "Referral",
    "ReferralStatus",
    "SupportTicket",
    "TicketStatus",
    "TicketPriority",
]
