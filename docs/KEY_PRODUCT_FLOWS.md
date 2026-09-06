# Key Product Flows

This is the catalog of **American Lutheran Church (Kellogg, Idaho)** Key Product Flows (KPFs) — the user-facing capabilities the website, API, and Discord Webmaster Bot provide, kept current as the source of truth for what "the product doing its job" means. Each entry details what breaks for the congregation, visitors, or church staff if the flow silently fails, and where it is tested today.

**Maintenance rule (binding for all contributors, human or AI):** any change that adds or alters user-facing behavior must land together with (a) a new or amended KPF entry here — including an updated test-status line — and (b) the tests that entry claims. See [AGENTS.md](../AGENTS.md) for the full requirement. New KPFs are appended (numbers are stable identifiers referenced from code and test docstrings — never renumber existing entries).

See [TESTING_STRATEGY.md](../TESTING_STRATEGY.md) for the testing standard this catalog feeds into.

Test status legend:
- **Backend-tested** — `tests/` exercises the Python API or Bot logic directly.
- **Website-tested** — `tests/` exercises the HTML, CSS, client JS logic, DOM integrity, or links.
- **Smoke-tested** — `scripts/smoke_test.py` validates live/staged HTTP responses and headers.
- **Gap** — no automated coverage yet.

---

## 1. Homepage & Sunday Service Countdown
Visitors to `index.html` (or the domain root `/`) see the hero section, welcome messaging, service times (Sunday 10:00 AM), quick action buttons (Plan a Visit, Prayer Request, Giving, Directions), and a live JavaScript countdown timer to the upcoming Sunday 10:00 AM worship service.
- **Entry points**: `index.html`, `js/main.js` (`initSundayCountdown`, `initHeader`, `initMobileMenu`), `css/styles.css`.
- **If it silently breaks**: Visitors see expired, incorrect, or negative countdown text (e.g. countdown stuck on past Sundays), broken hero styling, unresponsive mobile navigation menu, or missing service times, causing confusion for new visitors trying to attend worship.
- **Test status**: Website-tested — `tests/test_website_integrity.py` (`test_homepage_structure_and_countdown_element`, `test_service_times_consistency`), `tests/test_js_logic.py` (`test_sunday_countdown_math`). Smoke-tested — `scripts/smoke_test.py`.

---

## 2. Plan a Visit Flow
Visitors click "Plan a Visit" buttons across the site (`[data-open-visit]`), opening a native `<dialog id="visit-modal">` modal window (or visit `visit.html`). Visitors input their name, email, target Sunday date, and family/children notes. Upon submission, the form submits via background AJAX (`formsubmit.co/ajax/Cdshorey@gmail.com`) without navigating away or opening an email client, closes the modal, resets the inputs, and displays an affirmative toast notification.
- **Entry points**: `index.html`, `visit.html`, `js/main.js` (`initModals`, `initFormSubmissions`, `sendFormInBackground`, `showToast`).
- **If it silently breaks**: Prospective visitors cannot open the modal, get stuck with unresponsive submit buttons, lose their visit plans, or receive errors without pastor notification, losing new visitor engagement in the church.
- **Test status**: Website-tested — `tests/test_website_integrity.py` (`test_visit_modal_and_form_integrity`, `test_pastor_email_routing`), `tests/test_js_logic.py` (`test_visit_form_payload_structure`).

---

## 3. Prayer Request Submission
Parishioners and visitors click "Request Prayer" (`[data-open-prayer]`), opening `<dialog id="prayer-modal">`. The form captures name (optional/anonymous), contact info, a confidentiality checkbox ("Confidential — Pastor Only" vs "May share with prayer team"), and the prayer request text. Upon submission, data is sent via AJAX to `Cdshorey@gmail.com`, closes the modal, and shows a confirmation toast.
- **Entry points**: `index.html`, `about.html`, `visit.html`, `ministries.html`, `sermons.html`, `give.html`, `js/main.js` (`initModals`, `initFormSubmissions`).
- **If it silently breaks**: Urgent or confidential pastoral prayer requests fail silently to deliver to Pastor Craig, leaving congregation members without prayer support during crises.
- **Test status**: Website-tested — `tests/test_website_integrity.py` (`test_prayer_modal_and_fields_across_all_pages`, `test_prayer_confidentiality_option`), `tests/test_js_logic.py` (`test_prayer_form_payload_structure`).

---

## 4. Contact & General Pastoral Inquiries
Visitors navigate to `visit.html` or footer contact sections, filling out the general contact form (`#contact-page-form`). The form collects name, email, phone number, and message, dispatching via AJAX to `Cdshorey@gmail.com` with in-page toast feedback.
- **Entry points**: `visit.html`, `js/main.js` (`initFormSubmissions`).
- **If it silently breaks**: General community inquiries (baptisms, weddings, funerals, building use) are lost without confirmation or feedback.
- **Test status**: Website-tested — `tests/test_website_integrity.py` (`test_contact_form_fields_and_action`), `tests/test_js_logic.py` (`test_contact_form_payload_structure`).

---

## 5. Church Address Copy & Location Mapping
Users click "Copy Address" buttons (`[data-copy-address]`) in headers, footers, or visit cards to copy `15 E Mullan Ave, Kellogg, ID 83837` to their system clipboard via `navigator.clipboard.writeText`, accompanied by a confirmation toast. Direct Google Maps navigation links open map directions to the church building in a new tab.
- **Entry points**: `js/main.js` (`initCopyAddress`, `showToast`), `index.html`, `visit.html`, `about.html`.
- **If it silently breaks**: Users get clipboard permission errors with no fallback, clipboard contains wrong address or coordinates, or map link points to incorrect location in Kellogg.
- **Test status**: Website-tested — `tests/test_website_integrity.py` (`test_canonical_address_consistency`, `test_maps_link_validity`), `tests/test_js_logic.py` (`test_copy_address_constant`).

---

## 6. Website Support Ticket Widget & API
Website visitors or church staff click "Report Issue / Suggest Edit" in the footer (`[data-modal="support-modal"]`), opening `<dialog id="support-modal">`. The widget auto-detects the current page URL (`window.location.href`), page title (`document.title`), and maps it to the target source file (e.g. `sermons.html`). On submit, it calls `POST /api/support-ticket` (`api/main.py`), which formats a structured Markdown issue and calls the GitHub API (`https://api.github.com/repos/dsackr/american-lutheran-church-kellogg/issues`) using `GITHUB_TOKEN`, returning the created GitHub issue number and link.
- **Entry points**: `api/main.py` (`SupportTicketHandler.do_POST`, `do_GET`, `do_OPTIONS`), `js/main.js` (`initFormSubmissions`), `index.html`, `about.html`, `visit.html`, `ministries.html`, `sermons.html`, `give.html`.
- **If it silently breaks**: Support tickets fail with 400/500 errors, target filenames are misidentified, CORS blocks requests from valid domains, or GitHub issues fail to create, leaving bug reports and update requests unnoticed.
- **Test status**: Backend-tested — `tests/test_api.py` (`test_health_endpoint`, `test_cors_headers`, `test_support_ticket_empty_payload`, `test_support_ticket_missing_description`, `test_support_ticket_filename_deduction`, `test_support_ticket_success_mocked_github`, `test_support_ticket_github_api_error`). Website-tested — `tests/test_website_integrity.py` (`test_support_modal_presence_all_pages`).

---

## 7. Online Giving & Stewardship
Visitors and members navigate to `give.html` to find giving options: Tithe.ly direct online giving links, mail-in offering details (`American Lutheran Church, P.O. Box 247, Kellogg, ID 83837`), in-person offering basket info, memorial fund guidance, and 501(c)(3) tax deduction disclosures.
- **Entry points**: `give.html`, `css/styles.css`.
- **If it silently breaks**: Tithe.ly donation buttons or links are broken or point to incorrect church IDs; giving disclosures or mailing address for checks are incorrect, obstructing congregational donations.
- **Test status**: Website-tested — `tests/test_website_integrity.py` (`test_giving_page_links_and_disclosures`). Smoke-tested — `scripts/smoke_test.py`.

---

## 8. Sermon Archive & Ministry Discovery
Parishioners and prospective members access `sermons.html` to read current and past sermon series notes, listen/watch recorded sermons, and view scripture passages (ESV/NIV). `ministries.html` details Adult Bible Study, Sunday School / Youth programs, Silver Valley food pantry partnership, and community fellowship.
- **Entry points**: `sermons.html`, `ministries.html`, `about.html`.
- **If it silently breaks**: Sermon media links are broken, liturgical series information is outdated, or ministry schedules/contacts are missing or mislinked.
- **Test status**: Website-tested — `tests/test_website_integrity.py` (`test_sermons_and_ministries_page_structure`). Smoke-tested — `scripts/smoke_test.py`.

---

## 9. Discord AI Webmaster Bot Management
Pastor Craig or authorized church administrators send natural language requests to the **ALC Support** Discord Bot (`bot/`):
1. Bot parses the request via Hermes 3 agent (`bot/agent.py`), strictly bounded to `dsackr/american-lutheran-church-kellogg`.
2. Agent reads target files using `bot/tools.py` / `bot/github_client.py`.
3. Agent prepares a unified diff preview and displays an interactive Discord embed with `[🚀 Approve & Push Live]` and `[❌ Cancel]` buttons.
4. If an image is uploaded in Discord, `save_uploaded_asset` optimizes and resizes it (max 1920px width, 85% JPEG) to `assets/images/`.
5. Upon approval, changes are committed as `alckellogg`, automatically triggering CI/CD deployment.
- **Entry points**: `bot/main.py`, `bot/agent.py`, `bot/tools.py`, `bot/github_client.py`, `bot/config.py`.
- **If it silently breaks**: Bot fails to parse file paths, writes outside editable file whitelist (`EDITABLE_EXTENSIONS`), produces corrupt unified diffs, fails image resizing, or allows unauthorized users to commit to repository.
- **Test status**: Backend-tested — `tests/test_bot_tools.py` (`test_list_website_files_filters_correctly`, `test_read_website_file`, `test_apply_file_modification_unified_diff`, `test_save_uploaded_asset_optimization`, `test_deploy_cloud_run_mock`), `tests/test_bot_agent.py` (`test_agent_system_prompt_boundaries`, `test_tools_spec_schema`, `test_agent_proposal_flow_mocked`, `test_github_client_file_operations`).

---

## 10. Automated CI/CD & Cloud Run Deployment
Commits pushed or merged to the `main` branch trigger `.github/workflows/deploy.yml`. The workflow authenticates via GCP Service Account, builds the container via Dockerfile (Nginx + static assets + API), and deploys to Google Cloud Run service `alc-kellogg` in project `openclaw-gateway-489207` (region `us-west1`), serving `https://americanlutheranchurchkellogg.com` with caching, gzip compression, and security headers.
- **Entry points**: `.github/workflows/deploy.yml`, `Dockerfile`, `nginx.conf`, `deploy-gcp.sh`.
- **If it silently breaks**: Builds fail silently on Cloud Run, Nginx misroutes HTML5 pages or API endpoints, MIME types for `.css`/`.js`/`.svg`/`.webmanifest` are corrupted, or security headers are missing.
- **Test status**: Backend-tested — `tests/test_website_integrity.py` (`test_nginx_config_rules_and_security_headers`, `test_dockerfile_presence_and_syntax`). Smoke-tested — `scripts/smoke_test.py`.
