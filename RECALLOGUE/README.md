# Recallogue

Recallogue is an application that provides RAG (Retrieval Augmented Generation) capabilities for document processing and conversation management.

## Requirements

- Python 3.9 or higher
- pip

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd recallogue
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```

3. Activate the virtual environment:
   - On Windows:
     ```bash
     .venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```

4. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Environment Variables

Copy the `.env.example` file to `.env` and update the values as needed:

```bash
cp .env.example .env
```

## Running the Application

To run the application in development mode:

```bash
(.venv) PS D:\Duty\RECALLOGUE> python -m uvicorn app.src.main:app
```

The application will start and be available at `http://127.0.0.1:8000` (or as configured).

## Running Tests

To run all tests:

```bash
python -m pytest
```

To run tests with verbose output:

```bash
python -m pytest -v
```

## Project Structure

```
recallogue/
├── app/
│   ├── __init__.py
│   └── src/
│       ├── main.py          # Main application entry point
│       ├── services/        # Application services
│       ├── schema/          # Data schemas
│       └── repositories/    # Data repositories
├── app/tests/              # Test files
├── requirements.txt        # Python dependencies
├── .env.example            # Example environment variables
├── .gitignore
└── README.md
```

## Configuration

The application can be configured using environment variables. See `.env.example` for required variables.

## Development

When developing, make sure to activate the virtual environment:

```bash
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux
```

To update dependencies:

```bash
pip install -r requirements.txt
```

## License

[Add your license information here]