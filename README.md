# class-bot

Discord bot to answer course-administrative questions using local course materials and a swappable model backend.

## Layout

- `data/` is a private git submodule containing course documents and updates.
- `src/ai/` contains model backends selected by `MODEL_BACKEND`.
- `src/rag/answerer.py` is the stable app-facing answer entrypoint.

## Setup

```bash
git submodule update --init --recursive
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `MODEL_BACKEND=qwen_local` for free local testing with `mlx_lm`, or `MODEL_BACKEND=openai` once the OpenAI path is implemented.

## Run

```bash
.venv/bin/python -m src.bot.discord_bot
```

## Normalize raw course files

The bot expects the private `data/` submodule to be present. After cloning, initialize it with:

```bash
git submodule update --init --recursive
```

If you add raw PDFs or saved HTML course pages under `data/course_docs/raw`, rebuild the standardized markdown files with:

```bash
.venv/bin/python -m src.docs.normalize_raw_docs
```

## CLI testing

You can test the answer flow before Discord with:

```bash
.venv/bin/python -m src.cli.ask "Does MTE 320 have mandatory labs?" --course MTE320
```
