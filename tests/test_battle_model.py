import pytest
from meal_max.models.battle_model import BattleModel
from meal_max.models.kitchen_model import Meal


@pytest.fixture()
def battle_model():
    """Fixture to provide a new instance of BattleModel for each test."""
    return BattleModel()


@pytest.fixture
def sample_meal1():
    """Fixture providing a sample meal for testing."""
    return Meal(id=1, meal="Meal 1", cuisine="Italian", price=10.99, difficulty="MED")


@pytest.fixture
def sample_meal2():
    """Fixture providing a second sample meal for testing."""
    return Meal(id=2, meal="Meal 2", cuisine="Mexican", price=15.99, difficulty="HIGH")


@pytest.fixture
def sample_meal3():
    """Fixture providing a third sample meal for testing."""
    return Meal(id=3, meal="Meal 3", cuisine="Thai", price=8.99, difficulty="LOW")


##################################################
# Battle Management Test Cases
##################################################

def test_add_combatant(battle_model, sample_meal1):
    """Test adding a combatant to the battle."""
    battle_model.prep_combatant(sample_meal1)
    assert len(battle_model.combatants) == 1
    assert battle_model.combatants[0].meal == "Meal 1"


def test_add_combatant_list_capacity(battle_model, sample_meal1, sample_meal2, sample_meal3):
    """Test error when adding a third combatant, exceeding list capacity."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)

    # Adding a third combatant should raise ValueError due to list capacity limit
    with pytest.raises(ValueError, match="Combatant list is full, cannot add more combatants."):
        battle_model.prep_combatant(sample_meal3)


def test_clear_combatants(battle_model, sample_meal1):
    """Test clearing the combatants list."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.clear_combatants()
    assert len(battle_model.combatants) == 0, "Combatants list should be empty after clearing"


def test_battle_insufficient_combatants(battle_model):
    """Test starting a battle with insufficient combatants."""
    with pytest.raises(ValueError, match="Two combatants must be prepped for a battle."):
        battle_model.battle()


def test_battle_success(battle_model, sample_meal1, sample_meal2, mocker):
    """Test successful battle between two meals."""
    # Mock get_random to control the outcome of the battle
    mocker.patch("meal_max.utils.random_utils.get_random", return_value=0.5)
    mocker.patch("meal_max.models.battle_model.update_meal_stats")  # Mock DB update

    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)

    winner = battle_model.battle()

    assert winner in ["Meal 1", "Meal 2"], "The battle result should yield one of the combatants as the winner."
    assert len(battle_model.combatants) == 1, "One combatant should remain after the battle"


##################################################
# Score Calculation Test Cases
##################################################

def test_get_battle_score_medium_difficulty(battle_model, sample_meal1):
    """Test battle score calculation for a medium-difficulty meal."""
    score = battle_model.get_battle_score(sample_meal1)
    expected_score = (sample_meal1.price * len(sample_meal1.cuisine)) - 2  # MED difficulty modifier is 2
    assert score == expected_score, f"Expected score {expected_score}, but got {score}"


def test_get_battle_score_high_difficulty(battle_model, sample_meal2):
    """Test battle score calculation for a high-difficulty meal."""
    score = battle_model.get_battle_score(sample_meal2)
    expected_score = (sample_meal2.price * len(sample_meal2.cuisine)) - 1  # HIGH difficulty modifier is 1
    assert score == expected_score, f"Expected score {expected_score}, but got {score}"


def test_get_battle_score_low_difficulty(battle_model, sample_meal3):
    """Test battle score calculation for a low-difficulty meal."""
    score = battle_model.get_battle_score(sample_meal3)
    expected_score = (sample_meal3.price * len(sample_meal3.cuisine)) - 3  # LOW difficulty modifier is 3
    assert score == expected_score, f"Expected score {expected_score}, but got {score}"


##################################################
# Retrieve Combatants Test Cases
##################################################

def test_get_combatants(battle_model, sample_meal1, sample_meal2):
    """Test retrieving the current list of combatants."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)
    combatants = battle_model.get_combatants()

    assert len(combatants) == 2
    assert combatants[0].meal == "Meal 1"
    assert combatants[1].meal == "Meal 2"