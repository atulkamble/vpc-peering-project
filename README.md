# VPC Peering Project — Apache + Gunicorn + Flask + MariaDB

Amazon Linux 2023 production-style deployment: Apache (httpd) proxies to Gunicorn on loopback; Flask connects to MariaDB over VPC peering.

## Architecture

Browser → Apache :80 → Gunicorn 127.0.0.1:8000 → Flask → VPC peering → MariaDB :3306

Web VPC: `10.0.0.0/16`. DB VPC: `10.1.0.0/16`. Replace example DB IP with the actual private IP. This is a single-instance lab deployment, **not** a highly available production architecture.

## AWS networking

1. Create and accept VPC peering between non-overlapping CIDRs.
2. Web subnet route table: `10.1.0.0/16 → pcx-...`; DB subnet route table: `10.0.0.0/16 → pcx-...`.
3. Web EC2 security group: inbound TCP 80 from intended clients; TCP 443 when TLS is configured; SSH 22 only from administrator IP.
4. DB EC2 security group: inbound TCP 3306 **only from the web EC2 security group** where supported, or its private /32 address. No public database access.
5. Database MariaDB must listen on the DB instance private interface; configure `bind-address` and host-based SQL grants accordingly. Keep firewall restrictions in place.

## Database setup (on DB EC2)

```sql
CREATE DATABASE IF NOT EXISTS university;
CREATE USER IF NOT EXISTS 'webapp'@'10.0.%' IDENTIFIED BY 'CHOOSE_A_NEW_STRONG_PASSWORD';
GRANT SELECT, INSERT ON university.* TO 'webapp'@'10.0.%';
USE university;
CREATE TABLE IF NOT EXISTS students (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL,
  course VARCHAR(255) NOT NULL
);
```

Use a restricted host or specific web private IP instead of `10.0.%` where possible. Set the same new password in the local environment file. Rotate the old password because a `.env` was previously committed.

## Install on Amazon Linux 2023 web EC2

```bash
sudo dnf install -y httpd python3 git
sudo mkdir -p /opt
sudo git clone https://github.com/atulkamble/vpc-peering-project.git /opt/vpc-peering-project
sudo chown -R ec2-user:ec2-user /opt/vpc-peering-project
cd /opt/vpc-peering-project
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
sudo install -d -m 700 -o root -g root /etc/vpc-peering-project
sudo install -m 600 -o root -g root .env.example /etc/vpc-peering-project/app.env
sudo vi /etc/vpc-peering-project/app.env
sudo cp deploy/gunicorn.service /etc/systemd/system/vpc-peering.service
sudo cp deploy/apache.conf /etc/httpd/conf.d/vpc-peering.conf
sudo systemctl daemon-reload
sudo systemctl enable --now vpc-peering
sudo systemctl enable --now httpd
```

**Important:** The service runs as `ec2-user`; the environment file must be readable by that service user. Set ownership and permissions **after editing**:

```bash
sudo chown root:ec2-user /etc/vpc-peering-project /etc/vpc-peering-project/app.env
sudo chmod 750 /etc/vpc-peering-project
sudo chmod 640 /etc/vpc-peering-project/app.env
sudo systemctl restart vpc-peering
```

On SELinux-enforcing hosts, Apache reverse proxy connections may require `sudo setsebool -P httpd_can_network_connect 1` (install policy utilities if missing).

## Verify

```bash
sudo systemctl status vpc-peering httpd
curl -i http://127.0.0.1/health
curl -i http://127.0.0.1/
sudo journalctl -u vpc-peering -n 50 --no-pager
sudo tail -n 50 /var/log/httpd/vpc-peering-error.log
```

Browse `http://WEB_EC2_PUBLIC_IP/` once security groups allow access. For real production, use HTTPS via an ALB or configured Apache TLS certificate, restrict inbound access, manage secrets with AWS Secrets Manager, and use backups, monitoring and multi-AZ design. `/health` checks the web process only, not database availability.

## Update

```bash
cd /opt/vpc-peering-project
git pull --ff-only origin main
.venv/bin/python -m pip install -r requirements.txt
sudo systemctl restart vpc-peering
```

Never run `sudo python app.py` in production. Never commit `.env` or actual credentials. Removing tracked secrets does **not** erase earlier Git history.
