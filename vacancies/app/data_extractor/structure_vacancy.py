# Copyright 2024 Alumnihub
"""Structure of vacancy."""

from pydantic import BaseModel, Field


class Vacancy(BaseModel):
    """Structured representation of a job vacancy extracted by Gemini from HTML content.

    This model defines the expected format and structure for vacancy information,
    helping to standardize LLM output parsing.
    """

    title: str = Field(
        description="Job position title or role name extracted from the vacancy posting",
    )
    description: str = Field(
        description="Full job description including overview and key details of the position",
    )
    skills: list[str] = Field(
        description="List of required technical and soft skills for the position",
    )
    required_experience: str | None = Field(
        default=None,
        description="Required years of experience or experience level (e.g., '3-5 years', 'Entry level')",
    )
    location: str = Field(
        description="Physical location or geographical area of the job position",
    )

    level: str = Field(description="Seniority or professional level (e.g., 'Junior', 'Middle', 'Senior')")
    salary: str | None = Field(
        default=None,
        description="Salary range or compensation information if provided",
    )
    responsibilities: list[str] = Field(
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
