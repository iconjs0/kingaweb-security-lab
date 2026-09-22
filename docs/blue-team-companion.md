# Blue-Team Companion (per red lab)

Every exploit lab ships a defensive twin — learners practice detection, not just exploitation.

## Manifest addition (`blueTeam:`)
```yaml
blueTeam:
  logBundle: "blue-team.json"      # shipped with lab, synthetic logs only
  siemDialect: ["splunk", "elastic"]
  detectionGoal: "Write a query finding IDOR reads (403→200 on /orders/:id for foreign user)"
  sampleQuerySplunk: 'index=lab sourcetype=shop_access user!=owner uri="/orders/*" status=200 | stats count by user, uri'
  sampleQueryElastic: 'user.keyword:* AND NOT user:owner AND url.path:/orders/* AND http.response.status_code:200'
  alertThreshold: "count > 5 / 5m per user"
```

## Content rules
- Logs synthetic, UTC, no PII. Red (attack) + blue (detect) + remediation (verify 403 + alert silence).
- Instructor view shows expected query + false-positive discussion.

Example: `labs/kingaweb-native/_example/blue-team.json`.
