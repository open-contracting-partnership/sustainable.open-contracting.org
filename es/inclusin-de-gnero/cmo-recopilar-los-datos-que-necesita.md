---
permalink: "/inclusin-de-gnero/cmo-recopilar-los-datos-que-necesita"
title: "¿Cómo recopilar los datos que necesita?"
description: "In addition to contract award notices, the main datasets required for this use case are around gender pay and women in senior positions, categories, and information around companies and company ownership."
icon: "/assets/images/Icons_Light_Green3.png"
notion_id: "f4b63b9b2016433891c2dece69faa9c7"
---
In addition to contract award notices, the main datasets required for this use case are around gender pay and women in senior positions, categories, and information around companies and company ownership.

### Gender pay and employment metrics

There are two ways to obtain this data. First is by mandates, as seen in UK public procurement. This is more exhaustive than ad hoc reporting by public procurement and allows a broader analysis.

The second is through public procurement: mandating validated reporting as part of the tendering process and to release these reported metrics with contract notices.

### Category

The main method to obtain category data at present is through that published by the notices. Although many public buyers already do, it is not always complete, accurate and often limited by region (Europe uses CPV, US uses UNSPSC, etc.). Fortunately, modern machine learning has advanced to the point where, with enough data in the title and description, a correct and detailed label can be applied for any classification (CPV, HS, UNSPSC), regardless of language or whether a category has been published.

### Companies

Governments already collect financial data on companies in the form of tax reporting but these are not released. Outside of this, many countries have a central register of companies but not all. Such a register or reports are essential to validate other metrics such as company data recorded in gender pay or supplier data recorded on contract award notices.

Company ownership data is a lot less frequently published, with key exceptions being the UK and Denmark. With this data and gender based flags around ownership, companies can be reconciled to other data sources and gender analysis can be carried out.

If any of the data is not available, then the onus is on public buyers to mandate this information as part of tender submission. 

### Format and standardization

One of the critical issues of self reporting is the lack of standardization. Even mandated reporting across fields generally agreed in the industry (e.g. balance sheets) can carry wildly different interpretations of the data. For instance, is -£387,559 debt a net debt or a net credit? The answer is not always obvious and often counter intuitive.

Therefore, reporting needs to be prescribed as much as possible to prevent deviation and therefore anomalies in analysis, whether with a CSV creator such as Silver Eye or an online form. 

The other critical issue is that data is often published in PDF or other non machine readable format. Where possible, all this data needs to be released in a machine readable way to allow rapid ingestion and analysis.
