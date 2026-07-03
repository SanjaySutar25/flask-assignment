const express = require("express");
const path = require("path");

const app = express();
const PORT = process.env.PORT || 3000;

// The URL of the Flask backend. This is the ONE line you change between the
// three deployment scenarios (same instance / separate instance / ECS service).
//   - Scenario 1 (same EC2):       http://localhost:5000
//   - Scenario 2 (separate EC2):   http://<BACKEND_PRIVATE_IP>:5000
//   - Scenario 3 (ECS/Docker):     http://<backend-service-name>:5000  (via ECS service discovery)
const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:5000";

app.use(express.static(path.join(__dirname, "public")));
app.use(express.json());

// Simple proxy endpoint so the browser only ever talks to the frontend origin,
// and the frontend server talks to the Flask backend server-to-server.
app.get("/config.js", (req, res) => {
  res.type("application/javascript");
  res.send(`window.BACKEND_URL = "${BACKEND_URL}";`);
});

app.get("/health", async (req, res) => {
  res.json({ status: "ok", service: "express-frontend" });
});

app.listen(PORT, "0.0.0.0", () => {
  console.log(`Express frontend running on port ${PORT}`);
  console.log(`Talking to Flask backend at: ${BACKEND_URL}`);
});
