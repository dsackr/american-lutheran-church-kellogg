# Domain & DNS Setup Guide

This guide explains how to configure **`americanlutheranchurchkellogg.com`** and **`alckellogg.com`** for Google Cloud Platform (GCP) serverless hosting, including automatic HTTP 301 redirection.

---

## 1. Domain Registration Strategy

* **Primary Domain**: `americanlutheranchurchkellogg.com` (and `www.americanlutheranchurchkellogg.com`)
* **Short/Vanity Domain**: `alckellogg.com` (and `www.alckellogg.com`)
* **Redirect Behavior**: All traffic hitting `alckellogg.com` and `www.alckellogg.com` automatically issues a permanent `HTTP 301 Redirect` to `https://americanlutheranchurchkellogg.com`.

---

## 2. Option A: Firebase Hosting on GCP (Recommended & Easiest)

Firebase Hosting (built on Google Cloud infrastructure) provides automatic SSL certificate provisioning, CDN edge caching, and built-in domain redirect configuration.

### Steps:
1. Go to the [Firebase Console](https://console.firebase.google.com/) and select or link your GCP Project (`openclaw-gateway-489207` or a new project).
2. Under **Build > Hosting**, click **Add custom domain**.
3. Add `americanlutheranchurchkellogg.com`.
   - Firebase will provide you with **A records** (e.g. `199.36.158.100`). Add these at your domain registrar.
4. Click **Add custom domain** again and enter `alckellogg.com`.
   - Check the box: **"Redirect to an existing domain"** and select `americanlutheranchurchkellogg.com`.
5. Firebase will automatically verify the domains, provision free SSL/TLS certificates via Let's Encrypt / Google Trust Services, and handle the 301 redirect.

---

## 3. Option B: Google Cloud Run Custom Domain Mapping

If hosting on Google Cloud Run:

1. Map the primary domain:
   ```bash
   gcloud beta run domain-mappings create \
     --service alc-kellogg \
     --domain americanlutheranchurchkellogg.com \
     --region us-west1
   ```
2. Map the `www` subdomain:
   ```bash
   gcloud beta run domain-mappings create \
     --service alc-kellogg \
     --domain www.americanlutheranchurchkellogg.com \
     --region us-west1
   ```
3. Set up DNS records at your registrar with the values output by `gcloud`.
4. For `alckellogg.com`, configure URL Forwarding (301 Permanent Redirect) at your registrar (GoDaddy, Namecheap, Google Domains / Squarespace, Cloudflare) pointing to `https://americanlutheranchurchkellogg.com`.

---

## 4. Option C: Cloudflare DNS (Free Proxy & Redirect Rule)

If you use Cloudflare for DNS management:
1. Create DNS `A` or `CNAME` records pointing `americanlutheranchurchkellogg.com` to your GCP service.
2. In Cloudflare for `alckellogg.com`, go to **Rules > Redirect Rules** -> Create rule:
   - **When**: All incoming requests
   - **Then**: Dynamic Redirect to `https://americanlutheranchurchkellogg.com` (Status Code: `301 Moved Permanently`).

---

## 5. Summary of Church Contact & Metadata
* **Address**: 15 E Mullan Ave, Kellogg, ID 83837
* **Phone**: (208) 786-7791
* **Pastor**: Jason Bonnicksen
* **Worship Times**: Sundays at 10:00 AM
* **Facebook**: https://www.facebook.com/share/19XvBsfiGR/?mibextid=wwXIfr
* **YouTube**: https://www.youtube.com/@americanlutheranchurchkellogg
