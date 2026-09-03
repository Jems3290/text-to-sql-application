# Conversational Text-to-SQL System

An AI-powered conversational application that allows users to upload any SQLite database and interact with its data using natural-language questions without needing to know SQL or understand the database schema.

The system automatically analyzes the uploaded database, understands its tables, columns, data types, and relationships, detects ambiguous or irrelevant questions, asks schema-aware clarification questions when necessary, generates safe read-only SQL, validates and executes the query, and presents the final answer along with the generated SQL and query results.

The application uses **FastAPI** for the backend, **Flask** for the frontend, **Mistral AI** for LLM-powered reasoning and SQL generation, and **SQLite** as the supported database format.

---

## Features

- Upload arbitrary SQLite databases
- Supports `.db`, `.sqlite`, and `.sqlite3` files
- Automatic database validation
- Dynamic schema extraction
- Table and column discovery
- Foreign-key and relationship analysis
- Schema-aware natural-language question processing
- Question relevance detection
- Ambiguity detection
- AI-generated clarification questions
- Conversational clarification flow
- Natural-language to SQL generation
- SQL syntax validation
- Schema-aware SQL validation
- Read-only SQL security enforcement
- Safe SQL execution
- Automatic SQL error correction
- Natural-language answer generation
- Generated SQL display
- Query result display
- Row-count information
- Query-result truncation handling
- Flask session-based database tracking
- Conversational chat history
- Backend timeout handling
- Invalid database handling
- Expired database-session handling
- Expired clarification handling
- Responsive conversational web interface

---

## How It Works

The complete application workflow is:

```text
User
 │
 ▼
Upload SQLite Database
 │
 ▼
Database Validation
 │
 ▼
Schema Extraction
 │
 ▼
Relationship Analysis
 │
 ▼
Schema Context Generation
 │
 ▼
Ask Natural-Language Question
 │
 ▼
Question Processing
 │
 ├─────────────── Irrelevant ───────────────► Reject Question
 │
 ▼
Ambiguity Detection
 │
 ├─────────────── Ambiguous
 │                       │
 │                       ▼
 │              Generate Clarification
 │                       │
 │                       ▼
 │              User Provides Answer
 │                       │
 └───────────────────────┘
 │
 ▼
Text-to-SQL Generation
 │
 ▼
SQL Validation
 │
 ▼
SQL Security Check
 │
 ▼
SQL Execution
 │
 ├──────────── Error
 │                 │
 │                 ▼
 │        Automatic SQL Correction
 │                 │
 └─────────────────┘
 │
 ▼
Result Processing
 │
 ▼
Natural-Language Response
 │
 ▼
Flask Chat Interface
```

---

# Example

Suppose the uploaded database contains an employee table.

The user can ask:

```text
Give me the names of employees whose salary is greater than 10000.
```

The system can generate:

```sql
SELECT emp_name
FROM tbl_employee
WHERE salary > 10000;
```

The query is validated, checked for security, executed against the uploaded database, and the result is returned to the user.

---

## Schema-Aware Clarification

One of the major features of this project is its clarification engine.

For example, the user may ask:

```text
Show me the best employee of last month.
```

The word **best** is ambiguous.

Instead of blindly generating SQL, the system analyzes the available database schema and asks an appropriate clarification question.

For example:

```text
How should the best employee be determined?

- Highest number of completed projects
- Lowest number of leaves
- Highest sales
```

The available clarification criteria depend on information actually present in the uploaded database.

The user can then answer:

```text
Based on completed projects.
```

The system continues the existing conversation and generates the appropriate SQL.

---

# Application Architecture

The application separates the frontend, API layer, business logic, LLM components, and database-processing components.

```text
                         ┌─────────────────────┐
                         │       Browser       │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Flask Frontend    │
                         │                     │
                         │   HTML / CSS / JS   │
                         │   Jinja Templates   │
                         └──────────┬──────────┘
                                    │
                                    │ HTTP
                                    ▼
                         ┌─────────────────────┐
                         │      FastAPI        │
                         │      Backend        │
                         └──────────┬──────────┘
                                    │
                 ┌──────────────────┼───────────────────┐
                 │                  │                   │
                 ▼                  ▼                   ▼
        Database Services     Question Engine       LLM Layer
                 │                  │                   │
                 ▼                  ▼                   ▼
        Schema Extraction      Relevance          Clarification
        Relationships          Ambiguity           SQL Generation
        SQL Execution                              Response Generation
                 │                  │                   │
                 └──────────────────┼───────────────────┘
                                    │
                                    ▼
                              SQLite Database
```

---

# Technology Stack

## Backend

- Python
- FastAPI
- Uvicorn
- Pydantic
- SQLite3
- SQLGlot

## AI / LLM

- Mistral AI
- Structured LLM outputs
- Prompt engineering
- Schema-aware reasoning

## Frontend

- Flask
- Jinja2
- HTML5
- CSS3
- Vanilla JavaScript

## Testing

- Pytest
- HTTPX

---

# Project Structure

```text
Conversational-Text-to-SQL/
│
├── backend/
│   │
│   ├── main.py
│   │
│   ├── api/
│   │   ├── database_routes.py
│   │   └── chat_routes.py
│   │
│   ├── core/
│   │   └── config.py
│   │
│   ├── database/
│   │   ├── validator.py
│   │   ├── schema_extractor.py
│   │   ├── relationship_analyzer.py
│   │   ├── schema_builder.py
│   │   ├── sql_validator.py
│   │   ├── sql_security.py
│   │   └── query_executor.py
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── llm_client.py
│   │   ├── clarification_generator.py
│   │   ├── prompts.py
│   │   ├── sql_generator.py
│   │   └── response_generator.py
│   │
│   └── services/
│       ├── upload_service.py
│       ├── database_registry.py
│       ├── chat_service.py
│       ├── question_processor.py
│       ├── relevance_detector.py
│       ├── ambiguity_detector.py
│       ├── conversation_manager.py
│       ├── sql_correction_service.py
│       └── result_processor.py
│
├── frontend/
│   │
│   ├── flask_app.py
│   │
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   └── chat.html
│   │
│   └── static/
│       ├── css/
│       │   └── style.css
│       │
│       └── js/
│           └── app.js
│
├── data/
│   └── uploads/
│
├── tests/
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

> The exact frontend `static/` structure may vary depending on the final UI implementation.

---

# API Endpoints

The FastAPI backend exposes three main endpoints used by the Flask frontend.

## Upload Database

```http
POST /database/upload
```

Uploads and validates a SQLite database.

Supported extensions:

```text
.db
.sqlite
.sqlite3
```

Example successful response:

```json
{
    "message": "Database uploaded and validated successfully.",
    "database": {
        "upload_id": "...",
        "original_filename": "database.sqlite",
        "stored_filename": "...",
        "stored_path": "...",
        "database_id": "..."
    }
}
```

---

## Ask Question

```http
POST /chat/query
```

Example request:

```json
{
    "database_id": "database-id",
    "question": "Show me the top 5 customers by total spending."
}
```

Depending on the question, the endpoint can return one of the main processing states:

```text
completed
clarification_required
irrelevant
```

---

## Submit Clarification

```http
POST /chat/clarify
```

Example request:

```json
{
    "conversation_id": "conversation-id",
    "answer": "Based on total spending."
}
```

The backend uses the stored conversational context to continue processing the original question.

---

# Installation

## 1. Clone the Repository

```bash
git clone <your-repository-url>
```

Move into the project:

```bash
cd Conversational-Text-to-SQL
```

---

## 2. Create Virtual Environment

Python 3.12 is recommended.

### Windows

```powershell
py -3.12 -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

If you are using Command Prompt:

```cmd
.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Environment Variables

Create a `.env` file in the project root.

Example:

```env
MISTRAL_API_KEY=your_mistral_api_key
FLASK_SECRET_KEY=your_long_random_secret_key
```

Add any additional environment variables required by your current configuration.

Never commit `.env` to GitHub.

---

# Running the Application

The application consists of two servers:

```text
FastAPI Backend  → Port 8000
Flask Frontend   → Port 5000
```

Both need to be running.

---

## Start FastAPI

From the project root:

```bash
uvicorn backend.main:app --reload
```

FastAPI will normally be available at:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

---

## Start Flask

Open another terminal, activate the same virtual environment, and run:

```bash
python frontend/flask_app.py
```

The frontend will normally be available at:

```text
http://127.0.0.1:5000
```

Open that address in your browser.

---

# Using the Application

1. Open the Flask frontend.
2. Upload a `.db`, `.sqlite`, or `.sqlite3` database.
3. Wait for database validation.
4. After a successful upload, enter the conversational chat.
5. Ask a question about the database in natural language.
6. If the question is clear, the system generates and executes SQL.
7. If the question is ambiguous, answer the clarification question.
8. View the natural-language response.
9. Inspect the generated SQL when needed.
10. View the returned database records and row count.

Example:

```text
User:
Which five customers spent the most money?

Assistant:
The following customers have the highest total spending...

Generated SQL:
SELECT ...

Query Results:
...
```

---

# Security

Security is an important part of this project because an LLM-generated SQL query should never automatically be trusted.

The application uses multiple layers of protection.

## Read-Only SQL

The application is designed to allow read-only database operations.

Potentially destructive operations such as the following should be rejected:

```sql
INSERT
UPDATE
DELETE
DROP
ALTER
CREATE
REPLACE
TRUNCATE
```

The goal is to allow queries such as:

```sql
SELECT
```

without allowing the AI to modify the uploaded database.

---

## SQL Validation

Generated SQL is validated before execution.

Validation can include:

- SQL syntax validation
- table validation
- column validation
- schema consistency checks
- forbidden operation detection

---

## Uploaded Database Isolation

Uploaded databases are assigned server-generated identifiers.

The frontend works with a `database_id` rather than allowing the browser to freely provide arbitrary filesystem paths.

---

## Environment Secrets

Sensitive configuration such as API keys and Flask's secret key is stored using environment variables.

The `.env` file should remain excluded through `.gitignore`.

---

# Error Handling

The frontend handles common failures without exposing raw application exceptions to the user.

Examples include:

- FastAPI unavailable
- backend connection failure
- request timeout
- invalid backend response
- invalid database
- expired database ID
- expired clarification conversation
- malformed API response

For example, if FastAPI restarts and its in-memory database registry is cleared, Flask can detect the stale database state and ask the user to upload the database again.

---

# Current Development Limitations

Some application state is currently maintained in memory.

This can include:

- database registry
- clarification conversations
- frontend chat/result state

Therefore, restarting the FastAPI or Flask development servers may clear some active state.

For example:

```text
Upload database
      ↓
FastAPI assigns database_id
      ↓
Restart FastAPI
      ↓
old database_id may no longer exist
```

The user may then need to upload the database again.

For production deployment, persistent state management such as Redis or a database could be introduced.

---

# Testing

Run the test suite using:

```bash
pytest
```

Or:

```bash
pytest tests/
```

Important application scenarios to test include:

```text
Valid database upload
Invalid database upload
Unsupported file extension
Clear database question
Irrelevant question
Ambiguous question
Clarification response
Valid SQL generation
Invalid SQL rejection
Unsafe SQL rejection
SQL execution
SQL automatic correction
Empty query results
Large query results
Backend connection failure
Request timeout
Expired database state
Expired clarification state
Database reset
Database replacement
```

---

# Development Phases

The project was developed incrementally across the following major phases:

```text
1. Project Setup & Virtual Environment
2. Project Directory Structure
3. Environment Variables & API Configuration
4. FastAPI Backend Foundation
5. SQLite Database Upload System
6. Uploaded Database Validation & Security Checks
7. SQLite Schema Extraction
8. Database Relationship & Foreign-Key Analysis
9. Schema Representation & Schema Context Builder
10. User Question Processing
11. Schema-Aware Question Relevance Detection
12. Ambiguity Detection Engine
13. Schema-Aware Clarification Question Generation
14. Conversational Clarification & Context Management
15. Text-to-SQL Prompt Engineering
16. SQL Query Generation
17. SQL Syntax & Schema Validation
18. SQL Security & Read-Only Query Enforcement
19. SQL Query Execution Engine
20. SQL Error Handling & Automatic Query Correction
21. Query Result Processing & Natural-Language Response Generation
22. Chat & Database API Integration
23. Initial User Interface
24. Complete Application Testing & Validation
25. Flask Frontend Setup
26. Database Upload Interface
27. Flask Session & Database State Management
28. Conversational Chat Interface
29. Clarification Conversation Integration
30. SQL & Query Result Display
31. Flask Error Handling & User Feedback
32. Final Flask Frontend Cleanup
```

---

# Why This Project Is Different

A basic Text-to-SQL application usually follows:

```text
Question
   ↓
LLM
   ↓
SQL
```

This project adds several layers around that process:

```text
Question
   ↓
Schema Understanding
   ↓
Relevance Detection
   ↓
Ambiguity Detection
   ↓
Clarification
   ↓
SQL Generation
   ↓
SQL Validation
   ↓
Security Enforcement
   ↓
Execution
   ↓
Automatic Error Correction
   ↓
Result Processing
   ↓
Natural-Language Response
```

This makes the project more than a simple LLM-to-SQL demonstration. It focuses on building a safer and more conversational database interaction system.

---

# Future Improvements

Possible future improvements include:

- PostgreSQL support
- MySQL support
- SQL Server support
- persistent conversation storage
- Redis-backed sessions
- persistent database registry
- multi-user authentication
- database connection-string support
- query history
- saved conversations
- schema visualization
- SQL query explanation
- query execution statistics
- token usage monitoring
- LLM cost tracking
- database access permissions
- Docker support
- production deployment
- asynchronous/background query execution
- streaming AI responses

---

# Example Use Cases

The system can be used with SQLite databases containing information such as:

- employees
- customers
- orders
- e-commerce transactions
- inventory
- products
- sales
- students
- courses
- financial records
- analytics data
- application data

Because the schema is extracted dynamically, the application is not designed around one fixed database structure.

---

# Project Objective

The main objective of this project is to allow users to interact with structured database information using natural language while maintaining SQL correctness, schema awareness, security, and conversational context.

Instead of requiring users to know:

```sql
SELECT customer_name, SUM(order_total)
FROM customers
JOIN orders
ON customers.id = orders.customer_id
GROUP BY customer_name
ORDER BY SUM(order_total) DESC
LIMIT 5;
```

the user should simply be able to ask:

```text
Who are the top 5 customers by total spending?
```

The system handles the database understanding and SQL generation automatically.

---

# License

This project is intended for educational, portfolio, and development purposes.

Add an appropriate open-source license such as MIT if you plan to publicly distribute or allow reuse of the project.

---

# Author

**Jems Goyani**

B.Sc. IT Student  
AI/ML Developer

---

## Final Note

This project demonstrates practical integration of:

**Generative AI + LLMs + Prompt Engineering + SQL + Database Engineering + FastAPI + Flask + API Design + Validation + Security + Conversational AI**

with the goal of creating a dynamic and schema-aware conversational interface for SQLite databases.
