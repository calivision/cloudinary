# Custom Domain for Cloud Run Service using 
## AWS Route 53 for DNS management.
### **Important Core Concepts:**

1.  **No Static IP for Cloud Run:** Cloud Run services (on the managed platform) do **not** have a single, stable static IP address that you can reliably point an `A` record to. The underlying IPs used by Google's infrastructure can change.
2.  **Google Cloud Domain Mappings (Recommended):** The standard and recommended way to use a custom domain with Cloud Run is through Google Cloud's own "Domain Mappings" feature. This feature handles verification, provides the correct DNS records you need to add, and automatically provisions and manages SSL/TLS certificates for your custom domain.
3.  **CNAME vs. A/AAAA Records:**
    *   For **subdomains** (like `app.yourdomain.com`, `www.yourdomain.com`), Google Domain Mappings will typically ask you to create a `CNAME` record pointing to `ghs.googlehosted.com.`.
    *   For **apex/root domains** (like `yourdomain.com`), you usually cannot use a CNAME record directly (due to DNS rules). Google Domain Mappings will instead provide specific `A` and `AAAA` records pointing to Google frontend IP addresses.

## **Steps (Using Google Cloud Domain Mappings + Route 53):**

### **Phase 1: In Google Cloud Console**

1.  **Navigate to Cloud Run:** Go to the Google Cloud Console and select your project (`cloudinary-458008`). Navigate to the Cloud Run section.
2.  **Select Your Service:** Click on your service name (`cloudinary-manager-service`).
3.  **Go to Custom Domains:** Click on the "CUSTOM DOMAINS" tab near the top.
4.  **Add Mapping:** Click the "+ ADD MAPPING" button.
5.  **Select Service:** Ensure `cloudinary-manager-service` is selected.
6.  **Enter Domain:**
    *   **If using a subdomain (Recommended):** Enter the full subdomain you want to use (e.g., `cloudinary.yourdomain.com`, `manager.yourdomain.com`).
    *   **If using an apex/root domain:** Enter the domain without `www` (e.g., `yourdomain.com`). *Note: Using apex domains with Cloud Run sometimes requires specific DNS provider features, but Route 53 supports Alias records which can work.* Google's instructions might vary slightly for apex domains.
7.  **Initiate Verification:** Click "CONTINUE". Google will now likely tell you that you need to verify ownership of the domain. It will provide specific DNS record details (usually a `TXT` record or a `CNAME` record with specific names/values) that you need to add in Route 53. **Keep this screen open or copy the verification record details EXACTLY.**

### **Phase 2: In AWS Route 53 Console**

8.  **Navigate to Route 53:** Log in to your AWS Management Console and go to the Route 53 service.
9.  **Select Hosted Zone:** Click on "Hosted zones" in the left sidebar and select the hosted zone for the domain you own (e.g., `yourdomain.com`).
10. **Create Verification Record:**
    *   Click "Create record".
    *   **Record name:** Enter the name/host exactly as provided by Google Cloud (often `_acme-challenge` or a unique string, sometimes it's blank for apex domain verification).
    *   **Record type:** Select the type specified by Google Cloud (usually `TXT` or `CNAME`).
    *   **Value:** Paste the exact value provided by Google Cloud. Ensure no extra spaces or quotes unless specified. For TXT records, the value might need to be enclosed in double quotes (`"value goes here"`).
    *   **TTL:** You can usually leave the default TTL (Time To Live).
    *   Click "Create records".

### **Phase 3: Wait & Complete Mapping in Google Cloud**

11. **Wait for DNS Propagation:** It can take anywhere from a few minutes to several hours (though usually faster) for the DNS verification record you added in Route 53 to become visible across the internet.
12. **Google Verifies:** Go back to the Google Cloud Run "Custom Domains" / "Add Mapping" screen. Google should automatically re-check for the verification record. Once found, the status should update to indicate verification is complete.
13. **Get Mapping Records:** Google will now display the **final DNS records** needed to point your domain to the Cloud Run service. **Pay close attention to these!**
    *   **For subdomains:** It will typically be a `CNAME` record pointing to `ghs.googlehosted.com.` (don't forget the trailing dot).
    *   **For apex domains:** It will typically be four `A` records and potentially four `AAAA` records pointing to specific Google IP addresses.
14. **Copy these final mapping records precisely.**

### **Phase 4: Add Mapping Records in AWS Route 53**

15. **Return to Route 53:** Go back to your Hosted Zone in the AWS Route 53 console.
16. **Create Mapping Record(s):** Click "Create record".
    *   **If Google provided a CNAME (for subdomains):**
        *   **Record name:** Enter the subdomain part (e.g., `cloudinary`, `manager`).
        *   **Record type:** `CNAME`.
        *   **Value:** Enter `ghs.googlehosted.com.` (including the trailing dot).
        *   **TTL:** Default is usually fine.
        *   Click "Create records".
    *   **If Google provided A/AAAA records (for apex domains):**
        *   **Record name:** Leave this blank (for the apex domain).
        *   **Record type:** `A`.
        *   **Value:** Enter *each* of the four IPv4 addresses provided by Google, one per line in the value box.
        *   **TTL:** Default is fine.
        *   Click "Create records".
        *   **Repeat** the process for **Record type:** `AAAA`, entering the IPv6 addresses provided by Google if any.
        *   **(Alternative for Apex using Alias):** Route 53 allows "Alias" records. You *might* be able to create an `A` Alias record pointing to the Cloud Run service endpoint or associated Google infrastructure, but following Google's explicit A/AAAA record instructions is generally safer.

### **Phase 5: Finalization & Testing**

17. **Wait for DNS Propagation (Again):** Allow time for the mapping records to propagate (minutes to hours).
18. **Google Provisions Certificate:** Google Cloud will detect the mapping records pointing to its infrastructure and automatically provision a managed SSL/TLS certificate for your custom domain. You can monitor the status in the Cloud Run "Custom Domains" tab. It should change from "Provisioning Certificate" to "Active".
19. **(IMPORTANT) Update OAuth Authorized Origins:**
    *   Go back to Google Cloud Console -> APIs & Services -> Credentials -> Your OAuth 2.0 Client ID.
    *   Click **"+ ADD URI"** under "Authorized JavaScript origins".
    *   Add your **new custom domain URL** (e.g., `https://cloudinary.yourdomain.com`).
    *   Click **Save**.
20. **Test:** Open your browser and navigate to your custom domain (e.g., `https://cloudinary.yourdomain.com`). It should now load your Cloud Run application, and the Google Sign-In flow should work from this new domain.

This process ensures secure mapping and automatic SSL certificate handling via Google Cloud's integrated features.