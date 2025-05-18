console.log("Testing API connection...");
fetch("http://localhost:5056/api/iocs")
  .then((r) => r.json())
  .then((d) => console.log("API response:", d))
  .catch((e) => console.error("API error:", e));
