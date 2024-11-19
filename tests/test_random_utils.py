import pytest
import requests
from meal_max.utils.random_utils import get_random


@pytest.fixture
def mock_random_org(mocker):
    """Mock the requests.get call to random.org."""
    mock_response = mocker.Mock()
    mock_response.text = "0.42"  # Mock a valid random number response as a string
    mocker.patch("requests.get", return_value=mock_response)
    return mock_response


def test_get_random_success(mock_random_org):
    """Test successfully retrieving a random number from random.org."""
    result = get_random()
    assert result == 0.42, f"Expected random number 0.42, but got {result}"
    requests.get.assert_called_once_with(
        "https://www.random.org/decimal-fractions/?num=1&dec=2&col=1&format=plain&rnd=new", timeout=5
    )


def test_get_random_request_failure(mocker):
    """Simulate a request failure to random.org."""
    mocker.patch("requests.get", side_effect=requests.exceptions.RequestException("Connection error"))

    with pytest.raises(RuntimeError, match="Request to random.org failed: Connection error"):
        get_random()


def test_get_random_timeout(mocker):
    """Simulate a timeout when requesting from random.org."""
    mocker.patch("requests.get", side_effect=requests.exceptions.Timeout)

    with pytest.raises(RuntimeError, match="Request to random.org timed out."):
        get_random()


def test_get_random_invalid_response(mock_random_org):
    """Simulate an invalid response from random.org (non-numeric)."""
    mock_random_org.text = "invalid_response"

    with pytest.raises(ValueError, match="Invalid response from random.org: invalid_response"):
        get_random()