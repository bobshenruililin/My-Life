.PHONY: install validate report plan ics table deadlines anki

install:
	pip install -r requirements.txt
	chmod +x career-os

validate:
	PYTHONPATH=. python3 scripts/validate_opportunities.py

report:
	PYTHONPATH=. python3 -m career_os report

plan:
	PYTHONPATH=. python3 -m career_os summer-plan --urls

ics:
	PYTHONPATH=. python3 -m career_os ics

table:
	PYTHONPATH=. python3 -m career_os table
	PYTHONPATH=. python3 -m career_os table --laidlaw-safe --out state/opportunities_laidlaw_safe.md

deadlines:
	PYTHONPATH=. python3 -m career_os deadlines --within-days 60 --urls

anki:
	PYTHONPATH=. python3 -m career_os anki-export --source templates/sample_anki_cards.md

all: validate report plan ics table deadlines anki
