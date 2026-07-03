# Flask + Express Deployment Assignment

A minimal full-stack app:
- **Backend**: Flask REST API (`/backend`) — a simple in-memory Todo API
- **Frontend**: Express server (`/frontend`) — serves a static HTML page that calls the Flask API

The only thing that changes between the three deployment scenarios is the
**`BACKEND_URL`** the frontend uses to reach the backend. Everything else is identical.

---

## 0. Test locally first (optional but recommended)

```bash
docker compose up --build
```
Visit `http://localhost:3000`. This proves the app works before you touch AWS.

---

## 1. Single EC2 instance (both apps on one server)

1. Launch **one** EC2 instance (Ubuntu 22.04, t2.micro is fine).
2. Security Group: allow inbound TCP `22` (SSH), `3000` (frontend), `5000` (backend).
3. SSH in and install dependencies:
   ```bash
   sudo apt update
   sudo apt install -y python3-pip python3-venv nodejs npm
   ```
4. Copy the project to the instance (`scp -r fullstack-app ubuntu@<EC2_IP>:~`).
5. Start the backend:
   ```bash
   cd ~/fullstack-app/backend
   python3 -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   python3 app.py &          # or use gunicorn / a systemd service
   ```
6. Start the frontend, pointing it at the backend on **localhost** (same machine):
   ```bash
   cd ~/fullstack-app/frontend
   npm install
   BACKEND_URL=http://localhost:5000 npm start &
   ```
7. Open `http://<EC2_PUBLIC_IP>:3000` in your browser.

> Tip: use `pm2` or a `systemd` unit for both processes so they survive reboot/SSH logout.

---

## 2. Two separate EC2 instances (backend and frontend split)

1. Launch **two** EC2 instances in the same VPC/subnet: `backend-ec2` and `frontend-ec2`.
2. Security groups:
   - `backend-ec2`: allow inbound `5000` **only from the frontend-ec2's security group** (and `22` for SSH).
   - `frontend-ec2`: allow inbound `3000` from your IP/anywhere, and `22` for SSH.
3. On **backend-ec2**: install Python, copy `backend/`, run the Flask app on port `5000` (same as step 1 above).
4. On **frontend-ec2**: install Node, copy `frontend/`, then start it pointing at the backend's **private IP**:
   ```bash
   BACKEND_URL=http://<BACKEND_PRIVATE_IP>:5000 npm start
   ```
5. Open `http://<FRONTEND_PUBLIC_IP>:3000`.

> Note: `BACKEND_URL` is used by the *browser* directly (see `public/index.html`), so if
> your browser can't reach the backend's private IP, use the backend's **public IP**
> instead (and open port 5000 to your IP in its security group).

---

## 3. Docker containers via ECR + ECS + VPC

### a) Build & push images to ECR
```bash
# Create two repos
aws ecr create-repository --repository-name flask-backend
aws ecr create-repository --repository-name express-frontend

# Authenticate Docker to ECR
aws ecr get-login-password --region <REGION> | docker login --username AWS \
  --password-stdin <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com

# Build, tag, push backend
docker build -t flask-backend ./backend
docker tag flask-backend:latest <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/flask-backend:latest
docker push <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/flask-backend:latest

# Build, tag, push frontend
docker build -t express-frontend ./frontend
docker tag express-frontend:latest <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/express-frontend:latest
docker push <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/express-frontend:latest
```

### b) VPC
Use the default VPC (has public subnets) or create one with:
- 2 public subnets (different AZs) for a simple setup
- An Internet Gateway attached
- Route table sending `0.0.0.0/0` to the IGW

### c) ECS Cluster
```bash
aws ecs create-cluster --cluster-name fullstack-cluster
```
Use the **Fargate** launch type (no EC2 servers to manage).

### d) Task Definitions
Create two task definitions (one per container), each referencing its ECR image:
- `flask-backend-task`: image = backend ECR URI, container port `5000`
- `express-frontend-task`: image = frontend ECR URI, container port `3000`, environment variable `BACKEND_URL` = the backend service's address (see below)

### e) Services
- Create an ECS **Service** for the backend task, in your public subnets, with a security
  group allowing inbound `5000` from the frontend service's security group only.
- Enable **Service Connect** (or a Cloud Map namespace) so the backend gets a discoverable
  DNS name, e.g. `backend.fullstack.local`.
- Create an ECS **Service** for the frontend task with `BACKEND_URL=http://backend.fullstack.local:5000`,
  in a public subnet, security group allowing inbound `3000` from the internet (0.0.0.0/0),
  and `assignPublicIp=ENABLED` (or put it behind an Application Load Balancer for a stable URL).

### f) Access
Open the frontend service's public IP (or ALB DNS name) on port `3000`.

---

## Project structure
```
fullstack-app/
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── server.js
│   ├── package.json
│   ├── Dockerfile
│   └── public/index.html
├── docker-compose.yml
└── README.md
```
