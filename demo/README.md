# PrismQL Interactive Demo

A web-based demonstration of PrismQL query language for conversational data analysis.

## Features

- 🎯 **Interactive Query Interface** - Type and execute PrismQL queries in real-time
- 📚 **Example Queries** - 30+ pre-built queries organized by category
- 💬 **Synthetic Dataset** - Realistic customer support conversations
- 🔍 **Result Visualization** - See matched messages with full context
- 📖 **Inline Documentation** - Quick reference guide and syntax help

## Quick Start

### Run Locally

```bash
# Install dependencies
uv pip install '.[demo]'

# Or install just what's needed
uv pip install streamlit

# Run the app
streamlit run demo/app.py
```

The app will open in your browser at `http://localhost:8501`

### Deploy to Streamlit Cloud (Free)

1. **Fork/Clone this repository**

2. **Go to [share.streamlit.io](https://share.streamlit.io)**

3. **Click "New app"**

4. **Configure deployment:**
   - Repository: `your-username/prismql`
   - Branch: `main`
   - Main file path: `demo/app.py`
   - Python version: `3.9+`

5. **Click "Deploy"**

Your demo will be live at `https://your-app-name.streamlit.app` in ~2 minutes!

## Demo Dataset

The demo uses synthetic customer support conversations featuring:

- **Users:**
  - Customers: alice, bob, charlie, david, emma, frank
  - Support agents: support_sarah, support_mike, support_lisa
  - Managers: manager_john, manager_kate

- **Patterns:**
  - Greetings and introductions
  - Problems and solutions
  - Questions and answers
  - Escalations to management
  - Thank you messages

- **Size:** ~100-150 messages with realistic conversation patterns

## Example Queries

### Basic Filtering
```prismql
-- All messages from alice
SELECT from(alice)

-- All support agent messages
SELECT from(support_sarah)

-- Messages containing problems
SELECT contains(problems)
```

### Boolean Operations
```prismql
-- Messages from alice OR bob
SELECT from(alice) OR from(bob)

-- Problems from any customer
SELECT from(*) AND contains(problems)

-- Messages NOT from support
SELECT NOT from(support_sarah)
```

### Sequential Patterns
```prismql
-- Customer then support response
SELECT from(alice) FOLLOWED_BY from(support_sarah) WITHIN 3

-- Problem then solution
SELECT contains(problems) FOLLOWED_BY contains(solutions) WITHIN 5

-- Customer NOT followed by support (unanswered)
SELECT from(alice) NOT_FOLLOWED_BY from(support_sarah) WITHIN 10
```

### Pattern Variables
```prismql
-- Same user posting twice
SELECT from($user), from($user) INWIN 3

-- User asks, support responds, user follows up
SELECT from($customer) FOLLOWED_BY from(support_sarah) WITHIN 5 FOLLOWED_BY from($customer) WITHIN 5
```

### Advanced Patterns
```prismql
-- Escalation pattern: problem → urgent → manager
SELECT contains(problems) FOLLOWED_BY contains(urgent) WITHIN 3 FOLLOWED_BY from(manager_john) WITHIN 5

-- Question-answer-thanks sequence
SELECT contains(questions) FOLLOWED_BY from(support_sarah) WITHIN 3 FOLLOWED_BY contains(thanks) WITHIN 3
```

## Available Dictionaries

The demo includes these pre-defined word lists:

- `greetings` - hello, hi, hey, good morning
- `problems` - error, issue, problem, bug, broken, failed
- `solutions` - fixed, resolved, solved, try, reset
- `thanks` - thank, thanks, appreciate, perfect
- `urgent` - urgent, emergency, asap, critical
- `questions` - what, when, where, how, why, can you

## Customization

### Add Your Own Data

Edit `demo/generate_demo_data.py`:

```python
def generate_demo_conversations():
    conversations = []

    # Add your messages
    conversations.append({
        "id": 1,
        "user": "your_user",
        "text": "Your message text"
    })

    return conversations
```

### Add New Dictionaries

Edit `demo/generate_demo_data.py`:

```python
def get_demo_dictionaries():
    return {
        "your_dict": ["word1", "word2", "word3"],
        # ... existing dictionaries
    }
```

### Customize UI

Edit `demo/app.py` to change:
- Color scheme (`.streamlit/config.toml`)
- Example queries
- Page layout
- Result formatting

## Deployment Options

### Streamlit Cloud (Recommended)
- ✅ **Free tier available**
- ✅ **Automatic updates from GitHub**
- ✅ **HTTPS included**
- ✅ **No configuration needed**

### Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy
railway init
railway up
```

### Render
1. Connect your GitHub repo
2. Select "Web Service"
3. Build command: `pip install '.[demo]'`
4. Start command: `streamlit run demo/app.py --server.port $PORT`

### Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install '.[demo]'

EXPOSE 8501

CMD ["streamlit", "run", "demo/app.py"]
```

```bash
docker build -t prismql-demo .
docker run -p 8501:8501 prismql-demo
```

## Troubleshooting

### Import Errors
```bash
# Make sure you're in the project root
cd /path/to/prismql

# Install in development mode
pip install -e '.[demo]'
```

### Port Already in Use
```bash
# Use a different port
streamlit run demo/app.py --server.port 8502
```

### Streamlit Cloud Deployment Fails
- Check that `demo/requirements.txt` exists
- Verify Python version is 3.9+
- Check logs in Streamlit Cloud dashboard

## Screenshots

(Add screenshots of your deployed demo here)

## Links

- [PrismQL Documentation](https://prismql.readthedocs.io)
- [PrismQL GitHub](https://github.com/prismql/prismql)
- [Streamlit Documentation](https://docs.streamlit.io)

## License

MIT License - see LICENSE file for details
