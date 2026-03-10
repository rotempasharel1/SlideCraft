# EduBuilder

EduBuilder is an Educational AI Platform built with FastAPI (backend) and Streamlit (frontend), powered by Supabase and Gemini API.

## Quickstart on Windows

Follow these steps to get the project running locally on a Windows machine.

### Prerequisites

1.  **Python 3.8+** installed on your system.
2.  **Git** installed.
3.  A **Supabase** project with your database credentials.
4.  A **Google Gemini API** key.

### 1. Clone the Repository

```powershell
git clone <your-repo-url>
cd EduBuilder
```

### 2. Set Up a Virtual Environment

It is recommended to use a virtual environment to manage dependencies:

```powershell
python -m venv venv
.\venv\Scripts\activate
```
*(You should see `(venv)` appear at the start of your terminal prompt)*

### 3. Install Dependencies

With your virtual environment activated, install the required packages:

```powershell
pip install -r requirements.txt
```

### 4. Configure Environment Variables

1. Copy the example environment file to create a new `.env` file:
   ```powershell
   copy .env.example .env
   ```
2. Open the `.env` file in your editor and fill in your Supabase credentials and Gemini API key:
   ```env
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_KEY=your_supabase_anon_key
   GEMINI_API_KEY=your_gemini_api_key
   ```
*(Optional: include initial admin credentials if your `.env` requires it).*

### 5. Run the Application

You will need **two separate terminal windows** (both originating from the project directory with the virtual environment activated) to run the backend and frontend simultaneously.

#### Terminal 1: Start the FastAPI Backend

```powershell
# Ensure your virtual environment is activated
.\venv\Scripts\activate

# Start the Uvicorn dev server
uvicorn backend.main:app --reload
```
The backend API and its interactive Swagger documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

#### Terminal 2: Start the Streamlit Frontend

```powershell
# Open a new terminal in the EduBuilder folder
# Activate the virtual environment
.\venv\Scripts\activate

# Start the Streamlit app
streamlit run frontend\app.py
```
A new tab will automatically open in your default browser for the Streamlit application, typically at [http://localhost:8501](http://localhost:8501).