from alumni_hub.platform import events_pb2


from event_emitter.log_event_emitter import LogEventEmitter


def test_log_event_emmiter(caplog):
    caplog.set_level('DEBUG')

    event = events_pb2.Event(
        initiator_id=1,
    )

    caplog.clear()

    LogEventEmitter().emit(event)

    assert caplog.records[0].message == '{"initiatorId": "1"}'
