# Gather event website

A lightweight Django app for browsing upcoming events, creating an account, hosting events, and registering as an attendee. Event data is saved in a local SQLite database.

## Start on Windows

Open a terminal in this folder (`Z:\DJANGO\DJ`) and run:

```powershell
py -m pip install -r requirements.txt
py manage.py migrate
py manage.py runserver
```

When Django starts successfully, the terminal displays:

```text
Starting development server at http://127.0.0.1:8000/
```

Open that address in your browser. You can also use `http://localhost:8000/`. Keep the terminal open while using the site; press `Ctrl+C` there to stop the server.

If `py` is not available, replace it with `python` in the commands above. If the server reports that port 8000 is already in use, run `py manage.py runserver 8001` and open `http://127.0.0.1:8001/`.

## Features

- Event discovery with text and category search
- Sign-up, login, and logout
- Authenticated event creation
- Staff registration review with accept/reject controls
- Attendee name, phone, organization and optional relevant attendee note
- Event announcements and attendance check-in
- Online attendance sheet and downloadable PDF attendance report
- WhatsApp invite links visible only to accepted attendees
- Attendee registration with capacity checks
- A personal dashboard for hosted and joined events
- Django admin at `/admin/`

## Set up the administrator

After running migrations, create the first administrator account:

```powershell
py manage.py createsuperuser
```

Use those credentials at `/staff/login/`. Staff are sent to `/staff/` to review registrations and open each event workspace. The workspace manages the attendee list, check-in, announcements, WhatsApp invite URL, and PDF attendance export. `/admin/` remains available for direct database administration. Accepted attendees see the invite link and event announcements; the site does not add users to WhatsApp automatically.

Attendee contact details and notes are personal data. Collect only information necessary for the event, restrict access to trusted staff, and do not use free-text attendee notes to collect government identity numbers.

For local development only. Configure a private secret key, `DEBUG=False`, and production `ALLOWED_HOSTS` before deployment.