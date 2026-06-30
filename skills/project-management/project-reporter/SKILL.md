---
name: project-reporter
description: Generates monthly project reports (Milestone & Resource tables) from JIRA data using a billing key.
---

# Project Reporter

This skill generates monthly project reports by fetching data from JIRA. It produces two key tables:

1. **Milestone Table**: Shows progress per Epic (forecast vs actuals).
2. **Resource Table**: Shows cumulative effort and scope delivery over time.

## Prerequisites

Before running the report, ensure you have:

1. **Python Libraries**: Installed `jira` and `python-dotenv`.

    ```bash
    pip install jira python-dotenv
    ```

2. **JIRA Token**: A `.env` file in your working directory with your JIRA Personal Access Token.

    ```bash
    JIRA_TOKEN=your_token_here
    ```

## Usage

To generate a report for a specific project, run the bundled script with the project's **Billing Key**.

```bash
python3 <path-to-skill>/scripts/generate_report.py <BILLING_KEY>
```

**Example:**

```bash
python3 .gemini/skills/project-reporter/project-reporter/scripts/generate_report.py PASMOB
```

## Output

The script outputs two tables to stdout:

### 1. Milestone Table

Columns:

* **Key**: Epic Issue Key
* **Milestone**: Epic Summary
* **Status**: Backlog / In Progress / Completed / Cancelled
* **Forecast (md)**: Original Estimate in man-days
* **Actual (md)**: Total time spent (including child issues) in man-days
* **Deviation**: Percentage difference between Actual and Forecast

### 2. Resource Table

Columns:

* **Month**: YYYY-MM
* **Eff. Effort (md)**: Effort spent in that specific month
* **Eff. Effort CUM(md)**: Cumulative effort up to that month
* **Scope (md)**: Scope (Forecast of completed Epics) delivered in that month
* **Scope CUM (md)**: Cumulative delivered scope

## Workflow

1. Run the script for your project.
2. Copy the output tables.
3. Paste them into your monthly report (Confluence/Google Sheets).
