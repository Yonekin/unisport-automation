# Unisport Booking Automation

Automatically books courses on the Uni Mannheim sports portal.

## Setup

```bash
# Install dependencies
pipenv install

# Configure your details
cp .env.example .env
nano .env  # Edit with your data
```

## Configuration

Create a `.env` file:

```env
COURSE_URL=https://www.hochschulsport.uni-mannheim.de/angebote/aktueller_zeitraum_0/_Futsal.html
SEX=X
VORNAME=Max
NAME=Mustermann
STRASSE=Musterstraße 1
ORT=68159 Mannheim
STATUS=S-UNIMA
MATNR=1234567
EMAIL=max@example.com
TELEFON=0123456789
```

## Usage

```bash
# Run manually
pipenv run python book_course.py

# Or use wrapper script
./run_booking.sh
```

## Cron Job Setup

```bash
chmod +x run_booking.sh
crontab -e
```

Add schedule (example for 18:45):
```cron
45 18 17 2 * /path/to/unisport-automation/run_booking.sh
```

## Notes

- Script waits 22 seconds before submission (anti-bot timer)
- Debug HTML files saved for troubleshooting
- Check `booking.log` for cron output

## Requirements

- Python 3.x
- pipenv
