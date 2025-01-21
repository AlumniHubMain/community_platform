from alumni_hub.platform import events_pb2


class NotificationEventBuilder:
    @staticmethod
    def build_meeting_invitation_event(
        inviter_id: int, invited_id: int, meeting_id: int
    ) -> events_pb2.Event:
        return events_pb2.Event(
            event_type=events_pb2.eMeetingInvitation,
            initiator_id=inviter_id,
            recipient_id=invited_id,
            meeting_invitation=events_pb2.MeetingInvitationEvent(meeting_id=meeting_id),
        )

    @staticmethod
    def build_meeting_response_event(user_id: int, meeting_id: int) -> events_pb2.Event:
        return events_pb2.Event(
            event_type=events_pb2.eMeetingResponse,
            initiator_id=user_id,
            recipient_id=0,  # unspecified, send to organisers
            meeting_response=events_pb2.MeetingResponseEvent(meeting_id=meeting_id),
        )
        
    @staticmethod
    def build_meeting_update_event(updater_id: int, recipient_id: int, meeting_id: int) -> events_pb2.Event:
        return events_pb2.Event(
            event_type=events_pb2.eMeetingUpdate,
            initiator_id=updater_id,
            recipient_id=recipient_id,
            meeting_response=events_pb2.MeetingUpdateEvent(meeting_id=meeting_id),
        )
