from session import get_engine, Base
import models

Base.metadata.create_all(bind=get_engine())
print("Tables created.")