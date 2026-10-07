"""Shared bounded loop and security guards remain fixed for feature ablation."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Variant:
    context: bool = False
    skills: bool = False
    recovery: bool = False


VARIANTS = {
    "baseline": Variant(),
    "context": Variant(context=True),
    "skills": Variant(skills=True),
    "recovery": Variant(recovery=True),
    "full": Variant(True, True, True),
}


@dataclass(frozen=True)
class VariantV2:
    context: bool = False
    verification: bool = False
    skills: bool = False
    recovery: bool = False
    context_mode: str = "NO_COMPACTION"
    skill_mode: str = "NO_SKILLS"


V2_VARIANTS = {
    "baseline": VariantV2(),
    "context": VariantV2(context=True, context_mode="MANAGED_CONTEXT"),
    "verification": VariantV2(verification=True),
    "skills": VariantV2(skills=True, skill_mode="SELECTED_SKILL"),
    "recovery": VariantV2(recovery=True),
    "full": VariantV2(True, True, True, True, "MANAGED_CONTEXT", "SELECTED_SKILL"),
    "naive": VariantV2(context=True, context_mode="NAIVE_TRUNCATION"),
    "all_skills": VariantV2(skills=True, skill_mode="ALL_SKILLS_LOADED"),
}
