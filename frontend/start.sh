#!/bin/sh
set -e

echo "Starting nginx on port 80 - static files only"

cat > /etc/nginx/conf.d/default.conf << 'EOF'
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    # Basic bot/spam protection
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=60r/m;
    limit_req_zone $binary_remote_addr zone=general_limit:10m rate=120r/m;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    # SPA routing - all routes serve index.html
    location / {
        limit_req zone=general_limit burst=60 nodelay;
        try_files $uri $uri/ /index.html;
    }

    # Content Security Policy (production-safe defaults)
    add_header Content-Security-Policy "default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; form-action 'self'; img-src 'self' data: https://images.unsplash.com; font-src 'self' https://fonts.gstatic.com data:; style-src 'self' https://fonts.googleapis.com 'sha256-fO/9dcPp2YR4M42g9eXUAJUtoLh6g11o+hXWpz5hZPY='; style-src-attr 'unsafe-inline'; script-src 'self' 'sha256-uf+7mNA88XVfCdNJa7MlSLolHXL1jFfDlnxE25IAEuE=' 'sha256-GludQzLp2cagXwICMH/bRlmXJvC1iq2D1VUoJv2HmKg='; connect-src 'self' https://agriai-ecxt.onrender.com;" always;

    # Health check
    location /health {
        return 200 "ok";
    }
}
EOF

echo "Nginx config:"
cat /etc/nginx/conf.d/default.conf
exec nginx -g 'daemon off;'
