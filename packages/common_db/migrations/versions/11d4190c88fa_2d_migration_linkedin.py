"""2d-migration_linkedin

Revision ID: 11d4190c88fa
Revises: fbadf0e9b29c
Create Date: 2025-01-28 17:11:22.577700

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from common_db.config import db_settings


schema: str = db_settings.db.db_schema

# revision identifiers, used by Alembic.
revision: str = "11d4190c88fa"
down_revision: Union[str, None] = "fbadf0e9b29c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### LinkedIn API limits table ###
    op.create_table(
        "linkedin_api_limits",
        sa.Column("provider_type", sa.String(), nullable=False),
        sa.Column("provider_id", sa.String(), nullable=False),
        sa.Column("credits_left", sa.Integer(), nullable=False),
        sa.Column("rate_limit_left", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("TIMEZONE('utc', now())"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        schema=schema,
    )
    op.create_index(
        "idx_limits_status",
        "linkedin_api_limits",
        ["credits_left", "rate_limit_left"],
        unique=False,
        schema=schema,
    )
    op.create_index(
        "idx_provider_unique",
        "linkedin_api_limits",
        ["provider_type", "provider_id"],
        unique=True,
        schema=schema,
    )
    op.create_index(
        "ix_linkedin_api_limits_provider_type",
        "linkedin_api_limits",
        ["provider_type"],
        unique=False,
        schema=schema,
    )

    # ### LinkedIn raw data table ###
    op.create_table(
        "linkedin_raw_data",
        sa.Column("target_linkedin_url", sa.String(), nullable=False),
        sa.Column(
            "raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("parsed_date", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("TIMEZONE('utc', now())"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("TIMEZONE('utc', now())"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        schema=schema,
    )
    op.create_index(
        "ix_linkedin_raw_data_parsed_date",
        "linkedin_raw_data",
        ["parsed_date"],
        unique=False,
        schema=schema,
    )
    op.create_index(
        "ix_linkedin_raw_data_url",
        "linkedin_raw_data",
        ["target_linkedin_url"],
        unique=False,
        schema=schema,
    )

    # ### LinkedIn profiles table ###
    op.create_table(
        "linkedin_profiles",
        sa.Column("users_id_fk", sa.Integer(), nullable=True),
        # Basic info
        sa.Column("public_identifier", sa.String(), nullable=True),
        sa.Column("linkedin_identifier", sa.String(), nullable=True),
        sa.Column("member_identifier", sa.String(), nullable=True),
        sa.Column("linkedin_url", sa.String(), nullable=True),
        sa.Column("first_name", sa.String(), nullable=True),
        sa.Column("last_name", sa.String(), nullable=True),
        sa.Column("headline", sa.Text(), nullable=True),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("photo_url", sa.String(), nullable=True),
        sa.Column("background_url", sa.String(), nullable=True),
        sa.Column("is_open_to_work", sa.Boolean(), nullable=True),
        sa.Column("is_premium", sa.Boolean(), nullable=True),
        sa.Column("pronoun", sa.String(), nullable=True),
        sa.Column("is_verification_badge_shown", sa.Boolean(), nullable=True),
        sa.Column("creation_date", sa.DateTime(), nullable=True),
        sa.Column("follower_count", sa.Integer(), nullable=True),
        sa.Column("parsed_date", sa.DateTime(), nullable=False),
        
        # Skills and additional info
        sa.Column(
            "skills",
            postgresql.JSONB(none_as_null=True, astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "languages",
            postgresql.JSONB(none_as_null=True, astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "recommendations",
            postgresql.JSONB(none_as_null=True, astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "certifications",
            postgresql.JSONB(none_as_null=True, astext_type=sa.Text()),
            nullable=True,
        ),
        
        # Current work info
        sa.Column("is_currently_employed", sa.Boolean(), nullable=True),
        sa.Column("current_jobs_count", sa.Integer(), nullable=True),
        sa.Column("current_company_label", sa.String(), nullable=True),
        sa.Column("current_company_linkedin_id", sa.String(), nullable=True),
        sa.Column("current_position_title", sa.String(), nullable=True),
        sa.Column("current_company_linkedin_url", sa.String(), nullable=True),
        
        # Target company info
        sa.Column("is_target_company_found", sa.Boolean(), nullable=True),
        sa.Column(
            "target_company_positions_count", sa.Integer(), nullable=True
        ),
        sa.Column("target_company_label", sa.String(), nullable=True),
        sa.Column("target_company_linkedin_id", sa.String(), nullable=True),
        sa.Column("target_position_title", sa.String(), nullable=True),
        sa.Column("target_company_linkedin_url", sa.String(), nullable=True),
        sa.Column(
            "is_employee_in_target_company", sa.Boolean(), nullable=True
        ),
        
        # Base fields
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("TIMEZONE('utc', now())"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("TIMEZONE('utc', now())"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["users_id_fk"],
            [f"{schema}.users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("users_id_fk"),
        schema=schema,
    )

    # ### LinkedIn education table ###
    op.create_table(
        "linkedin_education",
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("school", sa.String(), nullable=False),
        sa.Column("degree", sa.String(), nullable=True),
        sa.Column("field_of_study", sa.String(), nullable=True),
        sa.Column("start_date", sa.DateTime(), nullable=True),
        sa.Column("end_date", sa.DateTime(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("linkedin_url", sa.String(), nullable=True),
        sa.Column("school_logo", sa.String(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("TIMEZONE('utc', now())"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("TIMEZONE('utc', now())"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            [f"{schema}.linkedin_profiles.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "profile_id", "school", "degree", 
            name="uq_education_profile_url"
        ),
        schema=schema,
    )
    op.create_index(
        "ix_linkedin_education_profile_id",
        "linkedin_education",
        ["profile_id"],
        unique=False,
        schema=schema,
    )

    # ### LinkedIn experience table ###
    op.create_table(
        "linkedin_experience",
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("company_label", sa.String(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("company_linkedin_url", sa.String(), nullable=True),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("start_date", sa.DateTime(), nullable=True),
        sa.Column("end_date", sa.DateTime(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("duration", sa.String(), nullable=True),
        sa.Column("employment_type", sa.String(), nullable=True),
        sa.Column("company_logo", sa.String(), nullable=True),
        sa.Column("linkedin_url", sa.String(), nullable=True),
        sa.Column("linkedin_id", sa.String(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("TIMEZONE('utc', now())"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("TIMEZONE('utc', now())"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            [f"{schema}.linkedin_profiles.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "profile_id", "company_label", "title", "start_date",
            name="uq_experience_profile_position"
        ),
        schema=schema,
    )
    op.create_index(
        "ix_linkedin_experience_profile_id",
        "linkedin_experience",
        ["profile_id"],
        unique=False,
        schema=schema,
    )
    op.create_index(
        "ix_linkedin_experience_dates",
        "linkedin_experience",
        ["start_date", "end_date"],
        unique=False,
        schema=schema,
    )


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("linkedin_experience", schema=schema)
    op.drop_table("linkedin_education", schema=schema)
    op.drop_table("linkedin_profiles", schema=schema)
    op.drop_table("linkedin_raw_data", schema=schema)
    op.drop_table("linkedin_api_limits", schema=schema)
    # ### end Alembic commands ###
