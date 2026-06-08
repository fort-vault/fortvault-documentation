# FortVault Weekly Release Notes

**Release Notes**  
**Week ending:** June 8, 2026

## Updates

### History

- Improved History date filtering so selected date ranges are handled consistently by the backend API.
- Fixed date range boundary handling to avoid timezone-related one-day shifts.
- History now remembers the selected date range while navigating between pages, until browser refresh.
- History transaction and action filters now remember selected values while navigating, until browser refresh.

### Reports

- Added Network Fee USD to exported CSV and PDF reports for deposits and withdrawals.
- Standardized exported Network Fee USD formatting to two decimal places, for example `$0.27` and `$0.00`.
- Improved report deposit and withdrawal summaries so internal movements are included consistently.
- Reports now remember selected date ranges while navigating between pages, until browser refresh.
- Report detail filters now remember selected values while navigating, until browser refresh.
- Added test coverage for report summary internal transfer handling.

### Dynamic Filters

- Added shared in-memory filter state for dynamic filters.
- Applied remembered dynamic filters to Customers, Vaults, Whitelisted Addresses, History, and Reports.
- Improved asset filter dropdown positioning when a selected asset includes an icon.

### Transfers

- Added quick amount buttons in the transfer dialog: 25%, 50%, 75%, and 100%.
- Improved transfer amount calculation so percentage buttons preserve decimal precision.

