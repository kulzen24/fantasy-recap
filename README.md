# LLM Fantasy Football Recap Generator

A web-based application that generates personalized, insightful fantasy football recaps using Large Language Models (LLMs). Connect your Yahoo, ESPN, and Sleeper leagues to get AI-powered recaps in your writing style.

## Features

- 🔐 **Single Sign-On Authentication** with Google and fantasy platforms
- 🏈 **Multi-Platform Integration** - Yahoo, ESPN, and Sleeper APIs
- 🤖 **Multi-LLM Support** - ChatGPT, Claude, and Gemini
- ✍️ **Personalized Style** - Train AI on your previous recaps
- 🏆 **Custom Weekly Awards** - Create and track your own awards
- 📱 **Modern UI** - ChatGPT-inspired clean interface
- 🔒 **Secure** - Best-practice encryption for API keys

## Tech Stack

### Backend
- **Database & Auth**: Supabase (PostgreSQL + Authentication)
- **API**: Node.js with Express and TypeScript
- **LLM Integration**: OpenAI, Anthropic, Google APIs

### Frontend
- **Framework**: React with TypeScript
- **Styling**: TailwindCSS
- **UI Components**: Modern component library
- **State Management**: React Query + Context

### External APIs
- Yahoo Fantasy Sports API
- ESPN Fantasy API (unofficial)
- Sleeper API
- OpenAI API (ChatGPT)
- Anthropic API (Claude)
- Google AI API (Gemini)

## Getting Started

### Prerequisites
- Node.js 18+
- npm or yarn
- Supabase account

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/fantasy-recaps.git
cd fantasy-recaps
```

2. Install dependencies
```bash
# Install backend dependencies
cd backend
npm install

# Install frontend dependencies
cd ../frontend
npm install
```

3. Set up environment variables
```bash
# Copy environment template
cp .env.example .env

# Add your API keys and Supabase configuration
```

4. Start development servers
```bash
# Start backend (in backend directory)
npm run dev

# Start frontend (in frontend directory)
npm run dev
```

## Project Structure

```
fantasy-recaps/
├── backend/              # Node.js/Express API server
├── frontend/             # React web application
├── docs/                 # Project documentation
├── .taskmaster/          # Task management files
└── README.md
```

## Development

This project uses TaskMaster for project management. See `.taskmaster/` directory for current tasks and progress.

### Running Tests
```bash
# Backend tests
cd backend && npm test

# Frontend tests
cd frontend && npm test
```

### Code Quality
```bash
# Lint code
npm run lint

# Format code
npm run format
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you have questions or need help, please open an issue or reach out to the maintainers.
