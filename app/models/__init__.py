from app.models.template import Template

# Import all the models, so that Base has them before being imported by Alembic
__all__ = ["Template"]
