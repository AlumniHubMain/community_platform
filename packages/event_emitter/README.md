# Notifications event emitter

The Event Emitter is a common interface to send notification events to the notification service using Google PubSub.

## Installation

```shell
pip install alumnihub.community_platform.event_emitter \
    --extra-index-url=https://europe-west3-python.pkg.dev/communityp-440714/community-platform/simple/
```

## Usage
```python
import logging

from alumnihub.community_platform.event_emitter import EmitterFactory, IProtoEmitter
from alumnihub.community_platform.event_emitter.events_pb2 import Event, MeetingInvitationEvent


logging.basicConfig(level=logging.INFO)

emitter: IProtoEmitter = EmitterFactory.create_event_emitter("log")
# Prod usage
pubsub_emitter: IProtoEmitter = EmitterFactory.create_event_emitter(
     settings.notification_target, # "pubsub",
     topic=settings.google_pubsub_notification_topic,
)

demo_event = Event(initiator_id=1, recipient_id=2, meeting_invitation=MeetingInvitationEvent(meeting_id=3))
emitter.emit(demo_event)

```

## Local development

```shell
# compile protobuf definitions
python setup.py build_protos

# install to local env
python setup.py develop

# or
pip install -e .

# or
python setup.py sdist bdist_wheel
pip install ./dist/alumnihub_event_emitter-0.1.2-py3-none-any.whl # replace the version
```

### Build and publish
```shell
rm -rf dist

# bump version manually or via Python bumpversion 

python setup.py sdist bdist_wheel

export TWINE_PASSWORD=$(gcloud auth print-access-token)
twine upload --repository community-platform dist/*
```

Environment setup taken from https://console.cloud.google.com/artifacts/python/communityp-440714/europe-west3/community-platform?chat=true&inv=1&invt=AbjwaA&project=communityp-440714

Example `~/.pypirc`:
```toml
[distutils]
index-servers="community-platform"

[community-platform]
repository="https://europe-west3-python.pkg.dev/communityp-440714/community-platform/"
username="oauth2accesstoken"
```
