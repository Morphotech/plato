# Import all the models, so that Base has them before being imported by Alembic
from app.db.base_class import Base
import app.models

__all__ = ['Base', *app.models.__all__]