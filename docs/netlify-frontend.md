# Netlify frontend preview

The web application can be exported as static HTML and uploaded independently
from the API and lab infrastructure.

## Build and upload

From the repository root:

```bash
npm install
npm run build:netlify --workspace=web
```

Upload the contents of `apps/web/out/` to Netlify Drop. Do not upload the
repository or the `apps/web` source directory.

The static preview includes the home page, catalogue, lab details, gallery and
the interface shell. Operations that start lab containers, unlock hints,
manage teams, synchronize intelligence or verify certificates require a
separately hosted API.

## Connect a hosted API later

Set these variables in Netlify before rebuilding:

- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_INTEL_URL`

Production authentication must replace development tokens before exposing
interactive API operations publicly. The API must also permit the final
Netlify site origin through its CORS policy.
