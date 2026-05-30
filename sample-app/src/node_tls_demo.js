const https = require("https");

const weakAgent = new https.Agent({
  secureProtocol: "TLSv1_method",
  rejectUnauthorized: false,
});

https.get("https://internal.example.local/health", { agent: weakAgent }, (response) => {
  response.resume();
});
