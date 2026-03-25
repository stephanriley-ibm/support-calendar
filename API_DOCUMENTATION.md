# Calendar Application - API Documentation

## Base URL
```
http://localhost:8000/api
```

## Authentication
All endpoints (except login) require authentication using Token Authentication.

Include the token in the Authorization header:
```
Authorization: Token <your-token-here>
```

---

## Authentication Endpoints

### Login
```http
POST /api/auth/users/login/
```

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "token": "string",
  "user": {
    "id": 1,
    "username": "string",
    "email": "string",
    "first_name": "string",
    "last_name": "string",
    "full_name": "string",
    "role": "engineer|coach|admin",
    "team": 1,
    "team_name": "string"
  }
}
```

### Logout
```http
POST /api/auth/users/logout/
```

### Get Current User
```http
GET /api/auth/users/me/
```

---

## User Management

### List Users
```http
GET /api/auth/users/
```
**Permissions:** Coach or Admin

**Query Parameters:**
- None

### Get User Details
```http
GET /api/auth/users/{id}/
```

### Create User
```http
POST /api/auth/users/
```
**Permissions:** Admin only

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "password_confirm": "string",
  "first_name": "string",
  "last_name": "string",
  "role": "engineer|coach|admin",
  "team": 1
}
```

---

## Team Management

### List Teams
```http
GET /api/auth/teams/
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "string",
    "coach": 1,
    "coach_name": "string",
    "max_concurrent_off": 2,
    "member_count": 5,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

### Get Team Details
```http
GET /api/auth/teams/{id}/
```

### Get Team Members
```http
GET /api/auth/teams/{id}/members/
```

### Get Team Availability
```http
GET /api/auth/teams/{id}/availability/?start_date=2024-01-01&end_date=2024-01-31
```

**Response:**
```json
{
  "2024-01-01": {
    "date": "2024-01-01",
    "total_members": 5,
    "off_count": 2,
    "timeoff_count": 1,
    "dil_count": 1,
    "available": 3,
    "at_limit": true,
    "over_limit": false
  }
}
```

---

## Time-Off Management

### List Time-Off Requests
```http
GET /api/timeoff/requests/
```

**Query Parameters:**
- `status`: pending|approved|rejected|cancelled
- `start_date`: YYYY-MM-DD
- `end_date`: YYYY-MM-DD
- `team`: team_id (coach/admin only)

### Create Time-Off Request
```http
POST /api/timeoff/requests/
```

**Request Body:**
```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-01-05",
  "reason": "string"
}
```

### Get My Requests
```http
GET /api/timeoff/requests/my_requests/
```

### Get Pending Requests (Coach)
```http
GET /api/timeoff/requests/pending/
```
**Permissions:** Coach or Admin

### Approve Request
```http
POST /api/timeoff/requests/{id}/approve/
```
**Permissions:** Coach (for team members) or Admin

### Reject Request
```http
POST /api/timeoff/requests/{id}/reject/
```
**Permissions:** Coach (for team members) or Admin

**Request Body:**
```json
{
  "action": "reject",
  "rejection_reason": "string"
}
```

### Check Conflicts
```http
POST /api/timeoff/requests/check_conflicts/
```

**Request Body:**
```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-01-05",
  "exclude_request_id": 123
}
```

**Response:**
```json
{
  "has_conflict": true,
  "message": "Conflict detected: 2 day(s) exceed team limit",
  "conflict_dates": ["2024-01-01", "2024-01-02"],
  "conflicts": {
    "2024-01-01": {
      "date": "2024-01-01",
      "requests": [
        {
          "id": 1,
          "user": "John Doe",
          "user_id": 1
        }
      ],
      "days_in_lieu": []
    }
  }
}
```

### Get Upcoming Time-Off
```http
GET /api/timeoff/requests/upcoming/?days=90&team=1
```

---

## On-Call Management

### List Holidays
```http
GET /api/oncall/holidays/
```

**Query Parameters:**
- `start_date`: YYYY-MM-DD
- `end_date`: YYYY-MM-DD
- `requires_coverage`: true|false

### Create Holiday
```http
POST /api/oncall/holidays/
```
**Permissions:** Coach or Admin

**Request Body:**
```json
{
  "name": "Christmas Day",
  "date": "2024-12-25",
  "description": "string",
  "requires_coverage": true
}
```

### Get Upcoming Holidays
```http
GET /api/oncall/holidays/upcoming/?days=90
```

---

## On-Call Shifts

### List Shifts
```http
GET /api/oncall/shifts/
```

**Query Parameters:**
- `start_date`: YYYY-MM-DD
- `end_date`: YYYY-MM-DD
- `engineer`: user_id
- `shift_type`: early_primary|late_primary|secondary|holiday
- `is_holiday`: true|false

### Create Shift
```http
POST /api/oncall/shifts/
```
**Permissions:** Coach or Admin

**Request Body:**
```json
{
  "shift_date": "2024-01-06",
  "shift_type": "early_primary",
  "engineer": 1,
  "holiday": null,
  "start_time": "08:00:00",
  "end_time": "16:00:00",
  "notes": "string"
}
```

### Generate Rotation
```http
POST /api/oncall/shifts/generate_rotation/
```
**Permissions:** Coach or Admin

**Request Body:**
```json
{
  "start_date": "2024-01-06",
  "end_date": "2024-03-31",
  "team_id": 1
}
```

**Response:**
```json
{
  "success": true,
  "shifts_created": 15,
  "errors": [],
  "shifts": [...]
}
```

### Get My Shifts
```http
GET /api/oncall/shifts/my_shifts/
```

### Get Schedule View
```http
GET /api/oncall/shifts/schedule/?start_date=2024-01-01&end_date=2024-01-31
```

**Response:**
```json
[
  {
    "date": "2024-01-06",
    "day_of_week": "Saturday",
    "shifts": [
      {
        "id": 1,
        "shift_type": "early_primary",
        "shift_type_display": "Early Primary",
        "engineer": {
          "id": 1,
          "name": "John Doe"
        },
        "holiday": null,
        "start_time": null,
        "end_time": null
      }
    ]
  }
]
```

---

## Days-in-Lieu Management

### List Days-in-Lieu
```http
GET /api/oncall/days-in-lieu/
```

**Query Parameters:**
- `user`: user_id
- `status`: scheduled|used|expired|cancelled
- `start_date`: YYYY-MM-DD
- `end_date`: YYYY-MM-DD

### Create Manual Day-in-Lieu
```http
POST /api/oncall/days-in-lieu/
```
**Permissions:** Coach or Admin

**Request Body:**
```json
{
  "user": 1,
  "scheduled_date": "2024-01-10",
  "notes": "string"
}
```

### Reschedule Day-in-Lieu
```http
POST /api/oncall/days-in-lieu/{id}/reschedule/
```
**Permissions:** Coach (for team members) or Admin

**Request Body:**
```json
{
  "new_date": "2024-01-15",
  "reason": "Team coverage needs"
}
```

### Mark as Used
```http
POST /api/oncall/days-in-lieu/{id}/mark_used/
```

### Get My Days-in-Lieu
```http
GET /api/oncall/days-in-lieu/my_days/
```

### Get Balance
```http
GET /api/oncall/days-in-lieu/balance/?user=1
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "name": "John Doe"
  },
  "scheduled": 3,
  "used": 5,
  "expired": 1,
  "total": 9
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Error message",
  "field_name": ["Validation error"]
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

---

## Permissions Summary

| Role | Permissions |
|------|-------------|
| **Engineer** | - View own data<br>- Submit time-off requests<br>- View own shifts and days-in-lieu<br>- Mark own days-in-lieu as used |
| **Coach** | - All Engineer permissions<br>- View team data<br>- Approve/reject team time-off requests<br>- Create holidays and shifts<br>- Generate rotations<br>- Reschedule team days-in-lieu<br>- Create manual days-in-lieu |
| **Admin** | - All Coach permissions<br>- View all data<br>- Manage users and teams<br>- Full system access |

---

## Workflow Examples

### 1. Engineer Submits Time-Off Request

```bash
# 1. Check for conflicts
POST /api/timeoff/requests/check_conflicts/
{
  "start_date": "2024-02-01",
  "end_date": "2024-02-05"
}

# 2. If no conflicts, submit request
POST /api/timeoff/requests/
{
  "start_date": "2024-02-01",
  "end_date": "2024-02-05",
  "reason": "Vacation"
}
```

### 2. Coach Approves Request

```bash
# 1. Get pending requests
GET /api/timeoff/requests/pending/

# 2. Approve specific request
POST /api/timeoff/requests/123/approve/
```

### 3. Generate Weekend Rotation

```bash
# Generate rotation for Q1 2024
POST /api/oncall/shifts/generate_rotation/
{
  "start_date": "2024-01-06",
  "end_date": "2024-03-31",
  "team_id": 1
}
```

### 4. Coach Reschedules Day-in-Lieu

```bash
# Reschedule due to team coverage needs
POST /api/oncall/days-in-lieu/456/reschedule/
{
  "new_date": "2024-02-15",
  "reason": "Team has multiple people out on original date"
}
```

---

## Testing the API

### Using cURL

```bash
# Login
curl -X POST http://localhost:8000/api/auth/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Use token for authenticated requests
curl -X GET http://localhost:8000/api/auth/users/me/ \
  -H "Authorization: Token <your-token>"
```

### Using Python

```python
import requests

# Login
response = requests.post(
    'http://localhost:8000/api/auth/users/login/',
    json={'username': 'admin', 'password': 'password'}
)
token = response.json()['token']

# Make authenticated request
headers = {'Authorization': f'Token {token}'}
response = requests.get(
    'http://localhost:8000/api/timeoff/requests/',
    headers=headers
)
```

---

## Notes

- All dates should be in ISO 8601 format (YYYY-MM-DD)
- All timestamps are in UTC
- Pagination is enabled for list endpoints (50 items per page)
- Use query parameters for filtering and searching