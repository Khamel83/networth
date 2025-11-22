#!/usr/bin/env python3
"""
ASHLEY'S DATA IMPORT SYSTEM
Handles any format she throws at us
"""

import pandas as pd
import sqlite3
import json
import os
import re
from simple_matcher import SimpleTennisMatcher
from pathlib import Path

class AshleyDataImporter:
    def __init__(self, db_path="tennis_simple.db"):
        self.matcher = SimpleTennisMatcher(db_path)

    def normalize_skill_level(self, skill_input):
        """Handle various skill level formats"""
        if pd.isna(skill_input) or skill_input == "":
            return 3.0  # Default intermediate

        skill_str = str(skill_input).lower().strip()

        # Direct numbers
        try:
            return float(skill_str)
        except:
            pass

        # Descriptive terms
        skill_mapping = {
            "beginner": 2.0,
            "beginner-intermediate": 2.5,
            "advanced beginner": 2.5,
            "intermediate": 3.5,
            "intermediate-advanced": 4.0,
            "advanced": 4.5,
            "advanced-expert": 5.0,
            "expert": 5.5,
            "professional": 6.0,
            "pro": 6.0,
            "ntrp 2.0": 2.0,
            "ntrp 2.5": 2.5,
            "ntrp 3.0": 3.0,
            "ntrp 3.5": 3.5,
            "ntrp 4.0": 4.0,
            "ntrp 4.5": 4.5,
            "ntrp 5.0": 5.0,
            "2.0": 2.0,
            "2.5": 2.5,
            "3.0": 3.0,
            "3.5": 3.5,
            "4.0": 4.0,
            "4.5": 4.5,
            "5.0": 5.0,
        }

        # Extract numbers from text like "NTRP 3.5"
        number_match = re.search(r'\d+\.?\d*', skill_str)
        if number_match:
            return float(number_match.group())

        # Check descriptive mapping
        return skill_mapping.get(skill_str, 3.5)  # Default to intermediate

    def normalize_zip_code(self, zip_input):
        """Handle various zip code formats"""
        if pd.isna(zip_input) or zip_input == "":
            return "90210"  # Default Beverly Hills

        zip_str = str(zip_input).strip()

        # Extract 5-digit zip from longer formats like "90210-1234"
        zip_match = re.search(r'(\d{5})', zip_str)
        if zip_match:
            return zip_match.group()

        return zip_str

    def normalize_phone(self, phone_input):
        """Handle various phone number formats"""
        if pd.isna(phone_input) or phone_input == "":
            return ""

        phone_str = str(phone_input).strip()

        # Extract digits only
        digits = re.findall(r'\d', phone_str)

        # Handle different lengths
        if len(digits) == 10:
            return f"{''.join(digits[:3])}-{''.join(digits[3:6])}-{''.join(digits[6:])}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"{''.join(digits[1:4])}-{''.join(digits[4:7])}-{''.join(digits[7:])}"
        elif len(digits) >= 7:
            return f"{''.join(digits[:3])}-{''.join(digits[3:6])}-{''.join(digits[6:])}"

        return phone_str

    def normalize_days(self, days_input):
        """Handle various day formats"""
        if pd.isna(days_input) or days_input == "":
            return ["monday", "wednesday", "saturday"]  # Default

        days_str = str(days_input).lower()

        day_mapping = {
            "mon": "monday",
            "tue": "tuesday",
            "tues": "tuesday",
            "wed": "wednesday",
            "thur": "thursday",
            "thu": "thursday",
            "thurs": "thursday",
            "fri": "friday",
            "sat": "saturday",
            "sun": "sunday",
            "weekdays": "monday,tuesday,wednesday,thursday,friday",
            "weekends": "saturday,sunday",
            "m-f": "monday,tuesday,wednesday,thursday,friday",
            "any": "monday,tuesday,wednesday,thursday,friday,saturday,sunday",
            "all": "monday,tuesday,wednesday,thursday,friday,saturday,sunday"
        }

        # Replace abbreviations
        for abbrev, full in day_mapping.items():
            days_str = days_str.replace(abbrev, full)

        # Split on common separators
        days = re.split(r'[,;|\s]+', days_str)

        # Valid days
        valid_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        result_days = []

        for day in days:
            day = day.strip()
            if day in valid_days:
                result_days.append(day)

        return result_days if result_days else ["monday", "wednesday", "saturday"]

    def normalize_times(self, times_input):
        """Handle various time formats"""
        if pd.isna(times_input) or times_input == "":
            return ["evening"]  # Default

        times_str = str(times_input).lower()

        # Time mapping
        time_mapping = {
            "morning": ["morning"],
            "am": ["morning"],
            "afternoon": ["afternoon"],
            "pm": ["afternoon"],
            "evening": ["evening"],
            "night": ["evening"],
            "early morning": ["morning"],
            "late morning": ["morning"],
            "early afternoon": ["afternoon"],
            "late afternoon": ["afternoon"],
            "early evening": ["evening"],
            "late evening": ["evening"],
            "morning,evening": ["morning", "evening"],
            "morning,afternoon": ["morning", "afternoon"],
            "afternoon,evening": ["afternoon", "evening"],
            "any": ["morning", "afternoon", "evening"],
            "all": ["morning", "afternoon", "evening"],
            "flexible": ["morning", "afternoon", "evening"]
        }

        # Handle time ranges like "6am-8am"
        time_range_match = re.search(r'(\d{1,2})\s*(am|pm)\s*-\s*(\d{1,2})\s*(am|pm)', times_str)
        if time_range_match:
            start_time = int(time_range_match.group(1))
            start_period = time_range_match.group(2)

            if start_period == "am" and start_time < 12:
                return ["morning"]
            elif start_period == "pm" and start_time >= 5:
                return ["evening"]

        # Check time mapping
        for pattern, result in time_mapping.items():
            if pattern in times_str:
                return result

        return ["evening"]  # Default

    def import_csv_file(self, file_path, sheet_name=None):
        """Import from CSV or Excel file"""
        try:
            # Try Excel first
            if file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            else:
                df = pd.read_csv(file_path)

            return self.process_dataframe(df)

        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return {"success": False, "error": str(e), "imported": 0}

    def process_dataframe(self, df):
        """Process the DataFrame and add players"""
        imported_count = 0
        errors = []

        # Common column name variations
        column_mapping = {
            # Names
            'name': ['name', 'player', 'player_name', 'full_name', 'first_name', 'participant'],
            'email': ['email', 'email_address', 'mail', 'contact_email'],
            'phone': ['phone', 'phone_number', 'mobile', 'cell', 'contact_phone', 'tel'],
            'skill': ['skill', 'skill_level', 'level', 'rating', 'ntrp', 'ability'],
            'zip': ['zip', 'zip_code', 'zipcode', 'postal', 'postal_code', 'location'],
            'days': ['days', 'preferred_days', 'availability', 'schedule', 'when'],
            'times': ['times', 'preferred_times', 'time', 'when_available', 'best_time']
        }

        # Find matching columns
        columns_found = {}
        for target_col, possible_cols in column_mapping.items():
            for col in df.columns:
                if col.lower() in [c.lower() for c in possible_cols]:
                    columns_found[target_col] = col
                    break

        print(f"Found columns: {columns_found}")

        for index, row in df.iterrows():
            try:
                # Extract data with fallbacks
                name = str(row[columns_found.get('name', 'name')]) if 'name' in columns_found else f"Player {index + 1}"
                email = str(row[columns_found.get('email', 'email')]) if 'email' in columns_found else ""
                phone = self.normalize_phone(row[columns_found.get('phone', 'phone')]) if 'phone' in columns_found else ""
                skill = self.normalize_skill_level(row[columns_found.get('skill', 'skill')]) if 'skill' in columns_found else 3.5
                zip_code = self.normalize_zip_code(row[columns_found.get('zip', 'zip')]) if 'zip' in columns_found else "90210"
                days = self.normalize_days(row[columns_found.get('days', 'days')]) if 'days' in columns_found else ["monday", "wednesday", "saturday"]
                times = self.normalize_times(row[columns_found.get('times', 'times')]) if 'times' in columns_found else ["evening"]

                # Skip if no email (required for notifications)
                if not email or email.lower() == 'nan':
                    errors.append(f"Row {index + 1}: Missing email for {name}")
                    continue

                # Add player using simple_matcher
                player_id = self.matcher.add_player(
                    name=name.strip(),
                    email=email.strip().lower(),
                    phone=phone,
                    skill_level=skill,
                    location_zip=zip_code,
                    preferred_days=days,
                    preferred_times=times
                )

                imported_count += 1
                print(f"✅ Imported: {name} ({email})")

            except Exception as e:
                errors.append(f"Row {index + 1}: {str(e)}")
                print(f"❌ Error importing row {index + 1}: {e}")
                continue

        return {
            "success": True,
            "imported": imported_count,
            "errors": errors,
            "total_rows": len(df)
        }

    def import_from_folder(self, folder_path):
        """Import from all files in a folder"""
        folder = Path(folder_path)
        results = {}
        total_imported = 0

        for file_path in folder.glob("*"):
            if file_path.is_file() and file_path.suffix in ['.csv', '.xlsx', '.xls']:
                print(f"\nProcessing: {file_path.name}")
                result = self.import_csv_file(str(file_path))
                results[file_path.name] = result
                total_imported += result.get("imported", 0)

        return {
            "total_imported": total_imported,
            "files_processed": len(results),
            "results": results
        }

    def import_from_text(self, text_data):
        """Import from raw text data"""
        # Split into lines
        lines = text_data.strip().split('\n')

        # Look for patterns like "Name, Email, Phone, etc."
        imported_count = 0

        for line in lines:
            if ',' in line:
                # CSV-like format
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 2:  # At least name and email
                    try:
                        name = parts[0]
                        email = parts[1]
                        phone = parts[2] if len(parts) > 2 else ""
                        skill = self.normalize_skill_level(parts[3]) if len(parts) > 3 else 3.5
                        zip_code = self.normalize_zip_code(parts[4]) if len(parts) > 4 else "90210"

                        player_id = self.matcher.add_player(
                            name=name,
                            email=email,
                            phone=phone,
                            skill_level=skill,
                            location_zip=zip_code,
                            preferred_days=["monday", "wednesday", "saturday"],
                            preferred_times=["evening"]
                        )
                        imported_count += 1
                        print(f"✅ Imported: {name}")
                    except Exception as e:
                        print(f"❌ Error importing '{line}': {e}")

        return {"imported": imported_count}

# CLI for Ashley
def main():
    import argparse

    parser = argparse.ArgumentParser(description='Ashley\'s Tennis Data Importer')
    parser.add_argument('--file', help='CSV or Excel file to import')
    parser.add_argument('--folder', help='Folder with multiple files to import')
    parser.add_argument('--sheet', help='Excel sheet name (if applicable)')
    parser.add_argument('--text', help='Raw text data to import')
    parser.add_argument('--list-imported', action='store_true', help='List all imported players')

    args = parser.parse_args()

    importer = AshleyDataImporter()

    if args.file:
        print(f"📊 Importing from: {args.file}")
        result = importer.import_csv_file(args.file, args.sheet)

        print(f"\n✅ Import Complete!")
        print(f"📊 Total rows: {result.get('total_rows', 0)}")
        print(f"✅ Successfully imported: {result.get('imported', 0)}")

        if result.get('errors'):
            print(f"\n⚠️ Errors:")
            for error in result['errors'][:5]:  # Show first 5 errors
                print(f"   {error}")
            if len(result['errors']) > 5:
                print(f"   ... and {len(result['errors']) - 5} more errors")

    elif args.folder:
        print(f"📁 Importing from folder: {args.folder}")
        result = importer.import_from_folder(args.folder)

        print(f"\n✅ Folder Import Complete!")
        print(f"📁 Files processed: {result.get('files_processed', 0)}")
        print(f"✅ Total imported: {result.get('total_imported', 0)}")

    elif args.text:
        print(f"📝 Importing from text data")
        result = importer.import_from_text(args.text)
        print(f"✅ Text import complete! Imported: {result.get('imported', 0)}")

    elif args.list_imported:
        print("\n🎾 Current Players:")
        importer.matcher.list_players()

    else:
        print("📊 Ashley's Tennis Data Importer")
        print("\nUsage examples:")
        print("python data_import.py --file players.csv")
        print("python data_import.py --file tennis.xlsx --sheet 'Sheet1'")
        print("python data_import.py --folder ./data_files/")
        print("python data_import.py --text 'John,john@email.com,555-1234,3.5,90210'")

if __name__ == "__main__":
    main()