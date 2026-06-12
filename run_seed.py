from app import app
from portal.seed import seed_initial_data

with app.app_context():
    seed_initial_data(app)

print("Seed complete.")