# Architectural Decision Log

This document records key technical decisions made during this project, the alternatives considered, and the reasoning behind each choice.

---

## Decision 1: Project Structure — Mono-repo with Domain Folders

**Date:** 2026-03-22
**Status:** Accepted

**Context:** Needed to decide how to organize the codebase — a single repository with domain-based folders, or multiple repositories per component.

**Decision:** Single repository with domain folders (ingestion/, processing/, dbt_models/, orchestration/, dashboard/, terraform/, tests/).

**Alternatives considered:**
- Multi-repo (separate repos for ingestion, processing, dashboard) — rejected because it adds CI/CD complexity without benefit for a single-developer project.
- Flat structure (all files in root) — rejected because it becomes unnavigable as the project grows.

**Reasoning:** A mono-repo with clear domain folders mirrors how production teams at Belgian consulting firms organize projects. Each folder has a single responsibility. A recruiter opening this repo can immediately understand the architecture from the folder names alone.

---

## Decision 2: uv + pyproject.toml over pip + requirements.txt

**Date:** 2026-03-22
**Status:** Accepted

**Context:** Needed to choose a Python dependency management approach.

**Decision:** Use uv as the package manager with pyproject.toml as the single configuration file.

**Alternatives considered:**
- pip + requirements.txt — rejected because it requires separate config files for each tool (pytest.ini, .flake8, setup.py) and has slower dependency resolution.
- Poetry + pyproject.toml — viable, but uv is significantly faster and gaining rapid adoption in the Python ecosystem.

**Reasoning:** pyproject.toml is the official Python packaging standard (PEP 621). It consolidates project metadata, dependencies, and tool configuration in one file. uv provides fast, reliable dependency resolution. Separating dev dependencies under [project.optional-dependencies] keeps production installs clean.

---

## Decision 3: Git Bash as Default Terminal on Windows

**Date:** 2026-03-22
**Status:** Accepted

**Context:** Working on Windows, needed to choose between PowerShell, CMD, or Git Bash for development.

**Decision:** Git Bash as the default VS Code terminal.

**Alternatives considered:**
- PowerShell — commands differ from Linux/Mac, making it harder to follow data engineering documentation and tutorials which assume Bash.
- WSL (Windows Subsystem for Linux) — more powerful but adds setup complexity. Can migrate later if needed.

**Reasoning:** All data engineering tooling (Docker, Terraform, CI/CD, Airflow) uses Bash commands. Using Git Bash ensures consistency between local development and the GitHub Actions CI environment, which runs on Ubuntu.

---



## Decision 4: Remote State in Azure Blob Storage

**Date:** 2026-03-23
**Status:** Accepted

**Context:** Terraform state tracks all managed resources. Storing it locally risks accidental deletion and prevents team collaboration.

**Decision:** Store Terraform state in a dedicated Azure Blob Storage account (`belgiantransporttfstate`) with the `tfstate` container.

**Alternatives considered:**
- Local state file — rejected because it's not backed up, can't be shared, and risks accidental deletion.
- Terraform Cloud — viable but adds another service dependency. Azure Blob Storage keeps everything within the Azure ecosystem.

**Reasoning:** Remote state is the production standard. It provides versioning, locking (prevents concurrent modifications), and durability. Using a separate storage account from the data lake keeps infrastructure concerns isolated from data concerns.

---
*New decisions will be added as the project progresses.*