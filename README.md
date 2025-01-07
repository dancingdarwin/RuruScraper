# Lulu Lemon Scraper
Identifies and notifies you whenever an item is in stock. Takes a Google Sheet (example [here](https://docs.google.com/spreadsheets/d/1_zNL_jJ7xQnfkGwQMX70QDBhikJ4Op7Dj8F7rDlvcfQ)) for list of items. 

##  Config Files (Not Included) 
`Emails.yaml` - Defines emails/personal information for interacting with Google Sheets/GMail
```
recipient: <INSERT EMAIL HERE > # Whoever will receive the email
sender: <SENDER EMAIL> # The email sender 
spreadsheet_id: # The Google Sheet ID described at https://developers.google.com/sheets/api/guides/concepts
```

`Credentials.json` - You need to set up your own Google API access credentials, which is described [here](https://developers.google.com/identity/protocols/oauth2)
