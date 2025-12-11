# Nutrition Facts Vision API

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Firebase](https://img.shields.io/badge/firebase-ffca28?style=for-the-badge&logo=firebase&logoColor=black)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)

A powerful backend API for intelligent nutrition facts recognition and personalized health analysis. This FastAPI-based service processes food label images through OCR, analyzes nutritional content, and provides AI-driven risk assessments tailored to individual health profiles.

---

## Project Overview

**Nutrition Facts Vision** is an innovative solution that helps users make informed dietary decisions by analyzing packaged food labels through their mobile devices. The system combines computer vision, natural language processing, and personalized health profiling to deliver actionable nutritional insights.

### Key Features

- **OCR-Powered Label Recognition** - Extracts text from food label images using Google ML Kit
- **AI-Driven Analysis** - Uses LLM (Large Language Models) to correct OCR errors and structure data
- **Personalized Risk Assessment** - Evaluates ingredients against user's allergies, health conditions, and dietary preferences
- **Intelligent Chatbot** - Context-aware Q&A about ingredients and nutritional concerns
- **Comprehensive Nutrient Tracking** - Stores and analyzes nutritional values over time
- **Secure Authentication** - Firebase-based user authentication and authorization

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Mobile App (Flutter)                     │
│              Camera + ML Kit OCR Integration                │
└────────────────────────┬────────────────────────────────────┘
                         │ Raw OCR Text
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (This Repository)              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Authentication Service (Firebase)                   │   │
│  │  Health Profile Management                           │   │
│  │  Scan Analysis & Processing                          │   │
│  │  Chatbot Service                                     │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
    ┌────────┐   ┌──────────────┐   ┌──────────┐
    │ LLM    │   │ PostgreSQL   │   │ Firebase │
    │Service │   │ Database     │   │ Auth     │
    └────────┘   └──────────────┘   └──────────┘
```

### Data Processing Pipeline

1. **OCR Extraction** - Mobile app captures food label image and extracts raw text using ML Kit
2. **Text Correction & Parsing** - LLM corrects OCR errors and structures data into ingredients and nutrients
3. **Risk Assessment** - System evaluates each ingredient against user's health profile
4. **Summary Generation** - LLM creates personalized, actionable insights
5. **Storage & Retrieval** - Results stored in PostgreSQL for history and analytics

---

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Docker & Docker Compose (optional)
- Firebase Admin SDK credentials
- OpenAI API key (for LLM services)

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/ZiyaKolcu/nutrition-facts-vision-api.git
cd nutrition-facts-vision-api
```

#### 2. Set Up Environment Variables

Create a `.env` file in the project root:

```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/nutrition_facts_db
POSTGRES_USER=nutrition_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=nutrition_facts_db
POSTGRES_PORT=5432

# Firebase Configuration
FIREBASE_CREDENTIAL_PATH=./firebase-adminsdk.json

# LLM Configuration
OPENAI_API_KEY=your_openai_api_key_here

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

#### 3. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 4. Set Up Database

```bash
# Run Alembic migrations
alembic upgrade head
```

#### 5. Add Firebase Credentials

Place your Firebase Admin SDK JSON file at:

```
./secrets/firebase-adminsdk.json
```

#### 6. Run the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Docker Deployment

```bash
docker-compose up -d
```

This will:

- Build and start the FastAPI application
- Start a PostgreSQL database
- Run database migrations automatically
- Expose the API on port 8000

---

## API Documentation

### Authentication Endpoints

#### Authenticate User

```http
POST /api/v1/auth/authenticate
Content-Type: application/json

{
  "id_token": "firebase_id_token_here"
}
```

**Response:**

```json
{
  "user": {
    "id": "uuid",
    "firebase_uid": "firebase_uid",
    "email": "user@example.com",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "message": "Authentication successful"
}
```

#### Get Current User

```http
GET /api/v1/auth/me?id_token=firebase_id_token_here
```

---

### Health Profile Endpoints

#### Get My Health Profile

```http
GET /api/v1/health-profile/me?id_token=firebase_id_token_here
```

**Response:**

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "allergies": ["peanuts", "shellfish"],
  "chronic_conditions": ["diabetes", "hypertension"],
  "dietary_preferences": ["vegetarian"],
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### Update Health Profile

```http
PUT /api/v1/health-profile/me?id_token=firebase_id_token_here
Content-Type: application/json

{
  "allergies": ["peanuts", "shellfish"],
  "chronic_conditions": ["diabetes"],
  "dietary_preferences": ["vegetarian"]
}
```

---

### Scan Analysis Endpoints

#### Analyze Food Label

```http
POST /api/v1/scans/analyze?id_token=firebase_id_token_here
Content-Type: application/json

{
  "raw_text": "INGREDIENTS: Wheat flour, sugar, salt...",
  "title": "Whole Wheat Crackers",
  "language": "en"
}
```

**Response:**

```json
{
  "scan": {
    "id": "uuid",
    "user_id": "uuid",
    "product_name": "Whole Wheat Crackers",
    "summary_explanation": "This product contains gluten which is incompatible with your celiac disease diagnosis...",
    "summary_risk": "High",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

#### Get All User Scans

```http
GET /api/v1/scans/me?id_token=firebase_id_token_here
```

**Response:**

```json
[
  {
    "id": "uuid",
    "product_name": "Whole Wheat Crackers",
    "created_at": "2024-01-01T00:00:00Z"
  },
  {
    "id": "uuid",
    "product_name": "Yogurt",
    "created_at": "2024-01-02T00:00:00Z"
  }
]
```

#### Get Scan Details

```http
GET /api/v1/scans/{scan_id}?id_token=firebase_id_token_here
```

**Response:**

```json
{
  "id": "uuid",
  "product_name": "Whole Wheat Crackers",
  "summary_explanation": "Detailed analysis...",
  "ingredients": [
    {
      "name": "Wheat flour",
      "risk_level": "High"
    },
    {
      "name": "Sugar",
      "risk_level": "Low"
    }
  ],
  "nutrients": [
    {
      "label": "Calories",
      "value": 140.0
    },
    {
      "label": "Protein",
      "value": 3.0
    }
  ]
}
```

#### Delete Scan

```http
DELETE /api/v1/scans/{scan_id}?id_token=firebase_id_token_here
```

---

### Chat Endpoints

#### Send Chat Message

```http
POST /api/v1/chat/message?id_token=firebase_id_token_here
Content-Type: application/json

{
  "message": "What is soya lecithin?",
  "scan_id": "uuid" (optional)
}
```

**Response:**

```json
{
  "response": "Soya lecithin is an emulsifier derived from soybean...",
  "confidence": "high"
}
```

---

## Project Structure

```
nutrition-facts-vision-api/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── auth.py              # Authentication endpoints
│   │   │   ├── health_profile.py    # Health profile management
│   │   │   ├── scan.py              # Scan analysis endpoints
│   │   │   └── chat.py              # Chatbot endpoints
│   │   ├── dependencies.py          # Dependency injection
│   │   └── __init__.py
│   ├── models/
│   │   ├── user.py                  # User model
│   │   ├── health_profile.py        # Health profile model
│   │   ├── scan.py                  # Scan model
│   │   ├── ingredient.py            # Ingredient model
│   │   ├── nutrient.py              # Nutrient model
│   │   └── chat_with_ai.py          # Chat history model
│   ├── schemas/
│   │   ├── user.py                  # User schemas
│   │   ├── health_profile.py        # Health profile schemas
│   │   ├── scan.py                  # Scan schemas
│   │   └── chat_with_ai.py          # Chat schemas
│   ├── services/
│   │   ├── auth/                    # Authentication service
│   │   ├── health_profile/          # Health profile service
│   │   ├── nutrition/               # Nutrition analysis service
│   │   │   ├── label_parser.py      # OCR text parsing
│   │   │   ├── nutrition_analyzer.py # LLM-based analysis
│   │   │   └── health_risk_assessor.py # Risk assessment
│   │   └── chat/                    # Chatbot service
│   ├── db/
│   │   ├── base.py                  # Database base
│   │   └── session.py               # Database session
│   └── main.py                      # FastAPI application
├── alembic/                         # Database migrations
├── Dockerfile                       # Docker image configuration
├── docker-compose.yml               # Docker Compose configuration
├── requirements.txt                 # Python dependencies
├── alembic.ini                      # Alembic configuration
└── README.md                        # This file
```

---

## Configuration

### Environment Variables

| Variable                   | Description                     | Required |
| -------------------------- | ------------------------------- | -------- |
| `DATABASE_URL`             | PostgreSQL connection string    | ✅       |
| `FIREBASE_CREDENTIAL_PATH` | Path to Firebase Admin SDK JSON | ✅       |
| `OPENAI_API_KEY`           | OpenAI API key for LLM services | ✅       |
| `POSTGRES_USER`            | PostgreSQL username             | ✅       |
| `POSTGRES_PASSWORD`        | PostgreSQL password             | ✅       |
| `POSTGRES_DB`              | PostgreSQL database name        | ✅       |
| `POSTGRES_PORT`            | PostgreSQL port                 | ✅       |

### Database Migrations

Create a new migration:

```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:

```bash
alembic upgrade head
```

Rollback migrations:

```bash
alembic downgrade -1
```

---

## Security Considerations

- **Firebase Authentication:** All endpoints require valid Firebase ID tokens
- **Database:** Use strong PostgreSQL passwords and enable SSL connections in production
- **API Keys:** Store sensitive credentials in environment variables, never commit to version control
- **CORS:** Currently allows all origins; configure for production use
- **Input Validation:** All endpoints validate request data using Pydantic schemas

### Production Recommendations

1. **CORS Configuration:** Restrict to specific frontend domains
2. **Rate Limiting:** Implement rate limiting for API endpoints
3. **HTTPS:** Always use HTTPS in production
4. **Database Backups:** Set up automated PostgreSQL backups
5. **Monitoring:** Implement logging and monitoring for production deployments
6. **API Keys:** Rotate OpenAI and Firebase credentials regularly

---

## Data Models

### User

- `id` (UUID): Primary key
- `firebase_uid` (String): Firebase user identifier
- `email` (String): User email address
- `created_at` (DateTime): Account creation timestamp

### Health Profile

- `id` (UUID): Primary key
- `user_id` (UUID): Foreign key to User
- `allergies` (Array): List of food allergies
- `chronic_conditions` (Array): List of chronic health conditions
- `dietary_preferences` (Array): Dietary restrictions/preferences
- `updated_at` (DateTime): Last update timestamp

### Scan

- `id` (UUID): Primary key
- `user_id` (UUID): Foreign key to User
- `product_name` (String): Name of scanned product
- `raw_text` (Text): Raw OCR output
- `parsed_ingredients` (Array): Structured ingredient list
- `summary_explanation` (Text): AI-generated analysis summary
- `summary_risk` (String): Overall risk level (Low/Medium/High)
- `created_at` (DateTime): Scan creation timestamp

### Ingredient

- `id` (UUID): Primary key
- `scan_id` (UUID): Foreign key to Scan
- `name` (String): Ingredient name
- `risk_level` (String): Risk assessment (Low/Medium/High)

### Nutrient

- `id` (UUID): Primary key
- `scan_id` (UUID): Foreign key to Scan
- `label` (String): Nutrient name (e.g., "Calories", "Protein")
- `value` (Float): Nutrient value
- `max_value` (Float, optional): Maximum recommended value

---

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- Follow PEP 8 guidelines
- Use type hints for all functions
- Write docstrings for all modules and functions
- Keep functions focused and modular

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Acknowledgments

- **Google ML Kit** - For on-device OCR capabilities
- **OpenAI** - For LLM-powered analysis and insights
- **Firebase** - For authentication infrastructure
- **FastAPI** - For the modern Python web framework
- **SQLAlchemy** - For database ORM

## Version History

### v1.0.0 (Current)

- Initial release
- Core OCR and analysis functionality
- User authentication and health profiles
- Chatbot integration
- Scan history management

---

**Last Updated:** December 2025
