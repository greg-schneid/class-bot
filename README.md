# class-bot

Discord bot to answer course-administrative questions using local course materials and a swappable model backend.

## Layout

- `data/course_docs/*.md` contains the main course documents.
- `data/course_updates/*.md` contains manually maintained update notes.
- `src/ai/` contains model backends selected by `MODEL_BACKEND`.
- `src/rag/answerer.py` is the stable app-facing answer entrypoint.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `MODEL_BACKEND=qwen_local` for free local testing with `mlx_lm`, or `MODEL_BACKEND=openai` once the OpenAI path is implemented.

## Run

```bash
python -m src.bot.discord_bot
```

## CLI testing

You can test the answer flow before Discord with:

```bash
python -m src.cli.ask "Does MTE 320 have mandatory labs?" --course MTE320
```
