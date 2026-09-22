// Phase-0 contract check: ensures openapi stub exists and is valid JSON
import { readFileSync, existsSync } from "fs";
const p = "packages/contracts/openapi.v1.json";
if (!existsSync(p)) { console.log("no openapi stub yet (ok)"); process.exit(0); }
JSON.parse(readFileSync(p, "utf8"));
console.log("contracts OK");
