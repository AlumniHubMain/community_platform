# Copyright 2024 Alumnihub
"""Structure of vacancy."""

from pydantic import BaseModel, Field


class VacancyStructure(BaseModel):
    """Structured representation of a job vacancy extracted by Gemini from HTML content.

    This model defines the expected format and structure for vacancy information,
    helping to standardize LLM output parsing.
    """

    full_text: str = Field(
        description="Complete plain text content of the vacancy, including all descriptions, requirements, and benefits",
    )

    title: str = Field(
        description="Job position title or role name extracted from the vacancy posting",
    )
    description: str = Field(
        description="Full job description including overview and key details of the position",
    )
    skills: list[str] | None = Field(
        default=None,
        description="List of required technical and soft skills for the position",
    )
    required_experience: str | None = Field(
        default=None,
        description="Required years of experience or experience level (e.g., '3-5 years', 'Entry level')",
    )
    location: str = Field(
        description="Physical location or geographical area of the job position",
    )

    level: str | None = Field(
        default=None,
        description="Seniority or professional level (e.g., 'Junior', 'Middle', 'Senior')",
    )
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
    remote_type: str | None = Field(
        default=None,
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
