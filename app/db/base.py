# Import all the models, so that Base has them before being imported by Alembic
import app.models
from app.db.base_class import Base

__all__ = ["Base", *app.models.__all__]
