from pydantic import BaseModel, Field, HttpUrl


class Education(BaseModel):
    """Education entry schema for API input"""
    school: str
    degree: str | None = None
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None


class EducationResponse(BaseModel):
    """Response schema for education"""
    # TODO: вынести в локальный пакет
    school: str
    degree: str | None = None
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None

    class Config:
        from_attributes = True


class Experience(BaseModel):
    """Work experience entry schema for API input"""
    company: str
    title: str
    company_linkedin_url: HttpUrl | None = Field(default=None, alias="companyLinkedinUrl")
    location: str | None = None
    start_date: str | None = Field(default=None, alias="startDate")
    end_date: str | None = Field(default=None, alias="endDate")
    description: str | None = None
    duration: str | None = None
    employment_type: str | None = Field(default=None, alias="employmentType")


class ExperienceResponse(BaseModel):
    """Response schema for work experience"""
    # TODO: вынести в локальный пакет
    company: str
    title: str
    company_linkedin_url: HttpUrl | None = None
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None
    duration: str | None = None
    employment_type: str | None = None

    class Config:
        from_attributes = True
