"""Seed system taxonomy. Safe to re-run; does not create personal household data."""

from sqlalchemy import select

from app.db.session import SessionLocal
from app.db.seed_taxonomy import TAXONOMY
from app.models.taxonomy import Category


def seed_system_categories() -> int:
    created = 0
    with SessionLocal() as db:
        for parent_name, children in TAXONOMY.items():
            parent = db.scalar(
                select(Category).where(
                    Category.household_id.is_(None),
                    Category.parent_category_id.is_(None),
                    Category.name == parent_name,
                    Category.is_system_seeded.is_(True),
                )
            )
            if not parent:
                parent = Category(
                    household_id=None,
                    parent_category_id=None,
                    name=parent_name,
                    description=f"System category: {parent_name}",
                    category_level=1,
                    is_system_seeded=True,
                    is_active=True,
                )
                db.add(parent)
                db.flush()
                created += 1
            for child_name in children:
                existing = db.scalar(
                    select(Category).where(
                        Category.household_id.is_(None),
                        Category.parent_category_id == parent.id,
                        Category.name == child_name,
                        Category.is_system_seeded.is_(True),
                    )
                )
                if existing:
                    continue
                db.add(
                    Category(
                        household_id=None,
                        parent_category_id=parent.id,
                        name=child_name,
                        description=f"System subcategory: {child_name}",
                        category_level=2,
                        is_system_seeded=True,
                        is_active=True,
                    )
                )
                created += 1
        db.commit()
    return created


def main() -> None:
    count = seed_system_categories()
    print(f"Seeded/ensured system categories. Newly created: {count}")


if __name__ == "__main__":
    main()
