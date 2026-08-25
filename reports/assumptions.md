# Assumptions Register

| ID | Assumption | Why required | Evidence | Risk if wrong | Sensitivity |
|---|---|---|---|---|---|
| A1 | Payment recovery uses `SUCCESS` status after duplicate payment ID/reference removal | Raw successful totals can be overstated | Duplicate payment audit | Under/overstated recovery | Compare raw vs validated totals |
| A2 | Business behavioral time is Asia/Kolkata | Calling-hour analysis needs local time | Dataset includes UTC/Kolkata/Dubai timezone warnings | Hour-of-day patterns shift | Retain raw timezone and UTC/local columns |
| A3 | Default attribution window is 7 days | Need channel/campaign association rule | Window sensitivity output generated | Channel ROI overstated | 3/7/14/30-day windows |
| A4 | Full supplied account population is eligible portfolio | No separate eligibility table was supplied | Accounts table is only portfolio source | Denominator may be too broad | Report targeted/attempted funnel separately |
| A5 | Cost and uplift assumptions for INR 10 Cr options are modeled | Actual unit cost/vendor pricing absent | No cost fields in dictionary | ROI can be wrong | Downside and confidence reported |
| A6 | Treatment/control for targeting is observational, not randomized | Counterfactual is requested | No experimental assignment flag | Causal effect overstated | Label as correlation/hypothesis |
