# 🧠 String Analyzer Service

## 🚀 Overview

This project implements a **RESTful API** service that analyzes strings
and stores their computed properties.

------------------------------------------------------------------------

## 🧩 Features

For each analyzed string, the service computes and stores the following
properties:

  -----------------------------------------------------------------------
  Property                        Description
  ------------------------------- ---------------------------------------
  `length`                        Number of characters in the string

  `is_palindrome`                 Whether the string reads the same
                                  forwards and backwards
                                  (case-insensitive)

  `unique_characters`             Count of distinct characters in the
                                  string

  `word_count`                    Number of words separated by whitespace

  `sha256_hash`                   Unique SHA-256 hash of the string

  `character_frequency_map`       Mapping of each character to its
                                  frequency
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 🧠 API Endpoints

### 1. Create / Analyze String

**POST** `/strings`

**Request Body**

``` json
{
  "value": "string to analyze"
}
```

**Success Response (201 Created)**

``` json
{
  "id": "sha256_hash_value",
  "value": "string to analyze",
  "properties": {
    "length": 17,
    "is_palindrome": false,
    "unique_characters": 12,
    "word_count": 3,
    "sha256_hash": "abc123...",
    "character_frequency_map": { "s": 2, "t": 3, "r": 2 }
  },
  "created_at": "2025-08-27T10:00:00Z"
}
```

------------------------------------------------------------------------

### 2. Get Specific String

**GET** `/strings/{string_value}`

**Success Response (200 OK)**

``` json
{
  "id": "sha256_hash_value",
  "value": "requested string",
  "properties": { /* same as above */ },
  "created_at": "2025-08-27T10:00:00Z"
}
```

------------------------------------------------------------------------

### 3. Get All Strings with Filtering

**GET**
`/strings?is_palindrome=true&min_length=5&max_length=20&word_count=2&contains_character=a`

**Success Response (200 OK)**

``` json
{
  "data": [
    { "id": "hash1", "value": "string1", "properties": { /* ... */ }, "created_at": "..." }
  ],
  "count": 15,
  "filters_applied": {
    "is_palindrome": true,
    "min_length": 5,
    "max_length": 20,
    "word_count": 2,
    "contains_character": "a"
  }
}
```

------------------------------------------------------------------------

### 4. Natural Language Filtering

**GET**
`/strings/filter-by-natural-language?query=all%20single%20word%20palindromic%20strings`

**Example Queries** \| Query \| Parsed Filters \|
\|--------\|----------------\| \| "all single word palindromic strings"
\| `word_count=1`, `is_palindrome=true` \| \| "strings longer than 10
characters" \| `min_length=11` \| \| "strings containing the letter z"
\| `contains_character=z` \|

**Success Response (200 OK)**

``` json
{
  "data": [ /* ... */ ],
  "count": 3,
  "interpreted_query": {
    "original": "all single word palindromic strings",
    "parsed_filters": { "word_count": 1, "is_palindrome": true }
  }
}
```

------------------------------------------------------------------------

### 5. Delete String

**DELETE** `/strings/{string_value}`

**Success Response (204 No Content)** --- Empty body.

------------------------------------------------------------------------

## ⚙️ Setup Instructions

### 1️⃣ Clone Repository

``` bash
git clone https://github.com/<your-username>/string-analyzer-service.git
cd string-analyzer-service
```

### 2️⃣ Create Virtual Environment

``` bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 3️⃣ Install Dependencies

``` bash
pip install -r requirements.txt
```

### 4️⃣ Run Locally

``` bash
uvicorn main:app --reload
```

API will be available at:\
👉 `http://127.0.0.1:8000`

------------------------------------------------------------------------

## 🧪 Testing

Use **Postman**, **cURL**, or **HTTPie** to test endpoints.

Example:

``` bash
curl -X POST http://localhost:8000/strings -H "Content-Type: application/json" -d '{"value": "racecar"}'
```

------------------------------------------------------------------------


## 🧑‍💻 Stack

-   **Language:** Python 🐍
-   **Framework:** FastAPI ⚡
-   **Database:** SQLite
-   **Hosting:** Railway.app

------------------------------------------------------------------------

## ✨ Author

**Full Name:** Kenechi Nzewi\
**Email:** caseynzewi@example.com\
