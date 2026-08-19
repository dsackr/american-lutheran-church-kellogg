FROM nginx:alpine

# Remove default nginx config and html
RUN rm -rf /etc/nginx/conf.d/* /usr/share/nginx/html/*

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy static website assets
COPY . /usr/share/nginx/html/

# Expose port 8080 (standard for Cloud Run)
EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
