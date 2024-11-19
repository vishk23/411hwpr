import pytest
import sqlite3
from unittest.mock import patch, Mock
from contextlib import contextmanager
from meal_max.models.kitchen_model import create_meal, delete_meal, get_meal_by_id, get_meal_by_name, get_leaderboard, update_meal_stats, Meal
import re

@pytest.fixture
def sample_meal_data():
    """Fixture providing sample data for a meal."""
    return {"meal": "Pasta", "cuisine": "Italian", "price": 12.99, "difficulty": "MED"}

# Mocking the database connection for tests
@pytest.fixture
def mock_cursor(mocker):
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    # Mock the connection's cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None
    mock_cursor.fetchall.return_value = []
    mock_conn.commit.return_value = None

    # Mock the get_db_connection context manager from sql_utils
    @contextmanager
    def mock_get_db_connection():
        yield mock_conn

    mocker.patch("meal_max.models.kitchen_model.get_db_connection", mock_get_db_connection)

    return mock_cursor   # Return the mock cursor so we can set expectations per test

def normalize_whitespace(sql_query: str) -> str:
    return re.sub(r'\s+', ' ', sql_query).strip()

##################################################
# Meal Creation and Deletion Test Cases
##################################################

def test_create_meal(mock_cursor, sample_meal_data):
    """Test creating a new meal in the database."""
    create_meal(**sample_meal_data)

    expected_query = """
        INSERT INTO meals (meal, cuisine, price, difficulty)
        VALUES (?, ?, ?, ?)
    """
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    expected_query = normalize_whitespace(expected_query)
    actual_arguments = mock_cursor.execute.call_args[0][1]

    assert actual_query == expected_query, "The SQL query did not match the expected structure."
    assert actual_arguments == tuple(sample_meal_data.values()), "The SQL query arguments did not match the expected values."

def test_create_meal_duplicate(mock_cursor, sample_meal_data):
    """Test creating a meal with a duplicate name raises an error."""
    mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: meals.meal")

    with pytest.raises(ValueError, match=f"Meal with name '{sample_meal_data['meal']}' already exists"):
        create_meal(**sample_meal_data)


def test_create_meal_invalid_price():
    """Test creating a meal with an invalid price raises an error."""
    with pytest.raises(ValueError, match="Invalid price: -5. Price must be a positive number."):
        create_meal("Salad", "Vegetarian", -5, "LOW")


def test_delete_meal(mock_cursor):
    """Test soft deleting a meal from the database by meal ID."""
    mock_cursor.fetchone.return_value = [False]  # Meal exists and is not deleted

    delete_meal(1)

    expected_select_query = "SELECT deleted FROM meals WHERE id = ?"
    expected_update_query = "UPDATE meals SET deleted = TRUE WHERE id = ?"
    actual_select_query = mock_cursor.execute.call_args_list[0][0][0]
    actual_update_query = mock_cursor.execute.call_args_list[1][0][0]

    assert actual_select_query.strip() == expected_select_query.strip(), "The SELECT query did not match the expected structure."
    assert actual_update_query.strip() == expected_update_query.strip(), "The UPDATE query did not match the expected structure."


def test_delete_meal_not_found(mock_cursor):
    """Test error when trying to delete a non-existent meal."""
    mock_cursor.fetchone.return_value = None  # Meal does not exist

    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        delete_meal(999)


def test_delete_meal_already_deleted(mock_cursor):
    """Test error when trying to delete a meal that's already deleted."""
    mock_cursor.fetchone.return_value = [True]  # Meal is already deleted

    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        delete_meal(1)


##################################################
# Meal Retrieval Test Cases
##################################################

def test_get_meal_by_id(mock_cursor):
    """Test retrieving a meal by its ID."""
    mock_cursor.fetchone.return_value = (1, "Pasta", "Italian", 12.99, "MED", False)

    result = get_meal_by_id(1)
    expected_result = Meal(id=1, meal="Pasta", cuisine="Italian", price=12.99, difficulty="MED")

    assert result == expected_result, f"Expected {expected_result}, but got {result}"


def test_get_meal_by_id_not_found(mock_cursor):
    """Test error when retrieving a meal by ID that does not exist."""
    mock_cursor.fetchone.return_value = None  # No meal with this ID

    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        get_meal_by_id(999)


def test_get_meal_by_name(mock_cursor):
    """Test retrieving a meal by its name."""
    mock_cursor.fetchone.return_value = (1, "Pasta", "Italian", 12.99, "MED", False)

    result = get_meal_by_name("Pasta")
    expected_result = Meal(id=1, meal="Pasta", cuisine="Italian", price=12.99, difficulty="MED")

    assert result == expected_result, f"Expected {expected_result}, but got {result}"


def test_get_meal_by_name_not_found(mock_cursor):
    """Test error when retrieving a meal by name that does not exist."""
    mock_cursor.fetchone.return_value = None  # No meal with this name

    with pytest.raises(ValueError, match="Meal with name Nonexistent Meal not found"):
        get_meal_by_name("Nonexistent Meal")


##################################################
# Leaderboard Retrieval Test Cases
##################################################

def test_get_leaderboard(mock_cursor):
    """Test retrieving the leaderboard sorted by wins."""
    mock_cursor.fetchall.return_value = [
        (1, "Pasta", "Italian", 12.99, "MED", 10, 7, 0.7),
        (2, "Taco", "Mexican", 9.99, "HIGH", 15, 10, 0.67)
    ]

    leaderboard = get_leaderboard("wins")
    expected_leaderboard = [
        {"id": 1, "meal": "Pasta", "cuisine": "Italian", "price": 12.99, "difficulty": "MED", "battles": 10, "wins": 7, "win_pct": 70.0},
        {"id": 2, "meal": "Taco", "cuisine": "Mexican", "price": 9.99, "difficulty": "HIGH", "battles": 15, "wins": 10, "win_pct": 67.0}
    ]

    assert leaderboard == expected_leaderboard, f"Expected {expected_leaderboard}, but got {leaderboard}"


##################################################
# Meal Stats Update Test Cases
##################################################

def test_update_meal_stats_win(mock_cursor):
    """Test updating meal stats to record a win."""
    mock_cursor.fetchone.return_value = [False]  # Meal exists and is not deleted

    update_meal_stats(1, "win")
    expected_update_query = "UPDATE meals SET battles = battles + 1, wins = wins + 1 WHERE id = ?"
    actual_update_query = mock_cursor.execute.call_args_list[1][0][0]

    assert actual_update_query.strip() == expected_update_query.strip(), "The SQL query did not match the expected structure."


def test_update_meal_stats_loss(mock_cursor):
    """Test updating meal stats to record a loss."""
    mock_cursor.fetchone.return_value = [False]  # Meal exists and is not deleted

    update_meal_stats(1, "loss")
    expected_update_query = "UPDATE meals SET battles = battles + 1 WHERE id = ?"
    actual_update_query = mock_cursor.execute.call_args_list[1][0][0]

    assert actual_update_query.strip() == expected_update_query.strip(), "The SQL query did not match the expected structure."


def test_update_meal_stats_deleted_meal(mock_cursor):
    """Test error when updating stats for a deleted meal."""
    mock_cursor.fetchone.return_value = [True]  # Meal is marked as deleted

    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        update_meal_stats(1, "win")
