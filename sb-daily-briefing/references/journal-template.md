# Journal Template

Template voor nieuwe daily journal entries.

## Format

```markdown
#daily [[{YYYY-MM}]]

# 📥 Braindump
## Quick Capture
> When in doubt, just throw it here. Use timestamps! If you add a task here, it's due (due::today)


## Meetings and notable events
> Specific for meetings and other events

# 📋 Logs
### Notes created today
```dataviewjs
const query = `
List
FROM ""
WHERE file.cday = date(substring("${dv.current().file.name}",0,10))
SORT file.ctime asc
`;
dv.span('```dataview' + query + '```');
```
### Notes last touched today
```dataviewjs
const query = `
List
FROM ""
WHERE file.mday = date(substring("${dv.current().file.name}",0,10))
SORT file.mtime asc
`;
dv.span('```dataview' + query + '```');
```
### Tasks completed today
```dataviewjs
var date = dv.current().file.name.split('-')

var year = date[0]
var month = date[1]
var day = date[2]

var formattedDate = year+"-"+month+"-"+day

if (year != "template"){
	const query = `
TASK
WHERE completion = date(${formattedDate})
SORT file.ctime asc
`;
dv.span('```dataview' + query + '```');
}
```
```

## Variabelen

- `{YYYY-MM}`: Jaar-maand (bijv. `2026-02`)
- `{YYYY-MM-DD}`: Volledige datum (bijv. `2026-02-10`)
