from pydantic import BaseModel

from ..enums.notifications import ENotificationType


class DTOEmptyParams(BaseModel):
    """The empty schema for notifications without parameters"""
    pass


class DTOMeetingInvitationParams(BaseModel):
    """The schema of meeting invitation"""
    inviter_id: int
    invited_id: int
    meeting_id: int


# dictionary that defines the correspondence between the type and parameters of notifications
type_params: dict[ENotificationType, type[BaseModel]] = {
    ENotificationType.meeting_invitation: DTOMeetingInvitationParams,
}
