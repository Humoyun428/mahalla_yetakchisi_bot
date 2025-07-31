import json

def is_user_allowed(phone_number):
    with open("data/users.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return phone_number in data.get("allowed_users", [])