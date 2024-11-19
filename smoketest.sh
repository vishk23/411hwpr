#!/bin/bash

# Define the base URL for the Flask API
BASE_URL="http://localhost:5000/api"

# Flag to control whether to echo JSON output
ECHO_JSON=false

# Parse command-line arguments
while [ "$#" -gt 0 ]; do
  case $1 in
    --echo-json) ECHO_JSON=true ;;
    *) echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done



###############################################
#
# Health checks
#
###############################################

# Function to check the health of the service
check_health() {
  echo "Checking health status..."
  curl -s -X GET "$BASE_URL/health" | grep -q '"status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Service is healthy."
  else
    echo "Health check failed."
    exit 1
  fi
}

# Function to check the database connection
check_db() {
  echo "Checking database connection..."
  curl -s -X GET "$BASE_URL/db-check" | grep -q '"database_status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Database connection is healthy."
  else
    echo "Database check failed."
    exit 1
  fi
}


##########################################################
#
# Meal Management
#
##########################################################

create_meal() {
  meal=$1
  cuisine=$2
  price=$3
  difficulty=$4

  echo "Creating meal ($meal, $cuisine, $price, $difficulty)..."
  response=$(curl -s -X POST "$BASE_URL/create-meal" -H "Content-Type: application/json" \
    -d "{\"meal\":\"$meal\", \"cuisine\":\"$cuisine\", \"price\":$price, \"difficulty\":\"$difficulty\"}")
  echo "$response"  # Print the full response for debugging

  # Check for success status in response
if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal created successfully."
else
    echo "Failed to create meal."
    exit 1
fi

}

delete_meal_by_id() {
  meal_id=$1

  echo "Deleting meal by ID ($meal_id)..."
  response=$(curl -s -X DELETE "$BASE_URL/delete-meal/$meal_id")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal deleted successfully by ID ($meal_id)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Delete meal JSON (ID $meal_id):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to delete meal by ID ($meal_id)."
    echo "Full response for debugging: $response"
    exit 1
  fi
}


get_meal_by_id() {
  meal_id=$1
  expect_fail=${2:-false}

  echo "Getting meal by ID ($meal_id)..."
  response=$(curl -s -X GET "$BASE_URL/get-meal-by-id/$meal_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal retrieved successfully by ID ($meal_id)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Meal JSON (ID $meal_id):"
      echo "$response" | jq .
    fi
  else
    if [ "$expect_fail" = true ]; then
      echo "Expected failure: Meal not found by ID ($meal_id), as it was deleted."
    else
      echo "Failed to retrieve meal by ID ($meal_id)."
      exit 1
    fi
  fi
}

get_meal_by_name() {
  meal_name=$1

  echo "Getting meal by name ($meal_name)..."
  response=$(curl -s -X GET "$BASE_URL/get-meal-by-name/$meal_name")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal retrieved successfully by name ($meal_name)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Meal JSON (Name $meal_name):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to retrieve meal by name ($meal_name)."
    exit 1
  fi
}


############################################################
#
# Battle Management
#
############################################################

prep_combatant() {
  meal=$1

  echo "Preparing combatant ($meal) for battle..."
  response=$(curl -s -X POST "$BASE_URL/prep-combatant" -H "Content-Type: application/json" \
    -d "{\"meal\":\"$meal\"}")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Combatant prepared successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Combatants JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to prepare combatant."
    exit 1
  fi
}


clear_combatants() {
  echo "Clearing combatants..."
  response=$(curl -s -X POST "$BASE_URL/clear-combatants")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Combatants cleared successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Clear combatants JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to clear combatants."
    echo "Full response for debugging: $response"
    exit 1
  fi
}


get_combatants() {
  echo "Getting current list of combatants..."
  response=$(curl -s -X GET "$BASE_URL/get-combatants")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Combatants retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Combatants JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to retrieve combatants."
    exit 1
  fi
}

battle() {
  echo "Starting a battle between combatants..."
  response=$(curl -s -X GET "$BASE_URL/battle")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Battle completed successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Battle JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to complete battle."
    echo "Full response for debugging: $response"
    exit 1
  fi
}



############################################################
#
# Leaderboard
#
############################################################

get_leaderboard() {
  sort_by=$1
  echo "Retrieving leaderboard sorted by $sort_by..."
  response=$(curl -s -X GET "$BASE_URL/leaderboard?sort=$sort_by")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Leaderboard retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Leaderboard JSON (sorted by $sort_by):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to retrieve leaderboard."
    exit 1
  fi
}


############################################################
#
# Run Smoketests
#
############################################################

# Health checks
check_health
check_db

# Create meals
create_meal "Pasta" "Italian" 12.99 "MED"
create_meal "Taco" "Mexican" 9.99 "HIGH"
create_meal "Sushi" "Japanese" 15.50 "LOW"

# Get meals by ID and name
get_meal_by_id 1
get_meal_by_name "Pasta"

# Prepare combatants and start a battle
prep_combatant "Pasta"
prep_combatant "Taco"
get_combatants
battle

# Clear combatants and get leaderboard
clear_combatants
get_leaderboard "wins"

# Delete a meal and verify deletion
delete_meal_by_id 1
get_meal_by_id 1 true  # This should fail since the meal is deleted

echo "All smoketests passed successfully!"