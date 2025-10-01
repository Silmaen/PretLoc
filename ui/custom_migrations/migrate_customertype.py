#!/usr/bin/env python3
"""
Script to safely migrate customer types from string to foreign key.
This must be run BEFORE Django migrations to prevent data loss.
"""
import json
import os
from pathlib import Path
from sys import stderr, path, argv

# Setup Django environment
path.append("/app")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "PretLoc.settings")

import django

django.setup()

from django.db import connection, transaction

# Backup file path
BACKUP_FILE = Path("/app/data/customer_type_backup.json")

# Type mapping from old values to new CustomerType data
TYPE_MAPPING = {
    "member": {
        "name": "Membre du CA",
        "code": "MEMBER",
        "entity_type": "physical",
        "color": "#1abc9c",
    },
    "physical": {
        "name": "Personne physique de Genay",
        "code": "PHYSICAL",
        "entity_type": "physical",
        "color": "#3498db",
    },
    "phys_ext": {
        "name": "Personne physique extérieure",
        "code": "PHYS_EXT",
        "entity_type": "physical",
        "color": "#9b59b6",
    },
    "legal": {
        "name": "Personne morale de Genay",
        "code": "LEGAL",
        "entity_type": "legal",
        "color": "#e67e22",
    },
    "legal_ext": {
        "name": "Personne morale extérieure",
        "code": "LEGAL_EXT",
        "entity_type": "legal",
        "color": "#e74c3c",
    },
    "asso": {
        "name": "Association de Genay",
        "code": "ASSO",
        "entity_type": "legal",
        "color": "#2ecc71",
    },
    "asso_ext": {
        "name": "Association extérieure",
        "code": "ASSO_EXT",
        "entity_type": "legal",
        "color": "#f1c40f",
    },
}


def backup_data():
    """Backup existing customer_type values and prepare for migration"""
    try:
        with connection.cursor() as cursor:
            # Check if column exists in its original form
            cursor.execute(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'ui_customer' AND column_name = 'customer_type'
            """
            )
            if not cursor.fetchone():
                print("Column 'customer_type' not found, assuming already migrated")
                return True

            # Backup data
            cursor.execute(
                "SELECT id, customer_type FROM ui_customer WHERE customer_type IS NOT NULL"
            )
            customers = cursor.fetchall()

            if not customers:
                print("No data to backup")
                return True

            backup_data = [{"id": cust[0], "type": cust[1]} for cust in customers]

            BACKUP_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(BACKUP_FILE, "w") as f:
                json.dump(backup_data, f, indent=2)

            print(f"Backed up {len(backup_data)} customers to {BACKUP_FILE}")

            # First remove the NOT NULL constraint
            with transaction.atomic():
                cursor.execute(
                    "ALTER TABLE ui_customer ALTER COLUMN customer_type DROP NOT NULL"
                )
                print("Removed NOT NULL constraint from customer_type column")

            # Now we can set values to NULL
            with transaction.atomic():
                cursor.execute("UPDATE ui_customer SET customer_type = NULL")
                print("Set all customer_type values to NULL for safe migration")

            return True
    except Exception as e:
        print(f"Error during backup: {e}")
        return False


def restore_data():
    """Restore data after Django has performed the migrations"""
    if not BACKUP_FILE.exists():
        print("Backup file not found")
        return False

    try:
        with open(BACKUP_FILE, "r") as f:
            loaded_data = json.load(f)

        from django.apps import apps

        customer_type = apps.get_model("ui", "CustomerType")

        # Create CustomerTypes
        type_mapping = {}
        for old_type, data in TYPE_MAPPING.items():
            customer_type, created = customer_type.objects.get_or_create(
                code=data["code"],
                defaults={
                    "name": data["name"],
                    "description": f"Migrated from {old_type}",
                    "entity_type": data["entity_type"],
                    "color": data["color"],
                },
            )
            type_mapping[old_type] = customer_type.id

        # Update customers directly through SQL to avoid ORM conflicts
        with connection.cursor() as cursor:
            updated_count = 0
            for item in loaded_data:
                old_type = item["type"]
                if old_type in type_mapping:
                    cursor.execute(
                        "UPDATE ui_customer SET customer_type_id = %s WHERE id = %s",
                        [type_mapping[old_type], item["id"]],
                    )
                    updated_count += 1

            # Clean up the old column if it still exists
            try:
                cursor.execute("ALTER TABLE ui_customer DROP COLUMN old_customer_type")
                print("Dropped old_customer_type column")
            except Exception as e:
                print(f"old_customer_type column already removed {e}", file=stderr)

        print(f"Restoration completed for {updated_count} customers")
        return True
    except Exception as e:
        print(f"Error during restoration: {e}")
        return False


def main():
    """Main function to handle backup or restoration"""
    if len(argv) > 1 and argv[1] == "restore":
        if not BACKUP_FILE.exists():
            print("Backup file not found, skipping restoration")
            return
        print("Restoration mode.")
        success = restore_data()
        BACKUP_FILE.unlink()
    else:
        print("Backup mode...")
        success = backup_data()

    if success:
        print("Operation successful")
    else:
        print("Operation failed", file=stderr)
        exit(1)


if __name__ == "__main__":
    main()
