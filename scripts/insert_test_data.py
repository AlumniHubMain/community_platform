import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
# TODO: remove this - bad idea to add parent directory to Python path
# Add parent directory to Python path to enable imports
sys.path.append(str(Path(__file__).parent.parent))

from db_common.config import DatabaseSettings
from db_common.db import DatabaseManager
from db_common.models import (
    ORMUserProfile, ORMLinkedInProfile, ORMMeetingIntent,
    ORMMeeting, ORMMeetingResponse
)
from db_common.enums.users import (
    ELocation, EGrade, EExpertiseArea, ESpecialisation,
    EIndustry, ESkills, ECompanyServices, EInterests,
    ERequestsToCommunity
)
from db_common.enums.meeting_intents import (
    EMeetingIntentMeetingType, EMeetingIntentQueryType,
    EMeetingIntentHelpRequestType, EMeetingIntentLookingForType
)
from db_common.enums.meetings import EMeetingStatus, EMeetingUserRole, EMeetingResponse

async def insert_test_data():
    settings = DatabaseSettings()
    db = DatabaseManager(settings)
    
    async with db.session() as session:
        # Create test users
        users = [
            ORMUserProfile(
                name="John",
                surname="Doe",
                email="john@example.com",
                location=ELocation.london_uk,
                grade=EGrade.grade1,
                expertise_area=[EExpertiseArea.development, EExpertiseArea.devops],
                specialisation=[ESpecialisation.backend, ESpecialisation.frontend],
                industry=[EIndustry.industry1],
                skills=[ESkills.skill1, ESkills.skill2],
                current_company="Tech Corp",
                company_services=[ECompanyServices.vkservice1],
                interests=[EInterests.interest1],
                requests_to_community=[ERequestsToCommunity.friendship],
                telegram_name="johndoe",
                telegram_id=123456789,
                about="Senior Software Engineer",
                avatars=["avatar1.jpg", "avatar2.jpg"],
                linkedin_link="https://linkedin.com/in/johndoe",
                referral=True
            ),
            ORMUserProfile(
                name="Jane",
                surname="Smith",
                email="jane@example.com",
                location=ELocation.moscow_russia,
                grade=EGrade.grade2,
                expertise_area=[EExpertiseArea.product_management],
                specialisation=[ESpecialisation.product_lifetime_management],
                industry=[EIndustry.industry2],
                skills=[ESkills.skill1],
                current_company="Product Co",
                company_services=[ECompanyServices.yandexservice1],
                interests=[EInterests.interest2],
                telegram_name="janesmith",
                telegram_id=987654321,
                about="Product Manager",
                linkedin_link="https://linkedin.com/in/janesmith",
                referral=False
            )
        ]
        
        session.add_all(users)
        await session.flush()
        
        # Create LinkedIn profiles
        linkedin_profiles = [
            ORMLinkedInProfile(
                user_id=users[0].id,
                profile_url="https://linkedin.com/in/johndoe",
                headline="Senior Software Engineer",
                location_name="London, UK",
                industry="Technology",
                summary="Experienced software engineer with focus on backend development",
                experience=[{
                    "company": "Tech Corp",
                    "title": "Senior Software Engineer",
                    "duration": "2020-present"
                }],
                education=[{
                    "school": "University of London",
                    "degree": "Computer Science",
                    "year": "2015-2019"
                }],
                skills={"programming": ["Python", "Java", "SQL"]}
            ),
            ORMLinkedInProfile(
                user_id=users[1].id,
                profile_url="https://linkedin.com/in/janesmith",
                headline="Product Manager",
                location_name="Moscow, Russia",
                industry="Technology",
                summary="Product manager with expertise in B2B products",
                experience=[{
                    "company": "Product Co",
                    "title": "Product Manager",
                    "duration": "2019-present"
                }],
                education=[{
                    "school": "Moscow State University",
                    "degree": "Business Administration",
                    "year": "2014-2018"
                }],
                skills={"product": ["Strategy", "Analytics", "User Research"]}
            )
        ]
        
        session.add_all(linkedin_profiles)
        
        # Create meeting intents
        meeting_intents = [
            ORMMeetingIntent(
                user_id=users[0].id,
                meeting_type=EMeetingIntentMeetingType.online,
                query_type=EMeetingIntentQueryType.interests_chatting,
                help_request_type=EMeetingIntentHelpRequestType.development,
                looking_for_type=EMeetingIntentLookingForType.work,
                text_intent="Looking for development opportunities"
            ),
            ORMMeetingIntent(
                user_id=users[1].id,
                meeting_type=EMeetingIntentMeetingType.offline,
                query_type=EMeetingIntentQueryType.startup_discussion,
                help_request_type=EMeetingIntentHelpRequestType.product,
                looking_for_type=EMeetingIntentLookingForType.cofounder,
                text_intent="Seeking co-founder for startup"
            )
        ]
        
        session.add_all(meeting_intents)
        
        # Create meetings
        meetings = [
            ORMMeeting(
                description="Technical Discussion",
                location="Zoom",
                scheduled_time=datetime.utcnow() + timedelta(days=1),
                status=EMeetingStatus.new
            ),
            ORMMeeting(
                description="Product Strategy Meeting",
                location="Office",
                scheduled_time=datetime.utcnow() + timedelta(days=2),
                status=EMeetingStatus.confirmed
            )
        ]
        
        session.add_all(meetings)
        await session.flush()
        
        # Create meeting responses
        meeting_responses = [
            ORMMeetingResponse(
                user_id=users[0].id,
                meeting_id=meetings[0].id,
                role=EMeetingUserRole.organizer,
                response=EMeetingResponse.confirmed
            ),
            ORMMeetingResponse(
                user_id=users[1].id,
                meeting_id=meetings[0].id,
                role=EMeetingUserRole.attendee,
                response=EMeetingResponse.tentative
            ),
            ORMMeetingResponse(
                user_id=users[1].id,
                meeting_id=meetings[1].id,
                role=EMeetingUserRole.organizer,
                response=EMeetingResponse.confirmed
            ),
            ORMMeetingResponse(
                user_id=users[0].id,
                meeting_id=meetings[1].id,
                role=EMeetingUserRole.attendee,
                response=EMeetingResponse.declined
            )
        ]
        
        session.add_all(meeting_responses)
        await session.commit()

if __name__ == "__main__":
    asyncio.run(insert_test_data())