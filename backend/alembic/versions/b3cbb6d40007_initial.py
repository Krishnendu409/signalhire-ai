"""initial

Revision ID: b3cbb6d40007
Revises: 
Create Date: 2026-05-28 08:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b3cbb6d40007'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users table
    op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=True),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('role', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_email', 'users', ['email'])

    # jobs table
    op.create_table('jobs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('recruiter_id', sa.UUID(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('raw_text', sa.String(), nullable=False),
        sa.Column('parsed_requirements', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('embedding_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['recruiter_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_jobs_recruiter_id', 'jobs', ['recruiter_id'])

    # candidates table
    op.create_table('candidates',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('recruiter_id', sa.UUID(), nullable=True),
        sa.Column('resume_file_key', sa.String(), nullable=False),
        sa.Column('parsed_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('embedding_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('layout_complexity', sa.Float(), nullable=True),
        sa.Column('extraction_confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['recruiter_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_candidates_recruiter_id', 'candidates', ['recruiter_id'])

    # ranking_jobs table
    op.create_table('ranking_jobs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('job_id', sa.UUID(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('total_candidates', sa.Integer(), nullable=True),
        sa.Column('results', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ranking_jobs_job_id', 'ranking_jobs', ['job_id'])

    # audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('action_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # recruiter_feedback table
    op.create_table('recruiter_feedback',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('ranking_job_id', sa.UUID(), nullable=True),
        sa.Column('candidate_id', sa.UUID(), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('reason', sa.String(), nullable=True),
        sa.Column('comment', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id']),
        sa.ForeignKeyConstraint(['ranking_job_id'], ['ranking_jobs.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_recruiter_feedback_ranking_job_id', 'recruiter_feedback', ['ranking_job_id'])


def downgrade() -> None:
    op.drop_index('ix_recruiter_feedback_ranking_job_id', table_name='recruiter_feedback')
    op.drop_table('recruiter_feedback')
    op.drop_table('audit_logs')
    op.drop_index('ix_ranking_jobs_job_id', table_name='ranking_jobs')
    op.drop_table('ranking_jobs')
    op.drop_index('ix_candidates_recruiter_id', table_name='candidates')
    op.drop_table('candidates')
    op.drop_index('ix_jobs_recruiter_id', table_name='jobs')
    op.drop_table('jobs')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')