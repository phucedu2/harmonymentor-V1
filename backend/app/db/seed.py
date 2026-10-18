from sqlalchemy.orm import Session

from ..content.seed_data import seed_initial_data


def seed_database(db: Session) -> None:
    seed_initial_data(db)
