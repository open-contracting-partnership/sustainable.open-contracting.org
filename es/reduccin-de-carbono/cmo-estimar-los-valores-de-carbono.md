---
permalink: /reduccin-de-carbono/cmo-estimar-los-valores-de-carbono
title: "¿Cómo estimar los valores de carbono?"
description: "The most basic way to estimate the carbon value of a contract is to multiply the contract value by a coefficient. One example coefficient is the carbon values derived from categories of goods and services. Spend Network has a table that calculates carbon tonnage based on CPV and UNSPSC. This presents a high level picture of what carbon value is associated with: for instance, a taxi contract. "
icon: /assets/images/Icons_Light_Green3.png
notion_id: "648c62289e8c43deba1c30c98f81f4b6"
---
The most basic way to estimate the carbon value of a contract is to multiply the contract value by a coefficient. One example coefficient is the carbon values derived from categories of goods and services. Spend Network has a table that calculates carbon tonnage based on CPV and UNSPSC. This presents a high level picture of what carbon value is associated with: for instance, a taxi contract. 

```sql
Carbon value = Contract value multiplied by Carbon coefficient

Facilities management's estimated carbon emissions/$ = 610.69 tonnes CO2/$ million

A $5 million dollar FM contract would therefore yield 3053.44 tonnes of CO2
```

In isolation, this data cannot be analysed: raw contract values gives an incomplete valuation. For instance, a notice for 5 million might be 5 million over 1 year or 5 million over 10. Tracking raw contract values creates uneven and highly skewed data (for instance, a large infrastructure contract awarded one year will skew the entire dataset).

Therefore, in order to better estimate the carbon value of a contract, it is necessary to calculate the contract value by using the award notice value and the contract start and end date.

```sql
Contract value = value divided by (end date minus start date) 

Carbon value = Contract value multiplied by Carbon coefficient

A $5 million dollar FM contract spread over 10 years would yield 305.34 tonnes/year
```
