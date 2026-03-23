"""SQLModel models - combined database models and Pydantic schemas."""

from datetime import datetime

from pydantic import EmailStr
from sqlmodel import Field, SQLModel


# Base models for creation/update (without id and timestamps)
class UserBase(SQLModel):
    """Base user model for creation and updates."""

    email: EmailStr = Field(index=True, unique=True)
    name: str | None = Field(default=None, max_length=255)


class PostBase(SQLModel):
    """Base post model for creation and updates."""

    title: str = Field(max_length=255)
    content: str | None = Field(default=None)


# Database table models
class User(UserBase, table=True):
    """User database model."""

    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Post(PostBase, table=True):
    """Post database model."""

    __tablename__ = "posts"

    id: int | None = Field(default=None, primary_key=True)
    author_id: int = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Create/Update schemas (for API input)
class UserCreate(UserBase):
    """Schema for creating a user."""

    pass


class UserUpdate(SQLModel):
    """Schema for updating a user."""

    email: EmailStr | None = None
    name: str | None = None


class PostCreate(PostBase):
    """Schema for creating a post."""

    author_id: int


class PostUpdate(SQLModel):
    """Schema for updating a post."""

    title: str | None = None
    content: str | None = None


# Response schemas (for API output)
class UserResponse(UserBase):
    """Schema for user response."""

    id: int
    created_at: datetime
    updated_at: datetime


class PostResponse(PostBase):
    """Schema for post response."""

    id: int
    author_id: int
    created_at: datetime
    updated_at: datetime
