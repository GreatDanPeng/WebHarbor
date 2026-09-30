"""Build-time seed entry point for the Airbnb mirror.

Materializes instance/airbnb.db deterministically from the tracked
source_data_listings.json / source_data_content.json snapshots
(PYTHONHASHSEED=0, frozen mirror date, frozen benchmark password hash).
The Dockerfile copies the result into instance_seed/airbnb.db.
"""
from app import main

if __name__ == '__main__':
    main()
