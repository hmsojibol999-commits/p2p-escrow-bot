from aiogram.fsm.state import State, StatesGroup


class DepositStates(StatesGroup):
    """FSM states for user deposit claims."""
    waiting_for_amount = State()
    waiting_for_trx_id = State()
    waiting_for_sender_number = State()


class WithdrawStates(StatesGroup):
    """FSM states for balance withdrawals."""
    waiting_for_method = State()
    waiting_for_amount = State()
    waiting_for_account = State()
    waiting_for_pin = State()


class TransferStates(StatesGroup):
    """FSM states for P2P wallet transfers."""
    waiting_for_recipient = State()
    waiting_for_amount = State()
    waiting_for_pin = State()


class ProductCreationStates(StatesGroup):
    """FSM states for seller creating a new product."""
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_category = State()
    waiting_for_price = State()
    waiting_for_delivery_mode = State()
    waiting_for_payload_files = State()


class DisputeStates(StatesGroup):
    """FSM states for opening or responding to an order dispute."""
    waiting_for_reason = State()
    waiting_for_evidence = State()


class SupportTicketStates(StatesGroup):
    """FSM states for support ticketing system."""
    waiting_for_subject = State()
    waiting_for_message = State()
    waiting_for_reply = State()


class PinSetupStates(StatesGroup):
    """FSM states for security PIN configuration."""
    waiting_for_new_pin = State()
    waiting_for_confirm_pin = State()
  
