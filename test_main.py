import pytest
import tempfile
import os
import sqlite3
from fastapi.testclient import TestClient
from datetime import date, datetime

# Import the main app
import sys
sys.path.append('.')
from main import app, init_db, create_sample_data

client = TestClient(app)

@pytest.fixture
def test_db():
    """Create a temporary database for testing"""
    # Override the database URL for testing
    test_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    test_db_path = test_db_file.name
    test_db_file.close()

    # Update the app to use test database
    original_db_url = os.getenv('DATABASE_URL')
    os.environ['DATABASE_URL'] = f'sqlite:///{test_db_path}'

    # Initialize test database
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE players (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            skill_level REAL NOT NULL,
            preferred_days TEXT,
            preferred_times TEXT,
            location_zip TEXT,
            travel_radius INTEGER DEFAULT 15,
            match_types TEXT,
            is_active BOOLEAN DEFAULT 1,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE matches (
            id TEXT PRIMARY KEY,
            player1_id TEXT NOT NULL,
            player2_id TEXT NOT NULL,
            match_type TEXT NOT NULL,
            match_date DATE NOT NULL,
            status TEXT DEFAULT 'pending',
            suggested_location TEXT,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Insert test players
    test_players = [
        ("player1", "test1@example.com", "hash1", 3.5, '["monday"]', '["evening"]', "90210", 15, '["singles"]'),
        ("player2", "test2@example.com", "hash2", 4.0, '["monday"]', '["evening"]', "90211", 15, '["singles"]'),
    ]

    for player_data in test_players:
        cursor.execute("""
            INSERT INTO players (id, name, email, password_hash, skill_level,
                               preferred_days, preferred_times, location_zip,
                               travel_radius, match_types)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, player_data)

    conn.commit()
    conn.close()

    yield test_db_path

    # Cleanup
    os.unlink(test_db_path)
    if original_db_url:
        os.environ['DATABASE_URL'] = original_db_url
    else:
        del os.environ['DATABASE_URL']

class TestHealthEndpoint:
    def test_health_check(self, test_db):
        """Test the health endpoint returns correct status"""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "total_players" in data
        assert "pending_matches" in data
        assert "timestamp" in data

class TestAuthentication:
    def test_login_page_loads(self):
        """Test that the login page loads correctly"""
        response = client.get("/")
        assert response.status_code == 200
        assert "Tennis Match LA" in response.text

    def test_login_with_invalid_credentials(self, test_db):
        """Test login fails with invalid credentials"""
        response = client.post("/login", data={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 200
        assert "Invalid email or password" in response.text

class TestMatchingAlgorithm:
    def test_distance_calculation(self):
        """Test distance calculation between zip codes"""
        from main import calculate_distance

        # Test same zip code
        assert calculate_distance("90210", "90210") == 0

        # Test different zip codes
        distance = calculate_distance("90210", "90211")
        assert isinstance(distance, float)
        assert distance >= 0

    def test_common_time_check(self):
        """Test time compatibility checking"""
        from main import has_common_time

        # Test overlapping times
        assert has_common_time(["morning", "evening"], ["evening", "night"]) == True
        assert has_common_time(["morning"], ["morning"]) == True

        # Test non-overlapping times
        assert has_common_time(["morning"], ["evening"]) == False

    def test_common_day_check(self):
        """Test day compatibility checking"""
        from main import has_common_day

        # Test overlapping days
        assert has_common_day(["monday", "tuesday"], ["tuesday", "wednesday"]) == True
        assert has_common_day(["saturday"], ["saturday", "sunday"]) == True

        # Test non-overlapping days
        assert has_common_day(["monday"], ["tuesday"]) == False

    def test_generate_matches_creates_matches(self, test_db):
        """Test that the matching algorithm creates matches"""
        # Trigger matching
        response = client.get("/admin/trigger_matching")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "matches_created" in data
        assert isinstance(data["matches_created"], int)

class TestAPIEndpoints:
    def test_dashboard_requires_auth(self):
        """Test that dashboard requires authentication"""
        response = client.get("/dashboard", follow_redirects=False)
        assert response.status_code == 303  # Redirect to login

    def test_preferences_requires_auth(self):
        """Test that preferences page requires authentication"""
        response = client.get("/preferences", follow_redirects=False)
        assert response.status_code == 303  # Redirect to login

class TestDatabaseOperations:
    def test_database_connection(self, test_db):
        """Test database connection works"""
        from main import get_db

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM players")
        result = cursor.fetchone()
        assert result["count"] == 2  # Two test players
        conn.close()

class TestSampleData:
    def test_sample_data_creation(self):
        """Test sample data creation doesn't fail"""
        # This should not raise any exceptions
        create_sample_data()

class TestSystemIntegration:
    def test_full_system_health(self, test_db):
        """Test overall system health and integration"""
        # Check health endpoint
        health_response = client.get("/health")
        assert health_response.status_code == 200

        # Try to trigger matching
        match_response = client.get("/admin/trigger_matching")
        assert match_response.status_code == 200

        # Verify health still good after matching
        health_response2 = client.get("/health")
        assert health_response2.status_code == 200

class TestErrorHandling:
    def test_404_not_found(self):
        """Test 404 handling"""
        response = client.get("/nonexistent-page")
        assert response.status_code == 404

    def test_invalid_json_handling(self):
        """Test handling of invalid JSON data"""
        response = client.post(
            "/api/test",
            json="invalid json"
        )
        # Should handle gracefully (either 422 or other appropriate error)
        assert response.status_code != 500

if __name__ == "__main__":
    pytest.main([__file__, "-v"])