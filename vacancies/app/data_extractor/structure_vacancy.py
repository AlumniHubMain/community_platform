# Copyright 2024 Alumnihub
"""Structure of vacancy."""

from pydantic import BaseModel, Field


class VacancyStructure(BaseModel):
    """Structured representation of a job vacancy extracted by Gemini."""

    full_text: str = Field(
        description="Complete plain text content of the vacancy, including all descriptions, requirements, and benefits",
    )

    title: str = Field(
        description="Clean job position title or role name",
    )
    description: str = Field(
        description="Clear textual description of the job position and its context",
    )
    skills: list[str] | None = Field(
        default=None,
        description="List of required technical and soft skills for the position extracted from the vacancy",
    )
    required_experience: str | None = Field(
        default=None,
        description="Required years of experience or experience level (e.g., '3-5 years', 'Entry level') extracted from the vacancy",
    )
    location: str = Field(
        description="Physical location or geographical area of the job position extracted from the vacancy",
    )

    level: str = Field(description="Seniority or professional level (e.g., 'Junior', 'Middle', 'Senior')")
    salary: str | None = Field(
        default=None,
        description="Salary range or compensation information if provided",
    )
    responsibilities: list[str] | None = Field(
        default=None,
        description="List of key job duties and responsibilities for the position",
    )
    benefits: list[str] | None = Field(
        default=None,
        description="List of company benefits, perks, and additional compensation offerings",
    )
    remote_type: str = Field(
        description="Work arrangement type: 'office' (on-site), 'hybrid', or 'remote'",
    )

    department: str | None = Field(
        default=None,
        description="Company department, division, or business unit offering the position",
    )

    additional_advantages: list[str] | None = Field(
        default=None,
        description="List of additional skills, experience, or qualifications that would be considered as advantages for the candidate",
    )
