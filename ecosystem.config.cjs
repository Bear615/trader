/**
 * PM2 ecosystem config
 * Usage:  pm2 start ecosystem.config.cjs
 *         pm2 restart ecosystem.config.cjs
 */
module.exports = {
  apps: [
    {
      name: "xrp-backend",
      cwd: "./backend",
      script: "./venv/bin/python",
      args: "-m uvicorn main:app --host 0.0.0.0 --port 8000",
      interpreter: "none",
      env: {
        PYTHONUNBUFFERED: "1",
      },
      // Restart on crash, but not in a tight loop
      autorestart: true,
      max_restarts: 10,
      restart_delay: 3000,
    },
    {
      name: "xrp-frontend",
      cwd: "./frontend",
      script: "npm",
      args: "run dev",
      interpreter: "none",
      autorestart: true,
      max_restarts: 10,
      restart_delay: 3000,
    },
  ],
};
