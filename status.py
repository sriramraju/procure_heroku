import enum


class Pr_Status(enum.Enum):
    created = 1
    approval_requested = 2
    requested_change = 3  # Or rejected
    approved = 4
    rfq_generated = 5
    order_placed = 6
    fulfilled = 7


class Order_Status(enum.Enum):
    rfq_generated = 1
    order_placed = 2
    vendor_stage_1 = 3
    vendor_stage_2 = 4
    vendor_stage_3 = 5
    fulfilled = 6
