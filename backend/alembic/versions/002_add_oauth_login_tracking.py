from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('oauth_provider', sa.String(), nullable=True))
    op.add_column('users', sa.Column('oauth_id', sa.String(), nullable=True))
    op.add_column('users', sa.Column('profile_picture_url', sa.String(), nullable=True))
    op.add_column('users', sa.Column('last_login', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('last_login_ip', sa.String(), nullable=True))
    op.add_column('users', sa.Column('login_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('users', sa.Column('login_method', sa.String(), server_default='email', nullable=False))
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('users', sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True))
    
    op.create_index('idx_users_oauth_id', 'users', ['oauth_id'], unique=False)
    op.create_index('idx_users_email_verified', 'users', ['email_verified'], unique=False)
    op.create_index('idx_users_last_login', 'users', ['last_login'], unique=False)
    
    op.execute("UPDATE users SET email_verified = is_verified WHERE is_verified = true")


def downgrade() -> None:
    op.drop_index('idx_users_last_login', table_name='users')
    op.drop_index('idx_users_email_verified', table_name='users')
    op.drop_index('idx_users_oauth_id', table_name='users')
    
    op.drop_column('users', 'email_verified_at')
    op.drop_column('users', 'email_verified')
    op.drop_column('users', 'login_method')
    op.drop_column('users', 'login_count')
    op.drop_column('users', 'last_login_ip')
    op.drop_column('users', 'last_login')
    op.drop_column('users', 'profile_picture_url')
    op.drop_column('users', 'oauth_id')
    op.drop_column('users', 'oauth_provider')
