from .base import Base, ObjectTable, PropertyTable

# Import models in dependency order
from .linkedin import ORMLinkedInProfile, ORMEducation, ORMWorkExperience, ORMLinkedInRawData
from .linkedin_helpers import ORMLinkedInApiLimits
from .matching import ORMMatchingResult
from .users import (
    ORMUserProfile,
    ORMSpecialisation,
    ORMUserSpecialisation,
    ORMInterest,
    ORMUserInterest,
    ORMUserIndustry,
    ORMSkill,
    ORMUserSkill,
    ORMRequestsCommunity,
    ORMUserRequestsCommunity,
    ORMReferralCode
)
from .meetings import ORMMeeting, ORMMeetingResponse
from .notifications import ORMUserNotifications
from .feedback import ORMMeetingFeedback
from .forms import ORMForm

# Make sure all models are imported before configuring
from sqlalchemy.orm import configure_mappers
configure_mappers()

__all__ = [
    "Base",
    "ObjectTable",
    "PropertyTable",
    "ORMUserProfile",
    "ORMSpecialisation",
    "ORMUserSpecialisation",
    "ORMInterest",
    "ORMUserInterest",
    "ORMUserIndustry",
    "ORMSkill",
    "ORMUserSkill",
    "ORMRequestsCommunity",
    "ORMUserRequestsCommunity",
    "ORMReferralCode",
    "ORMMeeting",
    "ORMMeetingResponse",
    "ORMMatchingResult",
    "ORMForm",
    "ORMLinkedInProfile",
    "ORMEducation",
    "ORMWorkExperience",
    "ORMLinkedInApiLimits",
    "ORMLinkedInRawData",
    "ORMUserNotifications",
]
