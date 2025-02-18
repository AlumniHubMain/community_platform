from common_db.schemas.forms import FormCreate, FormRead, EFormIntentType
from common_db.enums.forms import EFormIntentType
from common_db.schemas.matching import SUPPORTED_INTENTS, MatchingResultRead, MatchingRequest
from common_db.models import ORMForm, ORMUserProfile, ORMMatchingResult
from message_broker.factory import BrokerFactory, BrokerType
from message_broker.broker import MessageBroker
from fastapi import HTTPException, HTMLResponse

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
import datetime

from settings import settings


class FormsManager:
    """
    Класс для управления анкетами пользователей.
    """

    broker = BrokerFactory.create_broker(BrokerType.GOOGLE_PUBSUB, project_id=..., credentials=...)
    
    __matching_message_broker: MessageBroker = None

    @classmethod
    async def matching_message_broker(cls) -> MessageBroker:
        if not cls.__matching_message_broker:
            cls.__matching_message_broker = BrokerFactory.create_broker(
                BrokerType.GOOGLE_PUBSUB, 
                project_id=settings.emitter_settings.matching_requests_google_pubsub_project_id,
                credentials=settings.google_application_credentials
            )
        return cls.__matching_message_broker
    
    @classmethod
    async def check_user_exists(cls, session: AsyncSession, user_id: int):
        user: ORMUserProfile | None = await session.get(
            ORMUserProfile, user_id
        )
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
    
    @classmethod
    async def check_form_exists(cls, session: AsyncSession, form_id: int):
        form: ORMForm | None = await session.get(
            ORMForm, form_id
        )
        if not form:
            raise HTTPException(status_code=404, detail="Form not found")
    
    @classmethod
    async def get_user_form(
        cls, session: AsyncSession, user_id: int, intent_type: EFormIntentType
    ) -> FormRead:

        await cls.check_user_exists(session, user_id)
        
        # Select one last form by User and Intent type.
        result = await session.execute(
            select(ORMForm)
            .where(ORMForm.user_id == user_id)
            .where(ORMForm.intent == intent_type)
            .order_by(desc("created_at"))
            .limit(1)
        )
        form_orm = result.scalar_one_or_none()
        if form_orm is None:
            raise HTTPException(status_code=404, detail="Form not found")
        return FormRead.model_validate(form_orm)

    @classmethod
    async def create_form(
        cls, session: AsyncSession, form: FormCreate
    ) -> FormRead:    
        await cls.check_user_exists(session, form.user_id)
        form_orm = ORMForm(
            **form.model_dump(exclude_unset=True, exclude_none=True)
        )
        session.add(form_orm)
        await session.commit()
        return FormRead.model_validate(form_orm)

    @classmethod
    async def send_match(
        cls, session: AsyncSession, user_id: int, form_id: int, intent: EFormIntentType
    ) -> MatchingResultRead:
        await cls.check_user_exists(session, user_id)
        await cls.check_form_exists(session, form_id)
        
        if not (intent in SUPPORTED_INTENTS):
            raise HTTPException(status_code=400, detail=f"Intent type \"{intent.value}\" not supported for matching")
        
        matching_result_request = await session.execute(
            select(ORMMatchingResult)
            .where(ORMMatchingResult.user_id == user_id)
            .where(ORMMatchingResult.form_id == form_id)
            .order_by(desc("created_at"))
            .limit(1)
        )
        matching_result_orm = matching_result_request.scalar_one_or_none()
        if matching_result_orm is None or (matching_result_orm.updated_at - datetime.now()).total_seconds() >= settings.matching_requests.matching_delay_sec:
            
            message = MatchingRequest(
                user_id=user_id,
                form_id=form_id,
                model_settings_preset=settings.matching_requests.model_settings_preset,
                n=settings.matching_requests.requested_users_count
            )

            broker = await cls.matching_message_broker()
            broker.publish(topic=settings.emitter_settings.matching_requests_google_pubsub_topic, message=message)
            return HTMLResponse(status_code=102, detail="Waiting for results of matching")
        
        return MatchingResultRead.model_validate(matching_result_orm)
