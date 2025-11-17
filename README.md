# Scout

An intelligent code review system that learns from your feedback to provide better suggestions over time.

## Features

- 🔍 **Code Review**: Analyzes code diffs from GitHub PRs or local git repos
- 🧠 **Learning Memory**: Stores accepted/rejected suggestions in vector DB (ChromaDB)
- 📈 **Adaptive**: Improves review style based on your feedback patterns
- 🌐 **Web Interface**: Simple, clean UI for viewing reviews and providing feedback
- 🔗 **GitHub Integration**: Fetches PRs directly from GitHub

## Prerequisites

1. **Python 3.8+**
2. **Ollama** installed and running
3. **Llama 3.1 8B model** pulled in Ollama
4. **GitHub Token** (optional, for GitHub PR integration)

### Installing Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# Download from https://ollama.com/download

# Pull the model
ollama pull llama3.1:8b
```

### Getting a GitHub Token

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate a new token with `repo` scope
3. Copy the token for use in `.env` file

## Setup

1. **Clone the repository** (or navigate to project directory)

2. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

3. **Create `.env` file** from `.env.example`:
```bash
cp .env.example .env
```

4. **Edit `.env`** with your configuration:
```env
# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# GitHub (optional)
GITHUB_TOKEN=your_token_here

# Backend
API_PORT=8000

# Learning
MIN_CONFIDENCE_TO_SHOW=30
AUTO_LEARN=true

# ChromaDB
CHROMA_DB_PATH=./chroma_db
```

5. **Start the server** (from project root):
```bash
python run.py
```

Or use uvicorn directly:
```bash
uvicorn backend.main:app --reload --port 8000
```

Or run from backend directory:
```bash
cd backend
python main.py
```

6. **Open your browser**:
```
http://localhost:8000
```

## Usage

### Starting a Review

1. **GitHub PR Review**:
   - Select "GitHub PR" as source
   - Paste GitHub PR URL (e.g., `https://github.com/owner/repo/pull/123`)
   - Click "Start Review"

2. **Local Diff Review**:
   - Select "Paste Diff" as source
   - Paste your git diff content
   - Click "Start Review"

### Providing Feedback

1. Review the generated suggestions
2. Click **Accept**, **Reject**, or **Edit** on each suggestion
3. For rejections, optionally provide a reason
4. For edits, modify the suggestion text before accepting
5. The system learns from your feedback to improve future reviews

### Viewing Statistics

- Click the **Statistics** tab to see:
  - Total feedback count
  - Acceptance rate
  - Feedback by category
  - Confidence calibration
  - Recent learning patterns

## API Endpoints

### `POST /api/review`
Create a new code review.

**Request Body**:
```json
{
  "source": "github",
  "url": "https://github.com/owner/repo/pull/123"
}
```

or

```json
{
  "source": "diff",
  "content": "diff --git a/file.py..."
}
```

**Response**:
```json
{
  "review_id": "uuid",
  "suggestions": [...],
  "file_count": 2,
  "total_changes": 45,
  "created_at": "2024-01-01T00:00:00"
}
```

### `POST /api/feedback`
Submit feedback on a suggestion.

**Request Body**:
```json
{
  "review_id": "uuid",
  "suggestion_id": "uuid",
  "action": "accept",
  "reason": "Optional reason"
}
```

### `GET /api/reviews`
Get list of recent reviews.

### `GET /api/stats`
Get learning statistics.

## How Learning Works

1. **Initial Review**: System generates suggestions based on code analysis
2. **Feedback Collection**: User accepts/rejects suggestions
3. **Vector Storage**: Feedback is stored in ChromaDB with code context
4. **Similarity Search**: Future reviews search for similar code patterns
5. **Adaptive Suggestions**: System applies learned preferences:
   - Stops suggesting patterns you've rejected
   - Emphasizes patterns you've accepted
   - Adjusts confidence based on past feedback

## Project Structure

```
.
├── backend/
│   ├── api/
│   │   ├── review.py      # Review endpoints
│   │   ├── feedback.py    # Feedback endpoints
│   │   └── stats.py       # Statistics endpoints
│   ├── services/
│   │   ├── github_service.py    # GitHub API integration
│   │   ├── review_service.py    # LLM review generation
│   │   ├── diff_parser.py       # Diff parsing
│   │   ├── vector_store.py      # ChromaDB integration
│   │   ├── feedback_service.py  # Feedback processing
│   │   └── stats_service.py     # Statistics generation
│   ├── models.py          # Data models
│   └── main.py           # FastAPI application
├── frontend/
│   ├── index.html        # Main UI
│   ├── styles.css        # Styling
│   └── app.js           # Frontend logic
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
└── README.md           # This file
```

## Configuration

### Environment Variables

- `OLLAMA_BASE_URL`: Ollama server URL (default: `http://localhost:11434`)
- `OLLAMA_MODEL`: Model name (default: `llama3.1:8b`)
- `GITHUB_TOKEN`: GitHub personal access token (optional)
- `API_PORT`: Backend server port (default: `8000`)
- `MIN_CONFIDENCE_TO_SHOW`: Minimum confidence to show suggestions (default: `30`)
- `AUTO_LEARN`: Automatically learn from feedback (default: `true`)
- `CHROMA_DB_PATH`: Path to ChromaDB storage (default: `./chroma_db`)

## Troubleshooting

### Ollama Connection Error

- Make sure Ollama is running: `ollama serve`
- Check `OLLAMA_BASE_URL` in `.env`
- Verify model is pulled: `ollama list`

### GitHub API Error

- Verify `GITHUB_TOKEN` is set in `.env`
- Check token has `repo` scope
- Ensure PR URL is correct format

### ChromaDB Issues

- Check `CHROMA_DB_PATH` is writable
- Delete `chroma_db` folder to reset learning memory
- Ensure ChromaDB version is compatible (0.4.x)

### LLM Response Parsing Errors

- Check Ollama logs for errors
- Verify model is loaded correctly
- Try reducing `MIN_CONFIDENCE_TO_SHOW` to see more suggestions

## Limitations

- Reviews may take 30-60 seconds for large PRs
- LLM suggestions may not always be perfect (confidence scores help)
- Learning improves over time with more feedback
- GitHub integration requires valid token

## Future Enhancements

- GitHub OAuth instead of personal token
- Post approved suggestions as PR comments
- Support for multiple programming languages
- Team mode with shared learning
- Browser extension for in-GitHub review
- Export/import learned preferences

## License

MIT License

## Contributing

Contributions welcome! Please open an issue or pull request.

## Support

For issues or questions, please open a GitHub issue.

