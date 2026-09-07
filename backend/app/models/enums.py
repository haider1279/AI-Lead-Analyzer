from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    EMPLOYEE = "employee"

class LeadStatus(str, Enum):
    NEW = "NEW"
    CONTACTED = "CONTACTED"
    QUALIFIED = "QUALIFIED"
    PROPOSAL_SENT = "PROPOSAL_SENT"
    NEGOTIATION = "NEGOTIATION"
    WON = "WON"
    LOST = "LOST"

class LeadPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"

class LeadSource(str, Enum):
    UPWORK = "Upwork"
    LINKEDIN = "LinkedIn"
    WHATSAPP = "WhatsApp"
    EMAIL = "Email"
    WEBSITE = "Website"
    REFERRAL = "Referral"
    PHONE = "Phone"
    OTHER = "Other"

class TaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"

class ProposalStatus(str, Enum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"

class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    REJECTED = "REJECTED"
    DUPLICATE = "DUPLICATE"

class ActivityType(str, Enum):
    UPWORK = "Upwork Conversation"
    WHATSAPP = "WhatsApp Conversation"
    EMAIL = "Email"
    PHONE = "Phone Call"
    MEETING = "Meeting"
    PROPOSAL_SENT = "Proposal Sent"
    FOLLOW_UP = "Follow-up"
    NOTE = "Note"
    STATUS_CHANGE = "Status Change"
    OTHER = "Other"

