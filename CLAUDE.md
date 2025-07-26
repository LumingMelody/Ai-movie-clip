# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-powered video editing system that automatically analyzes video content and generates edited videos based on user requirements. The system supports multiple video templates, AI-generated content, and various video effects.

## Core Architecture

### Main Components

1. **Core System** (`/core/`):
   - `orchestrator/` - Workflow orchestration and main processing pipeline
   - `analyzer/` - Video content analysis using CV and ML models
   - `ai/` - AI model integration for content generation
   - `clipeffects/` - Video effects and filters
   - `cliptransition/` - Video transition effects
   - `clipgenerate/` - AI content generation (text-to-image, voice synthesis)
   - `cliptemplate/` - Video template system with specialized generators

2. **Template System** (`/templates/`):
   - Jinja2 templates organized by industry/use case
   - Categories: activity, brand, business, ecom, exhibition, groupon, ip, store
   - Template types: knowledge, painpoint, scenario, straightforward, suspense, testimonial

3. **Entry Points**:
   - `main.py` - CLI interface for video analysis and editing
   - `app.py` - FastAPI web server with 27+ endpoints
   - Various MCP (Model Context Protocol) servers for external integration

### Key Modules

- **VideoEditingOrchestrator** (`core/orchestrator/workflow_orchestrator.py`): Main workflow coordinator
- **VideoAnalyzer** (`core/analyzer/video_analyzer.py`): Video content analysis using OpenCV, YOLO, Whisper
- **AIModelCaller** (`core/ai/ai_model_caller.py`): AI model integration (primarily Qwen/Tongyi)

## Common Commands

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run the CLI application
python main.py --help

# Run the FastAPI server
python app.py
# or
uvicorn app:app --reload

# Run specific video analysis
python main.py analyze video.mp4 --output analysis.json

# Run video editing
python main.py edit video.mp4 --duration 30 --style "抖音风"
```

### Testing
The project uses various video analysis and generation tools. Test with:
```bash
# Test video analysis workflow
python main.py analyze test_video.mp4 --verbose

# Test complete editing workflow
python main.py edit test_video.mp4 --duration 60 --output ./output/
```

## Key Dependencies

- **Video Processing**: moviepy, opencv-python, scenedetect
- **AI/ML**: ultralytics (YOLO), whisper, speech_recognition, librosa
- **Web Framework**: fastapi, uvicorn
- **AI Services**: dashscope (Alibaba Tongyi), openai
- **Audio Processing**: pydub, webrtcvad
- **Template Engine**: Jinja2

## Configuration

- API keys stored in `api_key.txt` (git-ignored)
- Configuration files in `/config/` directory
- Voice and product configurations in JSON format

## Architecture Notes

### Video Analysis Pipeline
1. **Content Detection**: Scene detection, object recognition (YOLO)
2. **Audio Analysis**: Speech recognition, audio feature extraction
3. **Template Selection**: Based on content type and user requirements
4. **Effect Application**: Transitions, filters, and enhancements

### AI Integration
- Primary model: Qwen (Tongyi Qianwen) via DashScope API
- Supports text generation, image generation, and voice synthesis
- Fallback to local models when API unavailable

### Template System
- Industry-specific templates with Jinja2
- Automatic template selection based on content analysis
- Support for various video styles (social media, commercial, educational)

## Important Files

- `main.py:560-686` - Main CLI entry point with comprehensive argument parsing
- `app.py:1-50` - FastAPI application setup with extensive endpoint definitions
- `core/orchestrator/workflow_orchestrator.py:31-50` - Main workflow coordination
- `core/analyzer/video_analyzer.py:36-50` - Video analysis engine
- `core/ai/ai_model_caller.py:16-50` - AI model integration

## Development Notes

- The system is designed to handle both online and offline video sources
- Extensive logging system with automatic log file generation
- Support for batch processing and concurrent video analysis
- MCP (Model Context Protocol) integration for external tool connectivity
- Chinese language support throughout the system