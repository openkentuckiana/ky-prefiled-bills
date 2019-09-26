# KY Prefiled Bill Requests Scraper

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

### Deploying

1. Follow the `Google Drive API and Service Accounts` instructions [here](https://www.twilio.com/blog/2017/02/an-easy-way-to-read-and-write-to-a-google-spreadsheet-in-python.html)
1. Create a [new Google Sheet](http://sheets.net) with the name `Prefiled Bills`
1. Share the sheet with the email address in the `client_email` field of the JSON from step 1, making sure to give it edit access
1. Click the `Deploy to Heroku` button above to deploy this app
1. Put the contents of the JSON from step 1 into the `CLIENT_SECRET` field on the Heroku app creation screen

### Running manually

1. Go to the [Heroku Dashboard](https://dashboard.heroku.com/apps/) and find your app
1. Choose `Run console` from the `More` menu
1. Enter `python app.py` in the input field, and click `Run`
1. Check your `Prefiled Bills` spreadsheet to see if it was populated

### Scheduling runs

1. Go to the [Heroku Dashboard](https://dashboard.heroku.com/apps/) and find your app
2. Click the `Heroku Scheduler` link from the `Overview` tab
3. Click `Create Job`
4. Choose an interval (every hour or every day)
5. Enter `python app.py` in the `$` input field
6. Click `Save Job`
