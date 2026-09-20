import sys
import os
from collections import defaultdict
from datetime import datetime
from jira import JIRA
from dotenv import load_dotenv

# --- CONFIGURATION ---
# Load environment variables from .env file
load_dotenv()

JIRA_SERVER = "https://jira.omgeving.vlaanderen.be/jira/"
JIRA_TOKEN = os.getenv("JIRA_TOKEN")

if not JIRA_TOKEN:
    print("ERROR: No JIRA_TOKEN found in .env file or environment variables.")
    sys.exit(1)

def get_jira_client():
    try:
        return JIRA(server=JIRA_SERVER, token_auth=JIRA_TOKEN)
    except Exception as e:
        print(f"Error connecting to JIRA: {e}")
        sys.exit(1)

def get_epic_actuals(jira, epic_key):
    """
    Fetches total time spent (in seconds) for an Epic, including all
    issues linked to this Epic (via Parent/Epic Link) and their subtasks.
    """
    jql = f'("Epic Link" = {epic_key} OR parent = {epic_key})'
    
    try:
        issues = jira.search_issues(jql, maxResults=False, fields="timespent,aggregatetimespent")
    except Exception as e:
        jql = f'"Epic Link" = {epic_key}'
        try:
            issues = jira.search_issues(jql, maxResults=False, fields="timespent,aggregatetimespent")
        except:
            return 0
            
    total_seconds = 0
    for issue in issues:
        if issue.fields.aggregatetimespent:
             total_seconds += issue.fields.aggregatetimespent
        elif issue.fields.timespent:
             total_seconds += issue.fields.timespent
             
    return total_seconds

def generate_reports(billing_key):
    jira = get_jira_client()
    print(f"--- Fetching Data for Billing Key: {billing_key} ---")
    
    # 1. Milestone Table
    jql_epics = f'billingkey = "{billing_key}" AND issuetype = Epic ORDER BY Rank ASC'
    try:
        epics = jira.search_issues(jql_epics, maxResults=False, fields="summary,status,resolution,timeoriginalestimate,timespent,aggregatetimespent,resolutiondate")
    except Exception as e:
        print(f"Error searching for epics: {e}")
        return

    print(f"\n### Milestone Table ({len(epics)} epics found)")
    print(f"{ 'Key':<12} | { 'Milestone':<50} | { 'Status':<15} | { 'Forecast (md)':<13} | { 'Actual (md)':<12} | {'Deviation'}")
    print("-" * 125)
    
    total_forecast = 0
    total_actual = 0
    completed_epics_by_date = [] 
    
    for epic in epics:
        name = epic.fields.summary
        status_name = epic.fields.status.name
        resolution = epic.fields.resolution.name if epic.fields.resolution else None
        
        # Status Mapping
        if status_name.lower() in ['backlog', 'to do', 'open', 'selected for development']:
            mapped_status = "backlog"
        elif status_name.lower() in ['closed', 'done', 'resolved']:
            if resolution and resolution.lower() in ["won't fix", "duplicate", "cannot reproduce"]:
                mapped_status = "cancelled"
            else:
                mapped_status = "completed"
        else:
            mapped_status = "in progress"
            
        # Forecast
        forecast_sec = epic.fields.timeoriginalestimate or 0
        forecast_days = round(forecast_sec / 3600 / 8)
        
        # Actuals: Epic itself + Children
        epic_own_time = epic.fields.timespent or 0 
        children_time = get_epic_actuals(jira, epic.key) 
        
        actual_total_sec = epic_own_time + children_time
        actual_days = round(actual_total_sec / 3600 / 8)
        
        # Deviation
        if forecast_days > 0:
            dev = ((actual_days - forecast_days) / forecast_days) * 100
            dev_str = f"{round(dev)}%"
        else:
            dev_str = "-"
            
        print(f"{epic.key:<12} | {name[:48]:<50} | {mapped_status:<15} | {forecast_days:<13} | {actual_days:<12} | {dev_str}")
        
        if mapped_status != "cancelled":
            total_forecast += forecast_days
            total_actual += actual_days
            
        if mapped_status == "completed" and epic.fields.resolutiondate:
            res_date = datetime.strptime(epic.fields.resolutiondate.split('T')[0], '%Y-%m-%d')
            completed_epics_by_date.append((res_date, forecast_days))

    print("-" * 125)
    dev_total = round(((total_actual - total_forecast) / total_forecast) * 100) if total_forecast > 0 else 0
    print(f"{ 'TOTAL':<12} | { '':<50} | { '':<15} | {total_forecast:<13} | {total_actual:<12} | {dev_total}%")


    # 2. Resource Table
    print(f"\n\n### Resource Table (Fetching worklogs...)")
    jql_all = f'billingkey = "{billing_key}"'
    all_issues = jira.search_issues(jql_all, maxResults=False, fields="worklog")
    
    worklogs_by_month = defaultdict(float)
    
    for issue in all_issues:
        try:
            worklogs = jira.worklogs(issue.id)
            for w in worklogs:
                w_date = datetime.strptime(w.started.split('T')[0], '%Y-%m-%d')
                month_key = w_date.strftime("%Y-%m")
                worklogs_by_month[month_key] += w.timeSpentSeconds / 3600 / 8
        except:
            pass

    scope_by_month = defaultdict(float)
    for res_date, size in completed_epics_by_date:
        month_key = res_date.strftime("%Y-%m")
        scope_by_month[month_key] += size
        
    all_months = sorted(set(list(worklogs_by_month.keys()) + list(scope_by_month.keys())))
    
    if not all_months:
        print("No data found.")
        return

    print(f"{ 'Month':<10} | { 'Eff. Effort (md)':<18} | { 'Eff. Effort CUM(md)':<18} | { 'Scope (md)':<12} | { 'Scope CUM (md)'}")
    print("-" * 85)
    
    cum_effort = 0
    cum_scope = 0
    
    for m in all_months:
        effort = worklogs_by_month[m]
        scope = scope_by_month[m]
        cum_effort += effort
        cum_scope += scope
        print(f"{m:<10} | {round(effort):<18} | {round(cum_effort):<20} | {round(scope):<12} | {round(cum_scope)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 generate_report.py <BILLING_KEY>")
        sys.exit(1)
    
    billing_key = sys.argv[1]
    generate_reports(billing_key)
