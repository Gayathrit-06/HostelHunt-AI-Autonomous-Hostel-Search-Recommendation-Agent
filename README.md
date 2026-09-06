# HostelHunt AI: Autonomous Hostel Search & Recommendation Agent

HostelHunt AI is an intelligent, autonomous agent designed to streamline the search for student accommodation and PG options. Built using **LangGraph** and **LangChain**, the agent dynamically processes natural language queries to extract locations, fetch place details, compute distances, and fall back to web search whenever necessary.

---

## 🔑 Key Features

* **Dynamic Location Extraction:** Uses NLP regex pattern matching to resolve any location, area, or landmark globally without static hardcoding.
* **Dual-Search Pipeline:** Primary search via Google Places API with an automated fallback to Tavily Web Search.
* **Distance Calculation Integration:** Integrated distance computation tool to evaluate proximity to central hubs, metro stations, or landmarks.
* **Automatic Currency Standardization:** Ensures all rent prices and budget estimates display in formatted Indian Rupees ($\text{INR } ₹$).
* **Direct Navigation Links:** Generates ready-to-use Google Maps direction links for every recommended hostel.

---

## 🛠️ Tech Stack

* **Framework:** Python 3.10+
* **Agentic Workflow:** LangGraph, LangChain
* **External APIs:** Google Places API, Tavily Web Search API
* **Utilities:** `googlemaps`, `spacy` / `re`

---

## 📂 Project Structure

```text
.
├── backend/
│   ├── config.py                 # API keys and environment configurations
│   ├── agent.py                  # StateGraph workflow and agent node definitions
│   └── tools/
│       ├── distance_calculator.py# Distance computation helper
│       ├── filter_rank.py        # Custom logic for ranking search snippets
│       └── web_search.py         # Tavily web search integration
├── .gitignore
├── requirements.txt
└── README.md

```

## ⚙️ Setup & Installation

### 1. Clone the Repository
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git
cd YOUR_REPOSITORY_NAME

### 2. Create Virtual Environment
python -m venv venv

Windows:
venv\Scripts\activate

### 3. Install Dependencies
pip install -r requirements.txt

### 4. Configure API Keys

Create a .env file in the project root directory:

#### GPLACES_API_KEY = AIzaSyCuSBy_33inHkgutyPZWaoBXLUxdYy1ODI

#### TAVILY_API_KEY = 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

Note: Never upload your API keys to GitHub. Add .env to .gitignore.

---

## 🚀 Running the Agent

### Run the agent from the terminal:

python -m backend.agent

### Local Web Interface (Streamlit UI)

To launch the interactive chat UI on localhost:

Bash

streamlit run app.py

Local Web URL: Open http://localhost:8501 in your browser.

#### Example user query:

Find hostels in Vadapalani under ₹8000 near a metro station with Wi-Fi.

The agent understands the request, selects the required tools, searches external sources, calculates distances, filters and ranks suitable hostels, and provides a final recommendation.

---

## 🔄 Agent Workflow
                         USER
                           │
                           ▼
                  Natural Language Query
                           │
                           ▼
                    LangGraph Agent
                           │
                           ▼
                     OpenRouter LLM
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
       Google Places    Distance    Web Search
           Tool           Tool          Tool
              │            │            │
              └────────────┼────────────┘
                           ▼
                     Filter & Rank
                           │
                           ▼
                         Memory
                           │
                           ▼
                  Final Recommendation

---

## 🤖 Why HostelHunt AI is Agentic

HostelHunt AI is more than a simple chatbot. The LLM understands the user's goal and decides which tools are required to complete the task.

### The agent can:

Understand natural-language requirements.
Select and use appropriate tools.
Search external information.
Calculate distances.
Filter and rank hostel options.
Maintain conversation memory.
Provide personalized recommendations.
💡 Example

### User:

I need a hostel in Vadapalani under ₹8000,
near a metro station and with Wi-Fi.

### HostelHunt AI:

1. Understands the user's requirements.
2. Searches Google Places for suitable hostels.
3. Calculates distance from the preferred location.
4. Uses web search for additional information when required.
5. Filters unsuitable options.
6. Ranks the remaining hostels.
7. Provides the best matching recommendations.
