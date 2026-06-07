#!/bin/sh
set -e

echo "Starting nginx..."

cat > /etc/nginx/nginx.conf << 'EOF'
worker_processes auto;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;

    keepalive_timeout 65;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    limit_req_zone $binary_remote_addr zone=general_limit:10m rate=120r/m;

    server {
        listen 80;

        root /usr/share/nginx/html;
        index index.html;

        add_header X-Frame-Options "DENY" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
        add_header Content-Security-Policy "default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; form-action 'self'; img-src 'self' data: https://images.unsplash.com; font-src 'self' https://fonts.gstatic.com data:; style-src 'self' https://fonts.googleapis.com 'sha256-fO/9dcPp2YR4M42g9eXUAJUtoLh6g11o+hXWpz5hZPY='; style-src-attr 'unsafe-inline'; script-src 'self' 'sha256-uf+7mNA88XVfCdNJa7MlSLolHXL1jFfDlnxE25IAEuE=' 'sha256-GludQzLp2cagXwICMH/bRlmXJvC1iq2D1VUoJv2HmKg='; connect-src 'self' https://agriai-ecxt.onrender.com; upgrade-insecure-requests;" always;

        client_max_body_size 10M;

        location / {
            limit_req zone=general_limit burst=60 nodelay;
            try_files $uri $uri/ /index.html;
        }

        location /health {
            access_log off;
            return 200 "ok";
        }
    }
}
EOF

nginx -t

exec nginx -g 'daemon off;'