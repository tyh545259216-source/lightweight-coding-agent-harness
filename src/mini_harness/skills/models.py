"""Skill metadata does not contain the instruction body."""

from pathlib import Path

from pydantic import BaseModel, Field


class SkillMetadata(BaseModel):
    name: str = Field(pattern=r"^[a-z][a-z0-9-]{0,63}$")
    description: str = Field(min_length=1, max_length=1000)
    path: Path
