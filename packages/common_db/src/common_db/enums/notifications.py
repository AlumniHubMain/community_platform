from enum import Enum


class ENotificationType(Enum):
    """The enum containing notification types"""
    user_test: str = 'user_test'
    meeting_invitation: str = 'meeting_invitation'
